import json
import pdb 
import time
import datetime
from property.code import SUCCESS, ERROR
from content.models import   TxtContent  
from common.fun import timeStamp 
PERIOD_VALIDITY = 30*60     #订单有效期是30分钟 * 60秒

def get_product_name(producttype):
    """
    """
    name = "公告"
    if producttype == TxtContent.INFORMATION:
        name = "百事通"
    elif producttype == TxtContent.NOTIFICATION:
        name = "通知"
    elif producttype == TxtContent.ANNOUNCEMENT:
        name = "公告"
    elif producttype == TxtContent.NEWS:
        name = "社区见闻"
    
    return name 
 

def product_info(product, detail = False):
    """
    """
    product_dict = {}
    # 礼品创建人信息
    product_creator_dct = {}
    product_creator_dct['useruuid'] = product.user.uuid
    product_creator_dct['username'] = product.user.username
    
    # 礼品内容描述
    content = product.content 
    # 礼品轮播图
    if product.turns:
        turns = product.turns.split(',')
    else:
        turns = ''
    # 礼品标题
    title = product.title         
    tag_list = [(tag.id, tag.name, tag.label) for tag in product.tags.all()]
    org = {}
    
    product_dict = {
        "uuid":product.uuid,
        "creator_info":product_creator_dct,
        "content":content,
        
        "product_type":product.product_type, 
        "status" : product.status,
        "picture" : product.picture,
        "allow_comment" : product.allow_comment,
        "turns":turns,
        "title":title,
        "tags" : tag_list,  
        "org":org,
        "date" : time.mktime(product.date.timetuple()) 
    }
    if detail:
        # 详情内容可能很大，非必要不返回
        product_dict["detail"]= product.detail
    return product_dict

def product_infos_lst(products):
    # 获取详情
    product_infos = []  
    for product in products: 
        product_infos.append(product_info(product))
    return product_infos

 
def get_bill_single_dict(bill):
    """
    获取单个订单的字典
    """
    bill_dict = {}
    bill_dict["id"] = bill.id
    #bill_dict['way'] = bill.way
    # 订单详情
    bill_dict['number'] = bill.number
    bill_dict['status'] = bill.status
    create_date = time.mktime(bill.date.timetuple())
    bill_dict["create_date"] = create_date
    bill_dict["order_number"] = bill.order_number
    # 收货详情
    address_dict = {}
    address_dict['address'] = bill.address.address
    address_dict['phone'] = bill.address.phone
    address_dict['receiver'] = bill.address.receiver
    address_dict['default'] = bill.address.default
    bill_dict['address'] = address_dict
    bill_dict['express_number'] = bill.express_number
    bill_dict['express_company'] = bill.express_company
    bill_dict['purchase_way'] = bill.purchase_way     #返回账单的支付方式
    if bill.money:
        bill_dict["money"] = float(bill.money)     #返回账单的金额
    else:
        bill_dict["money"] = None
    bill_dict["coin"] = bill.coin       #返回账单的积分
    bill_dict["coin_money"] = bill.coin_money    #返回账单的积分+现金


    # 用户信息
    user_dict = {}
    user_dict['user_id'] = bill.user.id
    user_dict['user_name'] = bill.user.username
    bill_dict["user"] = user_dict
      
    return bill_dict

def get_bill_dict(bills, tag):
    bills_list = []
    if tag == 0: # 这是返回列表~
        for bill in bills:
            bill_dict = get_bill_single_dict(bill)
            bills_list.append(bill_dict)
        return bills_list
    else:
        bill_dict = get_bill_single_dict(bills)
        return bill_dict



def check_number(number):
    """验证express_number/order_number的合法性"""
    result = {'status': SUCCESS}
    if len(number) > 1024:
        result['status'] = ERROR
        result['msg'] = 'express_number too long.'

    elif len(number) == 0:
        result['status'] = ERROR
        result['msg'] = 'express_number is empty.'
    return result

def check_express_company(express_company):
    """验证express_company的合法性"""
    result = {'status': SUCCESS}
    if len(express_company) > 1024:
        result['status'] = ERROR
        result['msg'] = 'name too long.'

    elif len(express_company) == 0:
        result['status'] = ERROR
        result['msg'] = 'name is empty.'
    return result