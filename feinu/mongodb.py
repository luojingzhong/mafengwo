# -*- coding: utf-8 -*-
from feinu import settings
from pymongo import MongoClient
from feinu.tools import get_proxy
import tldextract
import requests
import random
import hashlib
import uuid
import time

hosts = ['192.168.1.164:20000','192.168.1.192:20000','192.168.1.118:20000']
host = hosts.pop(0)

def get_connection():
    conn = MongoClient(host=host,socketTimeoutMS=20000)
    return conn

def encrypt_data(obj):
    return hashlib.md5(obj.encode('utf-8')).hexdigest()

def now_time():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def time_stamp():
    return int(time.time())

def generate_id():
    return str(uuid.uuid1()) + str(random.randint(100000,999999))

def translate_url(url,source_url):
    source_domain = '.'.join(tldextract.extract(source_url))
    url = url.strip()
    domain = '.'.join(tldextract.extract(url))
    if domain == '..':
        url = 'http://{0}{1}'.format(source_domain,url)
    elif url.startswith('//'):
        url = 'http:{0}'.format(url)
    return url

def download_img(url):
    return
    # agent = 'http://{0}'.format(get_proxy())
    # proxies = {"http": agent,'https': agent}
    path = settings.DOWNLOAD_DIR + encrypt_data(url) + '.jpg'
    if url:
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,und;q=0.7',
            'Connection': 'keep-alive',
            'Host': '.'.join(tldextract.extract(url)),
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
        }
        with open(path,'wb+') as f:
            f.write(requests.get(url,headers=headers).content)

class SaveSeason(object):
    def __init__(self):
        self.conn = get_connection()
        self.db = self.conn[settings.DATABASE]

    def execute(self,item):
        # download_img(item['img_url'])
        # self.save_address(item)
        _id = encrypt_data(item['addr'])
        if self.conn[settings.DATABASE].address.find_one({'_id':_id}):
            self.save_season(item)
            self.save_relation(item)
        self.conn.close()

    def save_address(self,item):
        SaveAddress().execute(item)

    def save_season(self,item):
        _id = encrypt_data(item['tag'])
        season = self.db['season']
        if not season.find_one({'_id': _id}):
            season.insert({'_id': _id,'tag': item['tag']})

    def save_relation(self,item):
        addr_id = encrypt_data(item['addr'])
        tag_id = encrypt_data(item['tag'])
        tag_addr_realtion = self.db['tag_addr_realtion']
        if not tag_addr_realtion.find_one({'tag_id': tag_id,'addr_id': addr_id}):
            tag_addr_realtion.insert({'_id': generate_id(),'tag_id': tag_id,'addr_id': addr_id})

class SaveAddress(object):
    """docstring for SaveAddress"""
    def __init__(self):
        self.conn = get_connection()
        self.db = self.conn[settings.DATABASE]

    def execute(self,item):
        _id = encrypt_data(item['addr'])
        address = self.db['address']
        if not address.find_one({'_id': _id}):
            data = dict(item)
            data['_id'] = _id
            data['get_time'] = time_stamp()
            address.insert(data)
        else:
            address.update_one({'_id': _id},{'$set': {'introduction': item['introduction']}})
        self.conn.close()

class SaveScenic(object):
    """docstring for SaveScebic"""
    def __init__(self):
        self.conn = get_connection()
        self.db = self.conn[settings.DATABASE]

    def execute(self, item):
        _id = encrypt_data(item['name'])
        addr_id = encrypt_data(item['belong_to'])
        scenic = self.db['scenic']
        if not scenic.find_one({'_id': _id}):
            # download_img(item['img_url'])
            # image_urls = []
            # for img_url in item['image_urls']:
            #     download_img(img_url)
            #     image_urls.append(encrypt_data(img_url))
            data = dict(item)
            data['_id'] = _id
            # data['img_url'] = encrypt_data(item['img_url'])
            # data['image_urls'] = image_urls
            data.pop('belong_to')
            scenic.insert(data)
        scenic_addr_relation = self.db['scenic_addr_relation']
        if not scenic_addr_relation.find_one({'scenic_id':_id,'addr_id':addr_id}):
            scenic_addr_relation.insert({'_id':generate_id(),'scenic_id':_id,'addr_id':addr_id})
        self.conn.close()

class SaveFavorable(object):
    """docstring for SaveFavorable"""
    def __init__(self):
        self.conn = get_connection()
        self.db = self.conn[settings.DATABASE]

    def execute(self, item):
        datas = []
        scenic_id = encrypt_data(item['belong_to'])
        favorable = self.db['favorable']
        favorable.delete_many({'scenic_id': scenic_id})
        for data in item['datas']:
            _id = encrypt_data(data['url'])
            data['_id'] = _id
            data['scenic_id'] = scenic_id
            if not favorable.find_one({'_id':_id}):
                datas.append(data)
        if datas:
            favorable.insert(datas)
        self.conn.close()

class SaveFoods(object):
    """docstring for SaveFoods"""
    def __init__(self):
        self.conn = get_connection()
        self.db = self.conn[settings.DATABASE]

    def execute(self, item):
        _id = encrypt_data(item['url'])
        addr_id = encrypt_data(item['belong_to'])
        foods = self.db['foods']
        if not foods.find_one({'_id': _id}):
            # download_img(item['img_url'])
            data = dict(item)
            data['addr_id'] = addr_id
            # data['img_url'] = encrypt_data(item['img_url'])
            data['_id'] = _id
            data.pop('belong_to')
            foods.insert(data)
        else:
            foods.update_one({'_id':_id},{'$set':{'score':item['score']}})
        self.conn.close()

class SaveTravel(object):
    """docstring for SaveTravel"""
    def __init__(self):
        self.conn = get_connection()
        self.db = self.conn[settings.DATABASE]

    def execute(self, item):
        _id = encrypt_data(item['url'])
        addr_id = encrypt_data(item['belong_to'])
        travel = self.db['travels']
        if not travel.find_one({'_id': _id}):
            # download_img(item['img_url'])
            # for img_url in item['image_urls']:
            #     download_img(img_url)
            data = dict(item)
            data['_id'] = _id
            data['addr_id'] = addr_id
            # data['img_url'] = encrypt_data(item['img_url'])
            data.pop('belong_to')
            travel.insert(data)
        self.conn.close()

class SaveHotel(object):
    """docstring for SaveHotel"""
    def __init__(self):
        self.conn = get_connection()
        self.db = self.conn[settings.DATABASE]

    def execute(self, item):
        _id = encrypt_data(item['url'])
        addr_id = encrypt_data(item['belong_to'])
        hotel = self.db['hotels']
        # print('----->',hotel.find_one({'_id': _id}))
        if not hotel.find_one({'_id': _id}):
            # download_img(item['img_url'])
            data = dict(item)
            # data['img_url'] = encrypt_data(item['img_url'])
            data['addr_id'] = addr_id
            data['_id'] = _id
            data.pop('belong_to')
            hotel.insert(data)
        else:
            hotel.update_one({'_id': _id},{'$set':{'score':item['score']}})
        self.conn.close()
