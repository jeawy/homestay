import json
import pdb 
import time
import datetime
from property.code import SUCCESS, ERROR
from product.models import Product,Specifications
from product.models import PurchaseWay,Bill
from common.fun import timeStamp
from product.purchase_way_views import sing_goods_ways,back_sing_goods_way
PERIOD_VALIDITY = 30*60     #订单有效期是30分钟 * 60秒



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
        # 虚拟币数量
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
            "number":num,
            "coin":coin,
            "name":name,
            "content":content,
            "conversion_num":conversion_num,
            "business_num":business_num,
            "purchase_way":purchase_way
        }
        specifications_infos.append(spec_dct)
    return specifications_infos

def gift_infos_lst(gifts):
    # 获取礼品详情
    gift_infos = []
    
    for product in gifts: 
        gift_infos.append(get_single_gift(product))
    return gift_infos

def get_single_gift(product):
    category_lst = []
    specifications_lst = []
    gift_creator_dct = {}
    gift_creator_dct['userid'] = product.user.id
    gift_creator_dct['username'] = product.user.username
    gift_id = product.id
    # 礼品内容描述
    content = product.content
    # 礼品图片
    picture = product.picture
    # 礼品轮播图
    if product.turns:
        turns = product.turns.split(',')
    else:
        turns = ''
    # 礼品标题
    title = product.title
    # 礼品类别
    if product.category:
        category = product.category.name
    else:
        category = ""
    # 礼品规格
    specifications = product.product_specifications.all()
    specifications_lst = specifications_infos_lst(specifications)
    purchase_way = back_sing_goods_way(product.id)
    
    tag_list = [(tag.id, tag.name, tag.label) for tag in product.tags.all()]
    gift_dct = {
        "id":gift_id,
        "uuid":product.uuid,
        "creator_info":gift_creator_dct,
        "content":content,
        "picture":picture,
        "turns":turns,
        "title":title,
        "isbook" : product.isbook,
        "gifttype" : product.gifttype,
        "cardtype" : product.cardtype,
        "ready" : product.ready,
        "recommend" : product.recommend,
        "tags" : tag_list,
        "category":category,
        "categoryid":product.category.id,
        "specifications":specifications_lst,
        "purchase_way":purchase_way
    }

    return gift_dct

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
        gift_dict = {}
        gift_dict['id'] = spec.id
        gift_dict['picture'] = spec.product.picture
        gift_dict['content'] = spec.content
        gift_dict['specifications'] = spec.name
        bill_dict["product"] = gift_dict
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