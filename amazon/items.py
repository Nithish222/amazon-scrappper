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
    name = scrapy.Field()
    seller = scrapy.Field()
    seller_url = scrapy.Field()
    rating = scrapy.Field()
    review_count = scrapy.Field()
    past_count = scrapy.Field()
    # deal = scrapy.Field()
    discounts = scrapy.Field()
    price = scrapy.Field()
    mrp = scrapy.Field()
    offers = scrapy.Field()
    feature = scrapy.Field()
    # variants = scrapy.Field()
    overview = scrapy.Field()
    # keep = scrapy.Field()
    together = scrapy.Field()
    # similar = scrapy.Field()
    # also_bought = scrapy.Field()
    summary = scrapy.Field()
    aspects = scrapy.Field()