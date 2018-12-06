# -*- coding: utf-8 -*-
from scrapy.selector import Selector
from feinu.items import ScenicItem,FavorableItem
from feinu.mongodb import get_connection,translate_url
from feinu import settings
from feinu.tools import get_proxy
import requests
import scrapy
import json
import time
import redis
import re


class DetailsSpider(scrapy.Spider):
    name = 'scenic'
    allowed_domains = ['mafengwo.cn']

    def __init__(self,**kwargs):
        conn = get_connection()
        address = conn[settings.DATABASE].address
        self.addresses = list(address.find({}))
        conn.close()

    def start_requests(self):
        while self.addresses:
            addr = self.addresses.pop(0)
            mddid = re.search(r'\d+',addr['url']).group()
            scenic_data = {
                'sAct': 'KMdd_StructWebAjax|GetPoisByTag',
                'iMddid': mddid,
                'iTagId': '0',
                'iPage': '1',
            }
            yield scrapy.FormRequest(url='http://www.mafengwo.cn/ajax/router.php',formdata=scenic_data,callback=self.scenic,meta={'params':scenic_data,'addr':addr['addr']})

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
            return '',''

    def scenic(self,response):
        data = json.loads(response.text)['data']
        body = Selector(text=data['list'])
        for li in body.css('li'):
            url = translate_url(li.css('a::attr(href)').extract_first(),response.url)
            img_url = li.css('.img img::attr(src)').extract_first()
            yield scrapy.Request(url=url,callback=self.parse_scenic,meta={'img_url':img_url,'addr':response.meta['addr']})
        page_html = Selector(text=data['page'])
        if page_html.css('.pg-next').extract():
            params = response.meta['params']
            params['page'] = page_html.css('.pg-next::attr(data-page)').extract_first()
            yield scrapy.FormRequest(url='http://www.mafengwo.cn/ajax/router.php',formdata=params,callback=self.scenic,meta={'params':params,'addr':response.meta['addr']})

    def parse_scenic(self,response):
        item = ScenicItem()
        item['belong_to'] = response.meta['addr']
        item['name'] = response.css('.title h1::text').extract_first()
        item['url'] = response.url
        item['introduction'] = ''.join(response.css('.mod-detail .summary::text').extract())
        item['traffic'] = ''
        item['ticket'] = ''
        item['open_time'] = ''
        for dl in response.css('.mod-detail dl'):
            if dl.css('dt::text').extract_first() == '交通':
                item['traffic'] = ''.join(dl.css('dd::text').extract())
            elif dl.css('dt::text').extract_first() == '门票':
                item['ticket'] = ''.join(dl.css('dd div::text').extract())
            elif dl.css('dt::text').extract_first() == '开放时间':
                item['open_time'] = ''.join(dl.css('dd::text').extract())
        item['image_urls'] = [response.meta['img_url']] + response.css('.photo img::attr(src)').extract()
        item['location'] = response.css('.mod-location .sub::text').extract_first()
        poi_id = re.search(r'\d+',response.url).group()
        lng,lat = self.coordinate(poi_id,response.url)
        item['lng'] = lng
        item['lat'] = lat
        yield item
        url = 'http://pagelet.mafengwo.cn/poi/pagelet/poiTicketsApi?params=%7B%22poi_id%22%3A%22{0}%22%7D&_={1}'.format(poi_id,int(time.time()))
        headers = {
            'Host': 'pagelet.mafengwo.cn',
            'Referer': response.url
        }
        yield scrapy.Request(url=url,callback=self.parse_favorable,headers=headers,meta={'scenic': item['name']})

    def parse_favorable(self,response):
        item = FavorableItem()
        item['belong_to'] = response.meta['scenic']
        item['datas'] = []
        data = json.loads(response.text)['data']
        body = Selector(text=data['html'])
        for tr in body.css('tbody tr'):
            each_one = {}
            each_one['f_type'] = tr.css('.type::text').extract_first()
            each_one['title'] = tr.css('.pro a::attr(title)').extract_first()
            each_one['price'] = tr.css('.price::text').extract_first()
            each_one['url'] = tr.css('.pro a::attr(href)').extract_first()
            item['datas'].append(each_one)
        yield item
