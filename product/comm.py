import json
import pdb 
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import traceback
import os
from common.logutils import getLogger
from property.code import SUCCESS, ERROR
from product.models import Product,Specifications, ProductImages
from product.models import PurchaseWay,Bill
from common.fun import timeStamp
from django.conf import settings
from common.fileupload import FileUpload
from tags.comm import add 
from common.holiday import check_holiday, get_holidays
from product.purchase_way_views import sing_goods_ways,back_sing_goods_way

PERIOD_VALIDITY = 30*60     #订单有效期是30分钟 * 60秒
logger = getLogger(True, 'product', False)

def editData(product, data, request):
    user = request.user
    
    if 'isbook' in data:
        isbook = data['isbook'].strip()
        product.isbook = isbook 
     
    if 'ready' in data:
        ready = data['ready'].strip()
        product.ready = ready 

    if 'recommend' in data:
        recommend = data['recommend'].strip()
        product.recommend = recommend 

    if 'turns' in data:
        turns = data['turns'].strip()
        product.turns = turns 
    
    if 'producttype' in data:
        producttype = data['producttype'].strip()
        product.producttype = producttype 
    
    if 'producttype' in data:
        producttype = data['producttype'].strip()
        product.producttype = producttype 
    
    if 'cardtype' in data:
        cardtype = data['cardtype'].strip()
        product.cardtype = cardtype 
    

    if 'workday_price' in data:
        workday_price = data['workday_price'].strip()
        try:  
            product.workday_price = float(workday_price) 
        except ValueError:
            pass
    
    if 'workday_price' in data:
        workday_price = data['workday_price'].strip()
        try:  
            product.workday_price = float(workday_price) 
        except ValueError:
            pass
    
    if 'weekday_price' in data:
        weekday_price = data['weekday_price'].strip()
        try:  
            product.weekday_price = float(weekday_price) 
        except ValueError:
            pass
    if 'holiday_price' in data:
        holiday_price = data['holiday_price'].strip()
        try:  
            product.holiday_price = float(holiday_price) 
        except ValueError:
            pass
    
      
    if 'area' in data:
        area = data['area'].strip()
        try:  
            product.area = float(area) 
        except ValueError:
            pass

    if 'address' in data:
        address = data['address'].strip()
        product.address = address 
    
    if 'longitude' in data:
        longitude = data['longitude'].strip()
        product.longitude = longitude 

    if 'latitude' in data:
        latitude = data['latitude'].strip()
        product.latitude = latitude 
    
    if 'checkin_earlest_time' in data:
        checkin_earlest_time = data['checkin_earlest_time'].strip()
        product.checkin_earlest_time = checkin_earlest_time 
    
    if 'checkout_latest_time' in data:
        checkout_latest_time = data['checkout_latest_time'].strip()
        product.checkout_latest_time = checkout_latest_time
    
    if 'unsubscribe_rules' in data:
        unsubscribe_rules = data['unsubscribe_rules'].strip()
        product.unsubscribe_rules = unsubscribe_rules

    if 'checkin_notice' in data:
        checkin_notice = data['checkin_notice'].strip()
        product.checkin_notice = checkin_notice

    if 'customer_notice' in data:
        customer_notice = data['customer_notice'].strip()
        product.customer_notice = customer_notice
     
    if 'mainpic' in request.FILES:
        # 获取主图
        imagefile = request.FILES['mainpic']
        pre = datetime.now().strftime("%Y%m%d%H%M%S%f")
        file_name, file_extension = os.path.splitext(
            imagefile.name)
        filename = pre+file_extension
        FileUpload.upload(imagefile,
                            os.path.join('product', str(user.id)),
                            filename)
        filepath = os.path.join('product', str(user.id), filename  )
        if product.picture:
            # 删除旧的缩略图
            imgpath = os.path.join(settings.FILEPATH, product.picture )
            if os.path.isfile(imgpath): 
                os.remove(imgpath)
        product.picture = filepath
    
    if 'videopath' in request.FILES:
        # 获取视频路径
        imagefile = request.FILES['videopath']
        pre = datetime.now().strftime("%Y%m%d%H%M%S%f")
        file_name, file_extension = os.path.splitext(
            imagefile.name)
        filename = pre+file_extension
        FileUpload.upload(imagefile,
                            os.path.join('product', str(user.id)),
                            filename)
        filepath = os.path.join('product', str(user.id), filename  )
        if product.videopath:
            # 删除旧的 
            imgpath = os.path.join(settings.FILEPATH, product.videopath )
            if os.path.isfile(imgpath): 
                os.remove(imgpath)
        product.videopath = filepath
    
    if 'maxlivers' in data:
        maxlivers = data['maxlivers'].strip()
        try:  
            product.maxlivers = int(maxlivers) 
        except ValueError:
            pass

    if 'lighlight' in data:
        lighlight = data['lighlight'].strip()
        product.lighlight = lighlight 

    if 'housetype' in data:
        housetype = data['housetype'].strip()
        product.housetype = housetype
    
    if 'tags' in data: # 添加标签
        tags = data['tags'].split(",")
        label = "product"
        if product.tags:
            product.tags.all().delete()

        for tag in tags:
            if tag:
                product.tags.add(add(tag, label))
     
    return product

