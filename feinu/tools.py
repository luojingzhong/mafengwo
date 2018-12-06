# coding: utf-8
import redis
from feinu import settings

def get_proxy():
    r = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
    while True:
        agent = r.srandmember('agent_ip')
        if agent:
            break
    return agent