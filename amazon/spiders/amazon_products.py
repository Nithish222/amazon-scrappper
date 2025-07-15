from turtle import pd
import scrapy
from amazon.items import *
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time

class AmazonProductsSpider(scrapy.Spider):
    name = "amazon_products"
    allowed_domains = ["amazon.in"]

    def __init__(self, link=None, product=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if link:
            self.mode = "link"
            self.start_url = link
            self.logger.info(f"Spider will crawl link: {self.start_url}")
        elif product:
            self.mode = "product"
            self.start_url = f"https://www.amazon.in/s?k={product}"
            self.logger.info(f"Spider will crawl search for product: {product}")
        else:
            raise ValueError("You must provide either -a link=<url> or -a product=<product_name>")

    def start_requests(self):
        if self.mode == "link":
            yield scrapy.Request(self.start_url, callback=self.parse_link_mode)
        elif self.mode == "product":
            yield scrapy.Request(self.start_url, callback=self.parse_product_mode)

    def parse_link_mode(self, response):
        try:
            pdt_item = ProductItem()

            basic = response.css("div#centerCol")
            pdt_item['asin'] = response.url.split('dp/')[1].split('/')[0]
            pdt_item['name'] = basic.css("span#productTitle::text").get().strip()
            pdt_item['url'] = response.url
            pdt_item['is_available'] = response.css("div#availability_feature_div div#availability")
            pdt_item['brand'] = basic.css("a#bylineInfo::text").get().strip()
            pdt_item['brand_url'] = basic.css("a#bylineInfo::attr(href)").get()
            pdt_item['rating'] = basic.css("span#acrPopover::attr(title)").get()
            pdt_item['review_count'] = basic.css("span#acrCustomerReviewText::text").get()
            pdt_item['seller'] = response.css("a#sellerProfileTriggerId::text").get().strip()
            pdt_item['seller_url'] = response.css("a#sellerProfileTriggerId::attr(href)").get()

            dynamic_data = self.get_dynamic_content(response.url)
            pdt_item['past_count'] = dynamic_data.get('bought')
            pdt_item['discount'] = dynamic_data.get('discount')
            pdt_item['price'] = dynamic_data.get('price')
            pdt_item['mrp'] = dynamic_data.get('mrp')
            pdt_item['offers'] = dynamic_data['offers']
            pdt_item['features'] = dynamic_data.get('features')
            pdt_item['overview'] = dynamic_data.get('overview')
            pdt_item['together'] = dynamic_data.get('frequently_bought')
            pdt_item['summary'] = dynamic_data.get('summary')
            pdt_item['mentions'] = dynamic_data.get('mentions')

        except Exception as e:
            print(e)
        
        yield pdt_item

    @staticmethod
    def get_dynamic_content(url):
        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)

        driver.get(url)
        time.sleep(1)
        data = {}

        try:
            main = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "centerCol"))
            )
            try:
                data['bought'] = main.find_element(By.ID, "social-proofing-faceout-title-tk_bought").text.strip()
            except Exception as e:
                print(f"Could not find bought data: {e}")
                data['bought'] = ""

            try:
                pricing = main.find_element(By.ID, "corePriceDisplay_desktop_feature_div")
                data['discount'] = pricing.find_element(By.CSS_SELECTOR, "span.savingPriceOverride").text.strip()
                data['price'] = pricing.find_element(By.CSS_SELECTOR, "span.a-price-symbol").text.strip() + pricing.find_element(By.CSS_SELECTOR, "span.a-price-whole").text.strip()
                data['mrp'] = pricing.find_element(By.CSS_SELECTOR, "span.aok-relative").text.strip()
            except Exception as e:
                print(f"Could not find pricing data: {e}")
                data['discount'] = ""
                data['price'] = ""
                data['mrp'] = ""

            try:
                offers_list = []
                offers_tag = driver.find_element(By.CSS_SELECTOR, "div.a-cardui.vsx__offers-holder")
                
                # Loop to click through all offers
                while True:
                    try:
                        offers = offers_tag.find_elements(By.TAG_NAME, "li")
                        
                        for offer in offers:
                            try:
                                header = offer.find_element(By.CSS_SELECTOR, "h6.a-size-base.a-spacing-micro.offers-items-title").text
                                if header and header.strip():
                                    if header not in offers_list:
                                        offers_list.append(header)
                            except Exception as e:
                                print(f"Could not extract header from offer: {e}")
                                continue
                        
                        try:
                            next_button = offers_tag.find_element(By.CSS_SELECTOR, "div.a-carousel-col.a-carousel-right a")
                            if next_button.is_enabled() and next_button.is_displayed():
                                next_button.click()
                                time.sleep(2)
                                
                                offers_tag = driver.find_element(By.CSS_SELECTOR, "div.a-cardui.vsx__offers-holder")
                                offers = offers_tag.find_elements(By.TAG_NAME, "li")
                                
                                for offer in offers:
                                    try:
                                        header = offer.find_element(By.CSS_SELECTOR, "h6.a-size-base.a-spacing-micro.offers-items-title").text
                                        if header and header.strip():
                                            if header not in offers_list:
                                                offers_list.append(header)
                                    except Exception as e:
                                        print(f"Could not extract header from new offer: {e}")
                                        continue
                            else:
                                break
                        except Exception as e:
                            print(f"No more next button found: {e}")
                            break
                            
                    except Exception as e:
                        print(f"Error in offers loop: {e}")
                        break
                
                data['offers'] = offers_list
                
            except Exception as e:
                print(f"Could not find offers data: {e}")
                data['offers'] = []

            try:
                feature_list = []
                features_tag = driver.find_element(By.CSS_SELECTOR, "div#iconfarmv2_feature_div")
                
                # Loop to click through all features
                while True:
                    try:
                        features = features_tag.find_elements(By.CSS_SELECTOR, "li.a-carousel-card:not([aria-hidden='true'])")
                        
                        for feature in features:
                            try:
                                feature_name = feature.find_element(By.CSS_SELECTOR, "a.a-size-small.a-link-normal.a-text-normal").text
                                if feature_name and feature_name.strip():
                                    if feature_name not in feature_list:
                                        feature_list.append(feature_name)
                            except Exception as e:
                                print(f"Could not extract feature name: {e}")
                                continue
                        
                        try:
                            next_button = features_tag.find_element(By.CSS_SELECTOR, "div.a-carousel-col.a-carousel-right a")
                            if next_button.is_enabled() and next_button.is_displayed():
                                next_button.click()
                                time.sleep(2)
                                
                                features_tag = driver.find_element(By.CSS_SELECTOR, "div#iconfarmv2_feature_div")
                                features = features_tag.find_elements(By.CSS_SELECTOR, "li.a-carousel-card:not([aria-hidden='true'])")
                                
                                for feature in features:
                                    try:
                                        feature_name = feature.find_element(By.CSS_SELECTOR, "a.a-size-small.a-link-normal.a-text-normal").text
                                        if feature_name and feature_name.strip():
                                            if feature_name not in feature_list:
                                                feature_list.append(feature_name)
                                    except Exception as e:
                                        print(f"Could not extract feature name: {e}")
                                        continue
                            else:
                                break
                        except Exception as e:
                            print(f"No more next button found for features: {e}")
                            break
                            
                    except Exception as e:
                        print(f"Error in features loop: {e}")
                        break
                
                data['features'] = feature_list
                
            except Exception as e:
                print(f"Could not find features data: {e}")
                data['features'] = []

            try:
                overview = driver.find_element(By.CSS_SELECTOR, "div#productOverview_feature_div tbody").text.strip()
                data['overview'] = overview
            except Exception as e:
                print(f"Could not find overview: {e}")
                data['overview'] = ""

            try:
                frequently_list = []
                freq = driver.find_element(By.CSS_SELECTOR, "div[data-csa-c-content-id='sims-productBundle']")
                product_titles = freq.find_elements(By.CSS_SELECTOR, "span[class='a-size-base']")
                product_prices = freq.find_elements(By.CSS_SELECTOR, "span[class='a-price']")
                for titles, prices in zip(product_titles, product_prices):
                    title = titles.text.strip()
                    price = prices.text.strip().replace('\n', '.')
                    if title and price:
                        frequently_list.append({'name': title, 'price': price})
                data['frequently_bought'] = frequently_list
            except Exception as e:
                print(f"Could not find frequently bought products: {e}")
                data['frequently_bought'] = []

            # try:
            #     also_bought_list = []
            #     also_bought = WebDriverWait(driver, 10).until(
            #         EC.presence_of_element_located((By.CSS_SELECTOR, "div#DetailPage_sims-container_desktop-dp-sims_2_container"))
            #     )
            #     products = also_bought.find_elements(By.CSS_SELECTOR, "li.a-carousel-card")
            #     for product in products:
            #         product_name = product.find_element(By.CSS_SELECTOR, "a.a-link-normal.aok-block").text
            #         print(f"Name: {product_name}")
            #         product_link = product.find_element(By.CSS_SELECTOR, "a.a-link-normal.aok-block").get_attribute("href")
            #         print(f"Link: {product_link}")
            #         product_price = product.find_element(By.CSS_SELECTOR, "span.a-price span.a-offscreen").text.strip()
            #         product_mrp = product.find_element(By.CSS_SELECTOR, "span.aok-nowrap.a-text-strike").text.strip()
            #         also_bought_list.append({
            #             "name": product_name,
            #             "link": product_link,
            #             "price": product_price,
            #             "mrp": product_mrp
            #         })
            #     data['also_bought'] = also_bought_list
            #     print(f"List: {also_bought_list}")
            # except Exception as e:
            #     print(f"can not find frequently bought together: {e}")
            try:
                summary = driver.find_element(By.CSS_SELECTOR, "div#product-summary p.a-spacing-small").text.strip()
                data['summary'] = summary
            except Exception as e:
                print(f"Can not find product summary: {e}")
                data['summary'] = ""

            try:
                mentions_list = []
                mentions = driver.find_elements(By.CSS_SELECTOR, "div[aria-label='Commonly Mentioned Aspects'] a")
                for mention in mentions:
                    mention_text = mention.text.strip()
                    mentions_list.append(mention_text)
                data['mentions'] = mentions_list
            except Exception as e:
                print(f"Can not find commonly mentioned aspects: {e}")
                data['mentions'] = []

        finally:
            driver.quit()
        
        return data

    def parse_product_mode(self, response):
        pass