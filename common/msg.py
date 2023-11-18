# 发通知：app内部、短信、微信通知
from common.sms import send_sms
from notice.comm import NoticeMgr  

def send_notice(title = "", 
                content="",
                appurl="",
                user = None,
                entity_type = None,
                app = True,
                msg=False, 
                smstype = "", 
                phone=None,
                code = "",
                wx=False):
    # 发通知：app内部、短信、微信通知
    """
    NoticeMgr.create(
            title = "您的订单已发货",
            content = "您的订单已发货,点击查看物流状态" ,
            user = bill.user,
            appurl = "/pages/order/detail?uuid="+str(bill.uuid),
            entity_type=  EntityType.BILL
        )
    """
    if app:
        # 发送app通知
        NoticeMgr.create(
            title = title,
            content = content,
            user = user,
            appurl = appurl,
            entity_type =  entity_type
        )
        
    if msg:
       #短信通知
       send_sms(smstype = smstype,phone = phone, code = code)

    if wx:
        # 小程序内部通知
        pass