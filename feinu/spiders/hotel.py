# -*- coding: utf-8 -*-
from scrapy.selector import Selector
from feinu.items import HotelItem
from feinu.mongodb import get_connection
from feinu.tools import get_proxy
from feinu import settings
import requests
import scrapy
import json
import time
import redis
import re

class HotelSpider(scrapy.Spider):
    name = 'hotel'
    allowed_domains = ['mafengwo.cn']
    url = 'http://www.mafengwo.cn/search/s.php?q={0}&p={1}&t=hotel&kt=1'

    def __init__(self,**kwargs):
        conn = get_connection()
        address = conn[settings.DATABASE].address
        self.addresses = list(address.find({}))
        conn.close()

    def start_requests(self):
        while self.addresses:
            addr = self.addresses.pop(0)
            yield scrapy.Request(url=self.url.format(addr['addr'],1),callback=self.parse,meta={'page':1,'addr':addr['addr']})

    def parse(self, response):
        hotels = response.css('._j_search_section .hot-list .hot-about')
        for div in hotels:
            item = HotelItem()
            item['url'] = div.css('.ct-text h3 a::attr(href)').extract_first()
            item['belong_to'] = response.meta['addr']
            item['title'] = re.sub(r'(<.*?>)|\n','',div.css('.ct-text h3 a').extract_first()).replace('\xa0',' ')
            item['location'] = div.css('.ct-text .seg-desc p::text').extract_first()
            item['score'] = '0'
            if len(div.css('.ct-text .seg-desc p::text').extract()) > 1:
                item['score'] = re.search(r'\d+\.?\d?',div.css('.ct-text .seg-desc p::text').extract()[-1]).group()
            item['image_urls'] = [div.css('.flt1 a img::attr(src)').extract_first().split('?')[0]]
            yield item
        if hotels:
            page = response.meta['page'] + 1
            yield scrapy.Request(url=self.url.format(response.meta['addr'],page),callback=self.parse,meta={'page':page,'addr':response.meta['addr']})
