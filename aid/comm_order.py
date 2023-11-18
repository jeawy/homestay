from aid.models import Aid, AidOrders
import uuid
from property.billno import get_aid_bill_no


def create_order(aid,  user, community ):
    # 生成互助单订单
    communityname = community.name 
    try:
        order =  AidOrders.objects.get(aid = aid)
        order.money = aid.money 
        
    except AidOrders.DoesNotExist:
        order = AidOrders()
        order.aid = aid 
        # 新建订单 
        order.billno = get_aid_bill_no( user ) 
        order.uuid = uuid.uuid4()
        order.user = user 
        order.subject = "【{0}】{1}".format(
            communityname, "互助单") 
        order.money = aid.money 
        order.community =  community  
    order.save()
    return order
