import json
from math import e

from google.cloud import bigquery
from google.oauth2 import service_account
import logging
import os
from dotenv import load_dotenv
from config import BQ_PRODUCT_TABLE
from .items import *
from datetime import datetime, timezone

load_dotenv()
class AmazonPipeline:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mode = None
        self.project_id = os.getenv('BQ_PROJECT_ID')
        self.dataset_id = os.getenv('BQ_DATASET_ID')
        self.product_table = BQ_PRODUCT_TABLE
        self.client = None
        self.table_refs = {}
        self.seen_asins = {}
        try:
            with open('output.json', 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue  # skip blank lines
                    try:
                        obj = json.loads(line)
                        asin = obj.get('asin')
                        scraped_at_str = obj.get('scraped_at')
                        if asin and scraped_at_str:
                            try:
                                scraped_at = datetime.fromisoformat(scraped_at_str)
                                if asin not in self.seen_asins or scraped_at > self.seen_asins[asin]:
                                    self.seen_asins[asin] = scraped_at
                            except Exception:
                                pass
                    except Exception:
                        continue  # skip invalid lines
        except FileNotFoundError:
            pass

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        json_key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not json_key_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set")
        
        credentials = service_account.Credentials.from_service_account_file(json_key_path)
        pipeline.client = bigquery.Client(credentials=credentials, project=pipeline.project_id)
        pipeline.table_refs = {
            'product_data': f"{pipeline.client.project}.{pipeline.dataset_id}.{pipeline.product_table}"
        }

        return pipeline

    def process_item(self, item, spider):
        # asin = item.get('asin')
        # # Set scraped_at before checking
        # item['scraped_at'] = item.get('scraped_at') or datetime.now(timezone.utc).isoformat()
        # scraped_at_str = item['scraped_at']
        # if not asin or not scraped_at_str:
        #     self.logger.warning(f"Skipping item due to missing asin or scraped_at: {item}")
        #     return item
        # try:
        #     scraped_at = datetime.fromisoformat(scraped_at_str)
        # except Exception:
        #     scraped_at = datetime.now(timezone.utc)
        # last_scraped = self.seen_asins.get(asin)
        # if last_scraped:
        #     if scraped_at.date() == last_scraped.date():
        #         self.logger.info(f"Duplicate product skipped (same day): {asin}")
        #         return None
        #     else:
        #         self.logger.info(f"Product re-scraped on a new day: {asin}")
        # self.seen_asins[asin] = scraped_at

        try:
            item['rating'] = self.clean_rating(item.get('rating'))
            item['price'] = self.clean_price(item.get('price'))
            item['mrp'] = self.clean_price(item.get('mrp'))
            item['review_count'] = self.clean_review(item.get('review_count'))
            item['brand_url'] = self.clean_url(item.get('brand_url'))
            item['seller_url'] = self.clean_url(item.get('seller_url'))
            item['is_available'] = self.clean_available(item.get('is_available'))
            # item['scraped_at'] = datetime.now(timezone.utc).isoformat()  # Already set above
        except Exception as e:
            self.logger.info(f"Error cleaning the data: {e}")

        try:
            if isinstance(item, ProductItem):
                self.logger.info(f"Inserting Product data into: {self.table_refs['product_data']}")
                self.insert_amazon_product_data(item)
            else:
                self.logger.info(f"Unhandled item type: {type(item)}")
        except Exception as e:
            self.logger.info(f"Error processing item: {e}")
        return item

    def clean_rating(self, rating):
        if rating is None:
            return 0.0
        if isinstance(rating, (int, float)):
            return float(rating)
        cleaned = str(rating).split(' ')[0]
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def clean_price(self, price):
        if price is None or price == "":
            return 0.0
        if isinstance(price, (int, float)):
            return float(price)
        cleaned = str(price).split(':')[-1]
        cleaned = cleaned.replace('₹', '').replace(',', '').strip()
        cleaned = cleaned.replace('\n', '')
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def clean_review(self, review):
        if review is None or review == "":
            return 0
        if isinstance(review, int):
            return review
        cleaned = ''.join(str(review).split(',')).split(' ')[0]
        try:
            return int(cleaned)
        except ValueError:
            return 0

    def clean_url(self, url):
        if url is not None and url != "":
            return "https://amazon.in" + url
        return ""

    def clean_available(self, available):
        if not available:
            return "yes"
        else:
            return "no"
    
    def insert_amazon_product_data(self, item):
        if self.client is None:
            raise RuntimeError("BigQuery client is not initialized")

        # # Streaming inserts (Requires a billing account in BigQuery)
        # try:
        #     row = {
        #         'asin': item.get('asin'),
        #         'product_name': item.get('name'),
        #         'product_url': item.get('url'),
        #         'is_available': item.get('is_available'),
        #         'brand': item.get('brand'),
        #         'brand_url': item.get('brand_url'),
        #         'seller': item.get('seller'),
        #         'seller_url': item.get('seller_url'),
        #         'rating': item.get('rating'),
        #         'review_count': item.get('review_count'),
        #         'past_count': item.get('past_count'),
        #         'discount': item.get('discount'),
        #         'price': item.get('price'),
        #         'mrp': item.get('mrp'),
        #         'offers': item.get('offers'),
        #         'features': item.get('features'),
        #         'overview': item.get('overview'),
        #         'together': [
        #             {
        #                 'product_name': product.get('name'),
        #                 'product_price': self.clean_price(product.get('price'))
        #             }
        #             for product in item.get('together', [])
        #         ],
        #         'summary': item.get('summary'),
        #         'mentions': item.get('mentions'),
        #         'scraped_at': item.get('scraped_at')
        #     }
        #     errors = self.client.insert_rows_json(
        #         self.table_refs['product_data'],
        #         [row],
        #         retry=bigquery.DEFAULT_RETRY.with_deadline(30)
        #     )
        #     if errors:
        #         raise Exception(f"BigQuery insertion error: {errors}")
        #     else:
        #         self.logger.info(f"Successfully inserted products data of {item.get('name')}")
        # except Exception as e:
        #     self.logger.info(f"Error inserting product data: {e}")
        #     raise

        # Batch insert refer README.md for the steps in detail
        row = {
            'asin': item.get('asin'),
            'product_name': item.get('name'),
            'product_url': item.get('url'),
            'is_available': item.get('is_available'),
            'brand': item.get('brand'),
            'brand_url': item.get('brand_url'),
            'seller': item.get('seller'),
            'seller_url': item.get('seller_url'),
            'rating': item.get('rating'),
            'review_count': item.get('review_count'),
            'past_count': item.get('past_count'),
            'discount': item.get('discount'),
            'price': item.get('price'),
            'mrp': item.get('mrp'),
            'offers': item.get('offers'),
            'features': item.get('features'),
            'overview': item.get('overview'),
            # 'together': [
            #     {
            #         'product_name': product.get('name'),
            #         'product_price': self.clean_price(product.get('price'))
            #     }
            #     for product in item.get('together', [])
            # ],
            'together': item.get('together'),
            'summary': item.get('summary'),
            'mentions': item.get('mentions'),
            'scraped_at': item.get('scraped_at')
        }
        
        # Debug logging
        self.logger.info(f"About to write to output.json: {row}")
        try:
            with open('output.json', 'a') as f:
                f.write(json.dumps(row) + '\n')
            self.logger.info(f"Successfully wrote to output.json")
        except Exception as e:
            self.logger.error(f"Error writing to output.json: {e}")
            raise