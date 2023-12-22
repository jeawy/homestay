#! -*- coding: utf-8 -*-
from django.db import models

from basedatas.models import BaseDate
from appuser.models import AdaptorUser as User
from address.models import Address
from category.models import Category
from tags.models import Tags 
from django.conf import settings
import os
from coupon.models import Coupon


class Product(BaseDate):
    
    """
    商品表：特产、民宿、外卖
    """
 
    uuid = models.CharField(max_length= 64, unique=True) # UUID
    # 商品创建人
    user = models.ForeignKey(User, on_delete=models.CASCADE )
    # 商品图片封面图
    picture = models.CharField(max_length=200,null=True)

    # 视频路径 
    videopath = models.CharField(max_length=256, null=True)
    
    # 优惠券
    coupon = models.ForeignKey(Coupon, null=True, on_delete=models.SET_NULL)

    
    # 内容描述
    content = models.TextField(null=True)
    # 轮播图
    turns = models.TextField(null=True) # 分号隔开
    # 商品标题
    title = models.CharField(max_length=200,null=False)
    
    # 商品类别：0 表示民宿，1景区门票 2租车 10 表示其他
    producttype = models.PositiveSmallIntegerField(default= 0)
    
    # 评分
    rate = models.FloatField(default=5.0)

    # 商品分类
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,null= True )

    tags = models.ManyToManyField(Tags) # 标签

    # 是否为预约商品，默认为现货商品，1 为预约商品
    isbook = models.SmallIntegerField(default=0)
    
    # 上架 1 与下架0
    ready = models.SmallIntegerField(default=0)

    # 推荐 1 与未推荐0，推荐会上首页
    recommend = models.SmallIntegerField(default=0)

    # 商品类型，0表示实物，1表示商品卡、购物卡
    gifttype = models.PositiveSmallIntegerField(default = 0)

    # 购物卡类型：0 电子购物卡，1 实体购物卡
    cardtype = models.PositiveSmallIntegerField(default = 0)
    

    longitude = models.CharField(max_length=128, null=True)
    latitude = models.CharField(max_length=128, null=True)

    

    # 以下是民宿价格及民宿的其他属性设置
    # 工作日价格
    workday_price = models.FloatField(null = True ) 
    # 周末价格
    weekday_price = models.FloatField(null = True  ) 
    # 节假日价格
    holiday_price = models.FloatField( null = True ) 
    
    # 面积
    area = models.FloatField(null= True)
    
    # 地址
    address = models.CharField(max_length=200,null=True)
    
    # 最早入住时间
    checkin_earlest_time = models.CharField(max_length=50,null = True)
    # 最晚退房时间
    checkout_latest_time = models.CharField(max_length=50, null = True)
    
    # 退订规则
    unsubscribe_rules = models.TextField( null= True)
    # 入住须知
    checkin_notice = models.TextField( null= True)
    # 对客要求
    customer_notice = models.TextField( null= True)
    
    # 特色，特点
    lighlight = models.CharField(max_length= 100, null= True)
    # 户型: 两室一厅
    housetype = models.CharField(max_length= 100, null= True)
    
    # 最大允许入住人数
    maxlivers = models.PositiveSmallIntegerField(default=4)
    class Meta:
        default_permissions = ()
        ordering = ['-date']



class ProductImageQuerySet(models.QuerySet):
    def delete(self, *args, **kwargs):  
        print(self)
        for obj in self:
            print(obj)
            if obj.img:
                path = os.path.join(settings.FILEPATH, obj.img)  
                if os.path.isfile(path):
                    os.remove(path)
            if obj.share_img:
                path = os.path.join(settings.FILEPATH, obj.share_img)  
                if os.path.isfile(path):
                    os.remove(path)

            obj.delete()


class ProductImagesType(models.Model):
    # 商品中的图片，例如: 卧室图片
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    name = models.CharField(max_length=20 ) 
    # 排序
    sort = models.PositiveSmallIntegerField(default= 1)
    class Meta:
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(fields = ['product', 'name'], 
            name = "productimg_type_unique")
        ]
        ordering = ['sort']


class ProductImages(models.Model):
    # 商品中的图片，例如: 卧室图片 
    img = models.CharField(max_length=200 )
    imgtype = models.ForeignKey(ProductImagesType, on_delete=models.CASCADE)
    
    objects = ProductImageQuerySet.as_manager()


    class Meta:
        default_permissions = ()
        ordering = ['-id']



