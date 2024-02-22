from datetime import datetime
import string
import random
import time
import json
from bills.models import BillSpec

def getbillno():
    # 生成订单号
    g_timestr = "%Y%m%d%H%M%S%f"
    code = ''.join(random.choice(string.digits) for i in range(4))
    timestr = datetime.now().strftime(g_timestr)  
    orderno = "S" + timestr  + code
    return orderno

def getbill(bill):
    result= {
            "uuid":bill.uuid,
            "billno":bill.billno,
            "subject":bill.subject,
            "date":time.mktime(bill.date.timetuple()), 
            "payway":bill.payway,
            "paybillno":bill.paybillno,
            "express_number":bill.express_number,
            "express_company":bill.express_company,
            "receiver":bill.receiver,
            "receiver_phone":bill.receiver_phone,
            "receiver_address":bill.receiver_address,
            "remark":bill.remark, 
            "billtype":bill.billtype,  
            
            "user":{
                "username" : bill.user.username,
                "uuid" : bill.user.uuid,
                "phone" : bill.user.phone,
                "thumbnail_portait" : bill.user.thumbnail_portait,
            },
            "status":bill.status,
            "ordertype":bill.ordertype,
            "delivery":bill.delivery,
            "delivery_way":bill.delivery_way,
            "spec": list(BillSpec.objects.filter(bill = bill).values(
                "number",
                "name", 
                "spec__product__uuid",
                "picture",
                "title",
                "price",
                "content",
                "money" 
                ))
            } 
    money = 0
    for spec in BillSpec.objects.filter(bill = bill):
        money +=  spec.price * spec.number
    
    result['money'] = money
    if bill.extras:
        result['extras'] = json.loads( bill.extras)
    else:
        result['extras'] =  []

        
    return result

def get_bill_money(bill):
    # 获取订单金额
    money = 0
    for spec in BillSpec.objects.filter(bill = bill):
        money +=  spec.price * spec.number
    
    return money 