def addSpecs(product, data):
    if 'specifications' in data:
        """
        parms：price 商品单价
        parms：number 商品数量
        parms：name 商品名称
        parms：coin 商品虚拟币价格
        parms：content 商品说明
        specifications数据格式：
        [{"price":100.0, "number":100, "name":'大衣', "coin":100.0, "content":'保暖性能好'},
        {"price":120.0, "number":100, "name":'加绒大衣', "coin":200.0, "content":'保暖性能很好'},
        {"price":150.0, "number":100, "name":'貂皮大衣', "coin":300.0, "content":'保暖性能非常好'}]
        """
        product.product_specifications.all().delete()

        specifications = json.loads(data['specifications'])

        for specification in specifications:
            # 获取单价
            try:
                price = specification['price']
            except Exception:
                logger.error(traceback.format_exc())
                continue
            else:
                try:
                    price = float(price)
                except ValueError:
                    logger.error(traceback.format_exc())
                    continue
            
            # 获取数量
            try:
                number = specification['number']
            except Exception:
                logger.error(traceback.format_exc())
                continue
            else:
                try:
                    number = int(number)
                except ValueError:
                    logger.error(traceback.format_exc())
                    continue
            
            # 获取名称
            try:
                name = specification['name']
            except Exception:
                logger.error(traceback.format_exc())
                continue
            
            # 获取虚拟币单价
            try:
                coin = specification['coin']
            except Exception:
                logger.error(traceback.format_exc())
                continue
            else:
                try:
                    if coin is not None:
                        coin = float(coin) 
                    else:
                        coin = 0
                except ValueError:
                    logger.error(traceback.format_exc())
                    continue
            
            # 获取说明
            try:
                content = specification['content']
            except Exception:
                logger.error(traceback.format_exc())
                pass
                
            Specifications.objects.create(product = product,number = number, \
                name = name, price = price, coin = coin, content = content)


 

