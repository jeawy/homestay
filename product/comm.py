import json
import pdb 
import time
import datetime
from property.code import SUCCESS, ERROR
from product.models import Product,Specifications
from product.models import PurchaseWay,Bill
from common.fun import timeStamp
from product.purchase_way_views import sing_goods_ways
PERIOD_VALIDITY = 30*60     #订单有效期是30分钟 * 60秒

def get_product_name(producttype):
    """
    """
    name = "公告"
    if producttype == Product.INFORMATION:
        name = "百事通"
    elif producttype == Product.NOTIFICATION:
        name = "通知"
    elif producttype == Product.ANNOUNCEMENT:
        name = "公告"
    elif producttype == Product.NEWS:
        name = "社区见闻"
    
    return name 

def specifications_infos_lst(specs):
    # 获取礼品规格详情
    specifications_infos = []
    for spec in specs:
        spec_dct = {}
        id = spec.id
        # 礼品价格
        price = str(spec.price)
        # 礼品数量
        num = spec.number
        # 积分数量
        coin = str(spec.coin)
        # 礼品名称
        name = spec.name
        # 礼品规格名称
        content = spec.content
        # 兑换的数量
        conversion_num = spec.conversion_num
        # 交易数量
        business_num = spec.business_num
        # 购买方式
        purchase_way = spec.purchase_way

        spec_dct = {
            "id":id,
            "price":price,
            "num":num,
            "coin":coin,
            "name":name,
            "content":content,
            "conversion_num":conversion_num,
            "business_num":business_num,
            "purchase_way":purchase_way
        }
        specifications_infos.append(spec_dct)
    return specifications_infos

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

def update_bill_closed(bills):
    # 将订单的状态更新为关闭
    for bill in bills:
        # 获取现在时间
        now = timeStamp(datetime.datetime.now())
        # 获取到以后将计算是否过期
        create_time = timeStamp(bill.date)
        if now - create_time > PERIOD_VALIDITY:
            # 订单状态改为关闭
            bill.status = Bill.CLOSED
            specifications = bill.specifications
            # 恢复库存
            specifications.number = specifications.number + bill.number
            bill.save()
            specifications.save()

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
    # 礼品信息
    try:
        spec = Specifications.objects.get(id=bill.specifications.id)
        product_dict = {}
        product_dict['id'] = spec.id
        product_dict['picture'] = spec.product.picture
        product_dict['content'] = spec.content
        product_dict['specifications'] = spec.name
        bill_dict["product"] = product_dict
    except Product.DoesNotExist:
        pass
    # # 返回商品的支付方式
    # bill_dict['purchase_way'] = PurchaseWay.objects. \
    #     filter(goods_id=spec.product). \
    #     values('purchase_way', 'coin', 'cash', 'coin_cash')
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