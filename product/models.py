#! -*- coding: utf-8 -*-
from django.db import models

from basedatas.models import BaseDate
from appuser.models import AdaptorUser as User
from address.models import Address
from category.models import Category
from tags.models import Tags
from community.models import Community


class Product(BaseDate):
    """信息、公告、通知、社区见闻、内部内容表"""

    # 创建人
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="product_creator")
    # 图片
    picture = models.CharField(max_length=200,null=True)
    # 内容描述
    content = models.TextField(null=True)
    # 轮播图
    turns = models.TextField(null=True)
    uuid = models.CharField(max_length= 64, unique=True) # UUID
    # 详细内容
    detail = models.TextField(null=True) 
    # 标题
    title = models.CharField(max_length=200,null=False)
    INFORMATION = 0 # 百事通
    NOTIFICATION = 1 # 通知
    ANNOUNCEMENT = 2 # 公告 
    NEWS = 3 # 社区见闻，为了增加社区见闻的美观性，picture字段为必填
    INNER = 4 #内部文章，不在app中显示，或者只能通过app的活动页面点击进入的
    product_type = models.PositiveSmallIntegerField(default = INFORMATION)
    # 类别
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING,null= True, related_name="cat_product")
     
    tags = models.ManyToManyField(Tags)
    DRAFT = 0 
    PUBLISHED = 1
    # 商品状态
    status = models.PositiveSmallIntegerField(default = PUBLISHED) 
    YES = 1
    NO = 0 
    # 是否允许评论, 默认不开启评论
    allow_comment = models.PositiveSmallIntegerField(default = NO)
    
    class Meta:
        default_permissions = ()
        ordering = ['-date']
        permissions = [("manage_product", "发布、编辑：信息薄、公告通知等")]

class Specifications(models.Model):
    """规格表"""

    # 库存
    number = models.IntegerField()
    # 名称
    name = models.CharField(max_length=200,null=False)
    # 单价
    price = models.DecimalField(max_digits=8, decimal_places=2,null=True,default=None)
    # 积分数量
    coin = models.IntegerField(null=True,default=None)
    # 规格描述
    content = models.CharField(max_length=1024,null=False)
    # 外键
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='pro_specifications',null=True)
    # 已经兑换的数量 = 积分兑换 +积分加现金 + 资格兑换的数量
    conversion_num = models.IntegerField(null=True,default=0)
    # 交易量  = 现金购买 + 积分兑换 +积分加现金 + 资格兑换的数量
    business_num = models.IntegerField(null=True,default=0)
    # 购买方式 "1,2,3,4"
    COIN = 1  # 1:支持积分
    CASH = 2  # 2:支持现金
    CASH_AND_COIN = 3  # 3:支持现金+积分
    QUALIFICATION = 4  # 4:支持资格
    purchase_way = models.SmallIntegerField(default=COIN)

    def purchase_way_list(self):
        return [Specifications.COIN, Specifications.CASH,
                Specifications.CASH_AND_COIN, Specifications.QUALIFICATION]
    class Meta:
        default_permissions = ()
 
class Bill(BaseDate):
    """订单表"""

    # 规格的id
    specifications = models.ForeignKey(Specifications, on_delete=models.DO_NOTHING,
                            related_name='BILL_specifications',null=True,default=None)
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
    user = models.ForeignKey(User, related_name="bill_user", on_delete=models.PROTECT)
    # 收货地址
    address = models.ForeignKey(Address, related_name="address_user", on_delete=models.PROTECT)
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
    goods = models.OneToOneField(Product, on_delete=models.CASCADE,
                              related_name="goods_id")
    # 购买方式 "1,2,3,4"
    COIN = 1   # 1:支持积分
    CASH = 2    # 2:支持现金
    CASH_AND_COIN = 3  # 3:支持现金+积分
    QUALIFICATION = 4  # 4:支持资格
    purchase_way = models.CharField(max_length=128)
    # 积分
    coin = models.IntegerField(null=True,default=None)
    # 现金
    cash = models.FloatField(null=True,default=None)
    # 积分+现金
    coin_cash = models.CharField(max_length=128,null=True,default=None)
    # 资格兑换
    # qualification = models.ForeignKey(QualificationRule,on_delete=models.CASCADE,
    #                         related_name='way_qualification',null=True,default=None)
    qualification_id = models.IntegerField(null=True,default=None)

    def purchase_way_list(self):
        return [str(PurchaseWay.COIN),str(PurchaseWay.CASH),str(PurchaseWay.CASH_AND_COIN),
                str(PurchaseWay.QUALIFICATION)]
    class Meta:
        default_permissions = ()