def setHomestayPrice(product, pricemode):
    # 设置民宿的价格, 如果product不是民宿，则会直接跳过 
    product = Product.objects.get(uuid = product.uuid)
    if product.producttype == 0 :# 民宿
        if product.holiday_price is None and product.weekday_price is None and product.workday_price is None :
            # 没有设置价格，直接返回
            print('23333')
            return
        print('product')
        today = datetime.now().date()
        finalday = today + relativedelta(months = 6)
        # 只设置最近6个月的房价
        days = finalday - today
        holidays = get_holidays() # 获取节假日信息
        if pricemode == 0:# 仅覆盖日历上未设定价格的日期
            specs = Specifications.objects.filter(product = product, date__gte = today)
            for i in range(days.days + 1):
                day = today + timedelta( days=i)
                count = Specifications.objects.filter(product = product, date = day).count()
                if count > 1: # 有重复的，删除重复的，重新设置
                    Specifications.objects.filter(product = product, date = day).delete()
                elif count == 1: # 已经设置过价格了，直接跳过
                    continue
                else: 
                    # 之前没有设置价格
                    pass
                
                create_spec = {
                    "product" :product,
                    "date" : day,
                    "number" : 1,
                    "content" : str(day.day),
                    "purchase_way" : Specifications.CASH
                } 
                holiday = check_holiday(day, holidays) 
                if holiday != "":
                    # 是节假日,节假日价格没有设置就用周末价，周末价也没有设置就用日常价
                    if product.holiday_price:
                        create_spec['price'] = product.holiday_price
                    elif product.weekday_price:
                        create_spec['price'] = product.weekday_price
                    elif product.workday_price:
                        create_spec['price'] = product.workday_price
 
                elif day.weekday() == 6 or day.weekday() == 5:
                    # 周末
                    if product.weekday_price:
                        create_spec['price'] = product.weekday_price
                    elif product.workday_price:
                        create_spec['price'] = product.workday_price
                elif product.workday_price:
                    create_spec['price'] = product.workday_price
                

                if 'price' in create_spec:
                   Specifications.objects.create(**create_spec) 
                else:
                    print("no price")
  
        else: # 覆盖日历所有价格
            # 先删除原来所有的
            Specifications.objects.filter(product = product, date__gte = today).delete() 

            for i in range(days.days + 1):
                day = today + timedelta( days=i)
                 
                create_spec = {
                    "product" :product,
                    "date" : day,
                    "number" : 1,
                    "content" : str(day.day),
                    "purchase_way" : Specifications.CASH
                } 
                holiday = check_holiday(day, holidays) 
                if holiday != "":
                    # 是节假日,节假日价格没有设置就用周末价，周末价也没有设置就用日常价
                    if product.holiday_price:
                        create_spec['price'] = product.holiday_price
                    elif product.weekday_price:
                        create_spec['price'] = product.weekday_price
                    elif product.workday_price:
                        create_spec['price'] = product.workday_price
 
                elif day.weekday() == 6 or day.weekday() == 5:
                    # 周末
                    if product.weekday_price:
                        create_spec['price'] = product.weekday_price
                    elif product.workday_price:
                        create_spec['price'] = product.workday_price
                elif product.workday_price:
                    create_spec['price'] = product.workday_price
                

                if 'price' in create_spec:
                   Specifications.objects.create(**create_spec) 
                else:
                    print("no price2")




def specifications_infos_lst(specs):
    # 获取商品规格详情
    specifications_infos = []
    for spec in specs:
        spec_dct = {}
        id = spec.id
        # 商品价格
        price = str(spec.price)
        # 商品数量
        num = spec.number
        # 虚拟币数量
        coin = str(spec.coin)
        # 商品名称
        name = spec.name
        # 商品规格名称
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
        if spec.date:
            spec_dct['date'] = time.mktime(spec.date.timetuple())
        specifications_infos.append(spec_dct)
    return specifications_infos

def product_infos_lst(products):
    # 获取商品详情
    product_infos = []
    
    for product in products: 
        product_infos.append(get_single_product(product))
    return product_infos


def homestay_infos_lst(products, date=None,  detail=False, admin = False):
    # 获取民宿详情
    product_infos = []
    
    for product in products: 
        product_infos.append(get_single_homestay_product(product,  date ,  detail , admin ))
    return product_infos


