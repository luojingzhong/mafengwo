# -*- coding: utf-8 -*-
import scrapy
from feinu.items import FoodsItem
from feinu.mongodb import get_connection
from feinu.tools import get_proxy
from feinu import settings
import requests
import time
import re

class FoodsSpider(scrapy.Spider):
    name = 'foods'
    allowed_domains = ['mafengwo.cn']

    def __init__(self, **kwargs):
        conn = get_connection()
        address = conn[settings.DATABASE].address
        self.addresses = list(address.find({}))
        conn.close()

    def start_requests(self):
        while self.addresses:
            addr = self.addresses.pop(0)
            mddid = re.search(r'\d+',addr['url']).group()
            yield scrapy.Request(url='http://www.mafengwo.cn/cy/{0}/0-0-0-0-0-1.html'.format(mddid),callback=self.parse,meta={'addr':addr['addr']})

    def coordinate(self,poi_id,url):
        agent = 'http://{0}'.format(get_proxy())
        proxies = {"http": agent,'https': agent}
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,und;q=0.7',
            'Connection': 'keep-alive',
            'Host': 'pagelet.mafengwo.cn',
            'Referer': url,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
        }
        try:
            resp = requests.get('http://pagelet.mafengwo.cn/poi/pagelet/poiLocationApi?params=%7B%22poi_id%22%3A%22{0}%22%7D&_={1}'.format(poi_id,int(time.time())),proxies=proxies,headers=headers,timeout=10)
            result = resp.json()
            lng = result['data']['controller_data']['poi']['lng']
            lat = result['data']['controller_data']['poi']['lat']
            return lng,lat
        except Exception as e:
            print(e)
            return '',''

    def parse(self, response):
        for url in response.css('.poi-list .title h3 a::attr(href)').extract():
            yield response.follow(url=url,callback=self.parse_foods,meta={'addr':response.meta['addr']})
        next_page = response.css('.page-hotel .next::attr(href)').extract_first()
        if next_page:
            url_split = response.url.split('/')
            url_split[-1] = next_page
            yield response.follow(url='/'.join(url_split),callback=self.parse,meta={'addr':response.meta['addr']})

    def parse_foods(self, response):
        item = FoodsItem()
        item['belong_to'] = response.meta['addr']
        item['url'] = response.url
        item['image_urls'] = [response.css('.pic-r a img::attr(src)').extract_first()]
        item['name'] = response.css('.title h1::text').extract_first()
        item['location'] = ''
        item['telphone'] = ''
        for li in response.css('.m-info ul li'):
            if li.css('.icon-location'):
                item['location'] = ''.join(li.css('::text').extract()).strip()
            elif li.css('.icon-tel'):
                item['telphone'] = ''.join(li.css('::text').extract()).strip()
        item['score'] = response.css('.score .score-info em::text').extract_first()
        poi_id = re.search(r'\d+',response.url).group()
        lng,lat = self.coordinate(poi_id,response.url)
        item['lng'] = lng
        item['lat'] = lat
        yield item
