# -*- coding: utf-8 -*-
import scrapy
from feinu.mongodb import get_connection,encrypt_data
from feinu import settings
from scrapy.selector import Selector
from feinu.items import TravelItem
import json
import re

class TravelsSpider(scrapy.Spider):
    name = 'travels'
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
            data = {
                'mddid': mddid,
                'pageid': 'mdd_index',
                'sort': '1',
                'cost': '0',
                'days': '0',
                'month': '0',
                'tagid': '0',
                'page': '1'
            }
            yield scrapy.FormRequest(url='http://www.mafengwo.cn/gonglve/ajax.php?act=get_travellist',formdata=data,callback=self.parse,meta={'page':1,'mddid':mddid,'addr':addr['addr']})

    def parse(self, response):
        data = json.loads(response.text)
        body = Selector(text=data['list'])
        for div in body.css('.tn-item'):
            author = div.css('.tn-extra .tn-user a::text').extract_first()
            if not author:
                continue
            meta = {
                'addr': response.meta['addr'],
                'author': author,
                'img_url': div.css('.tn-image a img::attr(data-original)').extract_first()
            }
            yield response.follow(url=div.css('.tn-image a::attr(href)').extract_first(),callback=self.travel_detail,meta=meta)
        page_html = Selector(text=data['page'])
        if page_html.css('.pg-next'):
            page = response.meta['page'] + 1
            if page <= 3:
                params = {
                    'mddid': response.meta['mddid'],
                    'pageid': 'mdd_index',
                    'sort': '1',
                    'cost': '0',
                    'days': '0',
                    'month': '0',
                    'tagid': '0',
                    'page': str(page)
                }
                meta={'page':page,'mddid':response.meta['mddid'],'addr':response.meta['addr']}
                yield scrapy.FormRequest(url='http://www.mafengwo.cn/gonglve/ajax.php?act=get_travellist',formdata=params,callback=self.parse,meta=meta)

    def travel_detail(self, response):
        content = []
        image_urls = [response.meta['img_url']]
        for ele in response.xpath('//div[@class="_j_content_box"]/*'):
            if ele.css('a img'):
                img_url = ele.css('img::attr(data-rt-src)').extract_first()
                if img_url:
                    image_urls.append(img_url)
                    content.append('img:{0}'.format(encrypt_data(img_url)))
            else:
                c = re.sub(r'(<.*?>)|\n|\s+','',ele.extract(),flags=re.S)
                content.append(c)
        item = TravelItem()
        item['belong_to'] = response.meta['addr']
        item['title'] = response.css('.headtext::text').extract_first()
        item['image_urls'] = image_urls
        item['release_time'] = ''
        item['author'] = response.meta['author']
        item['content'] = content
        item['url'] = response.url
        iid = re.search(r'\d+',response.url).group()
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,und;q=0.7',
            'Connection': 'keep-alive',
            'Host': 'pagelet.mafengwo.cn',
            'Referer': response.url,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
        }
        yield scrapy.Request('http://pagelet.mafengwo.cn/note/pagelet/headOperateApi?params=%7B%22iid%22%3A%22{0}%22%7D&'.format(iid),callback=self.parse_time,headers=headers,meta={'item':item})

    def parse_time(self, response):
        data = json.loads(response.text)
        body = Selector(text=data['data']['html'])
        item = response.meta['item']
        item['release_time'] = body.css('.time::text').extract_first()
        yield item
        # print(item)