def get_single_homestay_product(product, date=None,  detail=False, admin = False):
    # admin = True,返回管理信息，= False，只返回客户所需看到的信息
    # detail 指的是详细页面中需要的数据
    # date 指的是date这一天的价格，如果为None则默认今天
     
    # 商品轮播图
    if product.turns:
        turns = product.turns.split(',')
    else:
        turns = ''
     
    product_dict = { 
        "uuid":product.uuid,
        "title":product.title, 
        "content":product.content,
        "picture":product.picture,
        "turns":turns,
        "videopath" : product.videopath,
        "isbook" : product.isbook,
        "producttype" : product.producttype,
        "cardtype" : product.cardtype,
        "ready" : product.ready,
        "recommend" : product.recommend, 
        "producttype" : product.producttype, 
        "categoryid":product.category.id, 

        "longitude" : product.longitude, 
        "latitude" : product.latitude, 
        "area" : product.area, 
        "address" : product.address, 

        "lighlight" : product.lighlight, 
        "housetype" : product.housetype, 
        "maxlivers" : product.maxlivers,
        "tags" : list(product.tags.all().values("id", "name")),
    }

    if date is None:
        # 获取今天的价格
        date = datetime.today().date()
    
    if detail:
        # 获取详细的
        specifications = product.product_specifications.all().values("id","date", "price", "number")
        product_dict['checkin_earlest_time'] =  product.checkin_earlest_time
        product_dict['checkout_latest_time'] =  product.checkout_latest_time

        product_dict['unsubscribe_rules'] =  product.unsubscribe_rules
        product_dict['checkin_notice'] =  product.checkin_notice
        product_dict['customer_notice'] =  product.customer_notice 

        # 每个图库，获取最前面的一张图，其他图通过图库接口获取 
        imgs = list(ProductImages.objects.filter(imgtype__product = product).\
            values("id", "img", "imgtype__id", "imgtype__name").\
                distinct("imgtype__id").order_by("imgtype__id", "id")) 
        product_dict['imgs'] =  imgs
    else:
        # 获取指定日期的
        specifications = list(product.product_specifications.filter(date = date).values("id","date", "price", "number"))
    for spec in specifications:
        spec['date'] = time.mktime(spec['date'].timetuple())
        spec['price'] = str(spec['price'] )

    product_dict['specifications']  = list(specifications)

    if admin:
        # 管理端获取详细的
        product_dict['workday_price'] =  product.workday_price
        product_dict['weekday_price'] =  product.weekday_price
        product_dict['holiday_price'] =  product.holiday_price

 
    return product_dict



def get_single_product(product): 
    specifications_lst = []
    product_creator_dct = {}
    product_creator_dct['userid'] = product.user.id
    product_creator_dct['username'] = product.user.username
    product_id = product.id
    # 商品内容描述
    content = product.content
    # 商品图片
    picture = product.picture
    # 商品轮播图
    if product.turns:
        turns = product.turns.split(',')
    else:
        turns = ''
    # 商品标题
    title = product.title
    # 商品类别
    if product.category:
        category = product.category.name
    else:
        category = ""
    # 商品规格
    specifications = product.product_specifications.all()
    specifications_lst = specifications_infos_lst(specifications)
    purchase_way = back_sing_goods_way(product.id)
    
    tag_list = [(tag.id, tag.name, tag.label) for tag in product.tags.all()]
    product_dict = {
        "id":product_id,
        "uuid":product.uuid,
        "creator_info":product_creator_dct,
        "content":content,
        "picture":picture,
        "turns":turns,
        "title":title,
        "isbook" : product.isbook,
        "producttype" : product.producttype,
        "cardtype" : product.cardtype,
        "ready" : product.ready,
        "recommend" : product.recommend,
        "tags" : tag_list,
        "category":category,
        "producttype" : product.producttype,
        "videopath" : product.videopath,
        "categoryid":product.category.id,
        "specifications":specifications_lst,
        "purchase_way":purchase_way
    }

    return product_dict

def update_bill_closed(bills):
    # 将订单的状态更新为关闭
    for bill in bills:
        # 获取现在时间
        now = timeStamp(datetime.now())
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
    # 商品信息
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

