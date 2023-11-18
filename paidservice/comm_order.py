from property.code import SUCCESS, ERROR
import time
from paidservice.models import PaidOrder 
from datetime import datetime
 
 

def get_paidservice_order_detail(order, perm):
    # perm = True时，代表物业获取更详细的订单信息
    # 订单
    order_dict = {}
    order_dict['uuid'] = order.uuid
    order_dict['subject'] = order.subject
    order_dict['servicenprice'] = order.servicenprice 
    order_dict['servicenunit'] = order.servicenunit
    order_dict['billno'] = order.billno
    order_dict['number'] = order.number
    order_dict['money'] = order.money
    order_dict['payway'] = order.payway
    order_dict['paybillno'] = order.paybillno
    order_dict['status'] = order.status
    order_dict['score'] = order.score
    order_dict['date'] = time.mktime(order.date.timetuple())
    order_dict['remark'] = order.remark
    if perm:
        order_dict['communityname'] = order.community.name
        order_dict['communityuuid'] = order.community.uuid
        order_dict['feerate'] = order.feerate
        order_dict['username'] = order.user.username
        order_dict['phone'] = order.user.phone
        

    return order_dict


def get_paidservice_orders(orders, perm):
    # 订单
    # perm = True时，代表物业获取更详细的订单信息
    order_ls = []
    for order in orders:
        order_dict = get_paidservice_order_detail(order, perm)
        order_ls.append(order_dict)

    return order_ls
