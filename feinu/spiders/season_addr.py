# -*- coding: utf-8 -*-
from scrapy.selector import Selector
from feinu.items import SeasonItem
from feinu.mongodb import translate_url
import scrapy
import json

class CtripSpider(scrapy.Spider):
    name = 'season'
    allowed_domains = ['mafengwo.cn']
    # start_urls = ['http://you.ctrip.com/countrysightlist/china110000/p1.html']
    headers = {
    'Host': 'www.mafengwo.cn',
    'Referer': 'http://www.mafengwo.cn/',
    }

    def start_requests(self):
        urls = {
            '1月': '113','2月': '116','3月': '119','4月': '122','5月': '125','6月': '128','7月': '131','8月': '134','9月': '137','10月': '140','11月': '143','12月': '146',
            '草原':'50',
            '星空':'98',
            '赏花':'35',
            '雪景':'68',
            '海岛':'59',
            '极限运动':'38',
            '滑雪':'56',
            '温泉':'53',
            '当地节庆':'32',
            '温暖地点':'71',
            '避暑':'170',
            '极光':'181'
        }
        for tag,code in urls.items():
            yield scrapy.FormRequest(url = 'http://www.mafengwo.cn/mdd/base/filter/getlist',formdata = {'tag[]': code,'page':'1'},callback = self.parse,meta = {'page':1,'tag':tag,'code':code})

    def parse(self, response):
        data = json.loads(response.text)
        body = Selector(text=data['list'])
        for li in body.css('li'):
            item = SeasonItem()
            item['addr'] = li.css('.img a .title::text').extract_first()
            item['introduction'] = li.css('.info .detail::text').extract_first()
            item['image_urls'] = [li.css('.img a img::attr(data-original)').extract_first()]
            item['tag'] = response.meta['tag']
            item['url'] = translate_url(li.css('.img a::attr(href)').extract_first(),response.url)
            yield item
        page_html = Selector(text=data['page'])
        if page_html.css('.pg-next').extract():
            page = response.meta['page'] + 1
            meta = {'page': page,'tag': response.meta['tag'],'code': response.meta['code']}
            yield scrapy.FormRequest(url = 'http://www.mafengwo.cn/mdd/base/filter/getlist',formdata = {'tag[]': response.meta['code'],'page':str(page)},callback = self.parse,meta = meta)

    def parse_item(self, url):
        print(response.meta['category'])
