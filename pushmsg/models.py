from basedatas.models import BaseDate

class Msg(BaseDate):
    # 待推送的消息池
    # 推送策略：单条推送或者目标推送群体不超过5个人的时候，实时推送，
    # 否则先将推送策略存储在本表中，由推送服务器按照推送策略进行消息推送
    
    class Meta:
        default_permissions = ()
 