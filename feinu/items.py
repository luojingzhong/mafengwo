# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class SeasonItem(scrapy.Item):
    addr = scrapy.Field()
    introduction = scrapy.Field()
    image_urls = scrapy.Field()
    img_urls = scrapy.Field()
    tag = scrapy.Field()
    url = scrapy.Field()

class AddressItem(scrapy.Item):
    addr = scrapy.Field()
    introduction = scrapy.Field()
    image_urls = scrapy.Field()
    img_urls = scrapy.Field()
    url = scrapy.Field()

class ScenicItem(scrapy.Item):
    belong_to = scrapy.Field()
    name = scrapy.Field()
    url = scrapy.Field()
    introduction = scrapy.Field()
    traffic = scrapy.Field()
    ticket = scrapy.Field()
    open_time = scrapy.Field()
    image_urls = scrapy.Field()
    img_urls = scrapy.Field()
    location = scrapy.Field()
    lng = scrapy.Field() # 经度
    lat = scrapy.Field() # 纬度

class FavorableItem(scrapy.Item):
    belong_to = scrapy.Field()
    datas = scrapy.Field()

class FoodsItem(scrapy.Item):
    belong_to = scrapy.Field()
    image_urls = scrapy.Field()
    img_urls = scrapy.Field()
    url = scrapy.Field()
    name = scrapy.Field()
    location = scrapy.Field()
    telphone = scrapy.Field()
    score = scrapy.Field()
    lng = scrapy.Field()
    lat = scrapy.Field()

class TravelItem(scrapy.Item):
    belong_to = scrapy.Field()
    title = scrapy.Field()
    image_urls = scrapy.Field()
    img_urls = scrapy.Field()
    release_time = scrapy.Field()
    author = scrapy.Field()
    content = scrapy.Field()
    url = scrapy.Field()

class HotelItem(scrapy.Item):
    belong_to = scrapy.Field()
    title = scrapy.Field()
    location = scrapy.Field()
    score = scrapy.Field()
    image_urls = scrapy.Field()
    img_urls = scrapy.Field()
    url = scrapy.Field()
