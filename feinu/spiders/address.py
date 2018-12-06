# -*- coding: utf-8 -*-
from scrapy.selector import Selector
from feinu.items import AddressItem,ScenicItem,FavorableItem,FoodsItem
from feinu.mongodb import translate_url
import requests
import scrapy
import json
import time
import re

class AddressSpider(scrapy.Spider):
    name = 'address'
    allowed_domains = ['mafengwo.cn']

    def start_requests(self):
        yield scrapy.FormRequest(url='http://www.mafengwo.cn/mdd/base/list/pagedata_citylist',formdata={'mddid': '21536','page':'1'},callback=self.parse,meta={'mddid': '21536','page':1})

    def parse(self, response):
        data = json.loads(response.text)
        body = Selector(text=data['list'])
        for li in body.css('li'):
            item = AddressItem()
            item['addr'] = li.css('.img a .title::text').extract_first().replace('\n','').strip()
            item['introduction'] = li.css('.caption .detail::text').extract_first().replace('\n','').strip()
            item['image_urls'] = [li.css('.img a img::attr(data-original)').extract_first()]
            item['url'] = translate_url(li.css('.img a::attr(href)').extract_first(),response.url)
            addr_id = li.css('.img a::attr(data-id)').extract_first()
            time.sleep(0.5)
            yield scrapy.Request(url=item['url'],callback=self.parse_detail,meta={'item': item,'addr_id': addr_id})
        page_html = Selector(text=data['page'])
        if page_html.css('.pg-next').extract():
            time.sleep(1)
            page = response.meta['page'] + 1
            yield scrapy.FormRequest(url='http://www.mafengwo.cn/mdd/base/list/pagedata_citylist',formdata={'mddid': response.meta['mddid'],'page':str(page)},callback=self.parse,meta={'mddid': response.meta['mddid'],'page': page})

    def parse_detail(self, response):
        if response.css('.navbar-mdd'):
            mddid = re.search(r'\d+',response.url).group()
            yield scrapy.FormRequest(url='http://www.mafengwo.cn/mdd/base/list/pagedata_citylist',formdata={'mddid': mddid,'page':'1'},callback=self.parse,meta={'mddid': mddid,'page':1})
        else:
            yield response.meta['item']
