import redis

class RedisSubscri():
    # 订阅模式：如果没有消费者，消息会被丢弃。
    # 
    def __init__(self ):
        self.coon=redis.Redis(host="123.57.62.122", password='myredis')

    def publish(self,message,channel):#发布
        # 返回订阅者数量
        # 订阅者数量为0 的时候，要发送短信给开发者，并且直接提交订单
        # publish 返回的是订阅者的数量。
        return self.coon.publish(channel,message) 

    def subscribe(self,channel):#订阅
        pub=self.coon.pubsub() # 
        pub.subscribe(channel)
        pub.parse_response()
        return  pub
    
    def getconn(self):#订阅
        return self.coon


    def unsubsceribe(self,channel):#取消订阅
        self.coon.pubsub().unsubscribe(channel)

def productor():
    # 消息发布端
    redisd=RedisSubscri()
    conn = redisd.getconn()
    conn.lpush("bills", "23232233223")

productor()