import json
import pdb 
import time 
 

def get_orders(orders):
    orders_ls = []
    for order in orders:
        orders_ls.append(order_dict(order))
    return orders_ls


def order_dict(order):
    """
    """
    order_dict = {}
    order_dict['subject'] = order.subject
    order_dict['org'] = order.org.alias
    order_dict['billno'] = order.billno
    order_dict['total'] = order.total
    order_dict['number'] = order.number

    order_dict['money'] = order.money
    order_dict['left'] = order.left 
    order_dict['user'] = order.user.username 
    order_dict['payway'] = order.payway
    order_dict['date'] = time.mktime(order.date.timetuple())
    order_dict['status'] = order.status
    return order_dict

def specifications_infos_lst(specs):
    # 获取短信规格详情
    specifications_infos = []
    for spec in specs:
        spec_dct = {}
        id = spec.id
        # 短信价格
        price = str(spec.price)
        # 短信数量
        number = spec.number 
        # 短信名称
        name = spec.name  

        spec_dct = {
            "id":id,
            "price":price,
            "number":number, 
            "name":name, 
        }
        specifications_infos.append(spec_dct)
    return specifications_infos

def msg_info(msg):
    """
    """
    msg_dct = {}
    # 短信创建人信息
    msg_creator_dct = {}
    msg_creator_dct['useruuid'] = msg.user.uuid
    msg_creator_dct['username'] = msg.user.username
    
    # 短信内容描述
    content = msg.content 
    # 短信轮播图
    if msg.turns:
        turns = msg.turns.split(',')
    else:
        turns = ''
        
    msg_dct = {
        "uuid":msg.uuid,
        "creator_info":msg_creator_dct,
        "content":content,
        "detail":msg.detail,   
        "status" : msg.status,
        "turns":turns,
        "title":msg.title , 
        "date" : time.mktime(msg.date.timetuple()), 
        "specifications":specifications_infos_lst(msg.msg_specifications.all())
    }
    return msg_dct

def msg_infos_lst(msgs):
    # 获取详情
    msg_infos = []  
    for msg in msgs: 
        msg_infos.append(msg_info(msg))
    return msg_infos
  