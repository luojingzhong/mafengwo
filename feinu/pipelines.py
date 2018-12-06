# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from feinu.mongodb import SaveSeason,SaveAddress,SaveScenic,SaveFavorable,SaveFoods,SaveTravel,SaveHotel,encrypt_data
from feinu.items import SeasonItem,AddressItem,ScenicItem,FavorableItem,FoodsItem,TravelItem,HotelItem
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exceptions import DropItem
from scrapy.http import Request
import redis as red
import tldextract

class FeinuPipeline(object):
    def __init__(self, host, port):
        pool = red.ConnectionPool(host=host, port=port, decode_responses=True)
        self.redis = red.StrictRedis(connection_pool=pool)

    @classmethod
    def from_crawler(cls, crawler):
        '''
            scrapy为我们访问settings提供了这样的一个方法，这里，
            我们需要从settings.py文件中，取得数据库的URI和数据库名称
        '''
        return cls(
            host = crawler.settings.get('REDIS_HOST'),
            port = crawler.settings.get('REDIS_PORT')
        )

    def process_item(self, item, spider):
        img_urls = []
        if item.get('image_urls',None) is not None:
            for img_url in item['image_urls']:
                if img_url and img_url != 'None':
                    if not self.redis.sismember('crawled_travel_images',img_url):
                        self.redis.lpush('travel_images',img_url)
                    img_urls.append(encrypt_data(img_url))
            item['img_urls'] = img_urls
        save = None
        if isinstance(item,SeasonItem):
            save = SaveSeason()
        elif isinstance(item,AddressItem):
            save = SaveAddress()
        elif isinstance(item,ScenicItem):
            save = SaveScenic()
        elif isinstance(item,FavorableItem):
            save = SaveFavorable()
        elif isinstance(item,FoodsItem):
            save = SaveFoods()
        elif isinstance(item,TravelItem):
            save = SaveTravel()
        elif isinstance(item,HotelItem):
            save = SaveHotel()
        if save is not None:
            save.execute(item)

class MyImagesPipeline(ImagesPipeline):

    def get_media_requests(self, item, info):
        if dict(item).get('image_urls',None) is not None:
            for image_url in item['image_urls']:
                url = image_url.split('?')[0]
                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,und;q=0.7',
                    'Connection': 'keep-alive',
                    'Host': '.'.join(tldextract.extract(url)),
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
                }
                yield Request(url=url,headers=headers)

    def item_completed(self, results, item, info):
        if dict(item).get('image_urls',None) is not None:
            image_paths = [x['path'] for ok, x in results if ok]
            if not image_paths:
                raise DropItem("Item contains no images")
            item['image_urls'] = image_paths
        return item
