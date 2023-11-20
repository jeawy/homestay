#! -*- coding: utf-8 -*-
from django.db import models

from basedatas.models import BaseDate
from appuser.models import AdaptorUser as User
from address.models import Address
from category.models import Category
from tags.models import Tags 
from django.conf import settings
import os


class Product(BaseDate):
    
    """商品表：特产、民宿、外卖"""
 
    uuid = models.CharField(max_length= 64, unique=True) # UUID
    # 礼品创建人
    user = models.ForeignKey(User, on_delete=models.CASCADE )
    # 礼品图片
    picture = models.CharField(max_length=200,null=True)
    # 内容描述
    content = models.TextField(null=True)
    # 轮播图
    turns = models.TextField(null=True)
    # 礼品标题
    title = models.CharField(max_length=200,null=False)
    # 礼品类别
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING,null= True )

    tags = models.ManyToManyField(Tags)

    # 是否为预约商品，默认为现货商品，1 为预约商品
    isbook = models.SmallIntegerField(default=0)
    
    # 上架 1 与下架0
    ready = models.SmallIntegerField(default=0)

    # 推荐 1 与未推荐0，推荐会上首页
    recommend = models.SmallIntegerField(default=0)

    # 商品类型，0表示实物，1表示礼品卡、购物卡
    gifttype = models.PositiveSmallIntegerField(default = 0)

    # 购物卡类型：0 电子购物卡，1 实体购物卡
    cardtype = models.PositiveSmallIntegerField(default = 0)

    class Meta:
        default_permissions = ()
        ordering = ['-date']
 
class Specifications(models.Model):
    """礼品规格表"""

    # 礼品库存
    number = models.IntegerField()
    # 礼品名称
    name = models.CharField(max_length=200,null=False)
    # 礼品单价
    price = models.DecimalField(max_digits=8, decimal_places=2,null=True,default=None)
    # 虚拟币数量
    coin = models.IntegerField(null=True,default=None)
    # 礼品规格描述
    content = models.CharField(max_length=1024,null=False)
    # 礼品外键
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gift_specifications', null=True)
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
 

class Bill(BaseDate):
    """订单表"""

    # 礼品规格的id
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