class Specifications(models.Model):
    """商品规格表"""

    # 商品库存
    number = models.IntegerField(default=1)
    # 商品名称
    name = models.CharField(max_length=200,null=True) #  民宿用date字段，非民宿用这个字段
    #  民宿用date字段 
    date = models.DateField(null= True)  # 注意 一天不能有两个价格
    # 商品单价
    price = models.DecimalField(max_digits=8, decimal_places=2,null=True,default=None)
    # 虚拟币数量
    coin = models.IntegerField(null=True,default=None)
    # 商品规格描述
    content = models.CharField(max_length=1024,null=True)
    # 商品外键
    product = models.ForeignKey(Product, on_delete=models.CASCADE, 
                                related_name='product_specifications' )
    # 已经兑换的数量 = 积分兑换 +积分加现金 + 资格兑换的数量
    conversion_num = models.IntegerField(null=True,default=0)
    # 交易量  = 现金购买 + 积分兑换 +积分加现金 + 资格兑换的数量
    business_num = models.IntegerField(null=True,default=0)
    # 购买方式 "1,2,3,4"
    COIN = 1  # 1:支持积分
    CASH = 2  # 2:支持现金
    CASH_AND_COIN = 3  # 3:支持现金+积分 
    purchase_way = models.SmallIntegerField(default=COIN)
     

    def purchase_way_list(self):
        return [Specifications.COIN, Specifications.CASH,
                Specifications.CASH_AND_COIN ]
    class Meta:
        default_permissions = ()
 



class ExtraItems(models.Model):
    """
    额外附加到商品或民宿中的收费内容：
    比如民宿的接送机服务，
    """ 
    # 商品名称
    name = models.CharField(max_length=200 ) #  民宿用date字段，非民宿用这个字段
     
    # 商品单价
    price = models.FloatField(default=0 )
  
    # 商品规格描述
    remark = models.CharField(max_length=1024,null=True)
    # 商品外键
    product = models.ForeignKey(Product, on_delete=models.CASCADE, 
                                related_name='extra_products' )
     
    class Meta:
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(fields = ['name', 'product' ], 
            name = "extra_items_unique")
        ]
 

class Bill(BaseDate):
    """订单表"""

    # 商品规格的id
    specifications = models.ForeignKey(Specifications, on_delete=models.DO_NOTHING,
                            null=True,default=None)
    # 购买的数量
    number = models.IntegerField()
    # 付款方式,订单支付后更新这个字段
    purchase_way = models.IntegerField(null=True,default=None)

    # 支付积分
    coin = models.IntegerField(null=True,default=None)
    # 支付金额
    money = models.DecimalField(max_digits=8, decimal_places=2,null=True,default=None)
    # # 支付金额+积分
    coin_money = models.CharField(null=True,default=None,max_length=128)
    # # 支付资格

    # 订单创建人
    user = models.ForeignKey(User,  on_delete=models.PROTECT)
    # 收货地址
    address = models.ForeignKey(Address , on_delete=models.PROTECT)
    # 快递单号
    express_number = models.CharField(max_length=1024, null=True)
    # 快递公司
    express_company = models.CharField(max_length=128, null=True)
    # 订单号
    order_number = models.CharField(max_length=1024, null=True)
    # 订单状态
    # 未支付
    NON_PAYMENT = 0
    # 未发货
    WAIT_DELIVERY = 1
    # 待收货
    DELIVERING = 2
    # 已完成
    ACCOMPLISH = 3
    # 已关闭
    CLOSED = 4
    status = models.SmallIntegerField(default=NON_PAYMENT)

    class Meta:
        default_permissions = ()
        ordering = ['-date']

    def get_status_list(self):
        return [Bill.NON_PAYMENT,Bill.WAIT_DELIVERY,Bill.DELIVERING,Bill.ACCOMPLISH,Bill.CLOSED]

class PurchaseWay(models.Model):
    '''商品的购买方式表'''

    # 商品id外键
    goods = models.OneToOneField(Product, on_delete=models.CASCADE )
    # 购买方式 "1,2,3,4"
    COIN = 1   # 1:支持积分
    CASH = 2    # 2:支持现金
    CASH_AND_COIN = 3  # 3:支持现金+积分 
    purchase_way = models.CharField(max_length=128)
    # 积分
    coin = models.IntegerField(null=True,default=None)
    # 现金
    cash = models.FloatField(null=True,default=None)
    # 积分+现金
    coin_cash = models.CharField(max_length=128,null=True,default=None)
    
    qualification_id = models.IntegerField(null=True,default=None)

    def purchase_way_list(self):
        return [str(PurchaseWay.COIN),str(PurchaseWay.CASH),str(PurchaseWay.CASH_AND_COIN) 
               ]
    class Meta:
        default_permissions = ()

