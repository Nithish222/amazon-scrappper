# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class AmazonItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class ProductItem(scrapy.Item):
    asin = scrapy.Field()
    name = scrapy.Field()
    url = scrapy.Field()
    is_available = scrapy.Field()
    brand = scrapy.Field()
    brand_url = scrapy.Field()
    seller = scrapy.Field()
    seller_url = scrapy.Field()
    rating = scrapy.Field()
    review_count = scrapy.Field()
    past_count = scrapy.Field()
    discount = scrapy.Field()
    price = scrapy.Field()
    mrp = scrapy.Field()
    offers = scrapy.Field()
    features = scrapy.Field()
    overview = scrapy.Field()
    together = scrapy.Field()
    frequently_bought = scrapy.Field()
    summary = scrapy.Field()
    mentions = scrapy.Field()
    scraped_at = scrapy.Field()