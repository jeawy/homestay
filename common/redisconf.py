import redis
from django.conf import settings
import pdb

def redisconn():
    # 连接redis
    pool = redis.ConnectionPool(host=settings.REDIS['HOST'],
        port=settings.REDIS['PORT'] ,max_connections=10, 
        password=settings.REDIS['PASSWORD']
        ,decode_responses=True)
    conn = redis.StrictRedis(connection_pool=pool) 
    return conn

def set_access_token(conn, seconds, value):
    # 设置微信的访问token
    conn.setex("wx_access_token", seconds , value)

def get_access_token(conn ):
    # 获取微信的访问token
    conn.get("wx_access_token")
 

class RedisSubscri():
    # 订阅模式：如果没有消费者，消息会被丢弃。
    # 
    def __init__(self):
        self.coon= redisconn()


    def publish(self,message,channel):#发布
        # 返回订阅者数量
        # 订阅者数量为0 的时候，要发送短信给开发者，并且直接提交订单
        return self.coon.publish(channel,message) 


    def subscribe(self,channel):#订阅
        pub=self.coon.pubsub()
        pub.subscribe(channel)
        pub.parse_response()
        return  pub

    def unsubsceribe(self,channel):#取消订阅
        self.coon.pubsub().unsubscribe(channel)
    
    def getconn(self):#订阅
        return self.coon

 

def productor():
    # 消息发布端
    redisd=RedisSubscri()
    while True:
        n=input("请输入你要发布的频道:")
        m=input("请输入你要发布的消息:")
        print(redisd.publish(m,n))

def consumer():
    # 订阅端
    resad = RedisSubscri()
    meaaag = resad.subscribe('1')
    while True:
        print('监听开始')
        meaaage=meaaag.parse_response()
        print(meaaage[2].decode('utf-8'))
        if meaaage[2].decode('utf-8')=='1':
            m=meaaag.unsubscribe('fm9.01')
            print(m)
            print('取消订阅成功')
            break