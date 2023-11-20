from statistics import mode
from django.db import models
from basedatas.models import PayBase
from appuser.models import AdaptorUser as User
from product.models import Specifications
from address.models import Address
from card.models import Card


class Bills(PayBase):
    """
    订单表
    """ 
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    EBILL = 0 # 电子订单
    REALBILL = 1 # 实物订单
    ebill = models.SmallIntegerField(default = REALBILL)

    # 订单类型，积分还是现金
    COIN = 0 #  当类型为积分的时候，money中存储的就是积分数量
    MONEY = 1 #  
    ordertype = models.PositiveSmallIntegerField(default= MONEY )
     
    # 未支付
    NON_PAYMENT = 0
    # 已支付
    PAYED = 2
    DELIVERIED = 3 # 已发货
    FINISHED = 4 # 已签收
    REFUND = 5 #  已退款
    NOTENOUGH = 6 #  库存不足
    UNUSUAL = -1  # 异常订单，例如库存不足等
    status = models.SmallIntegerField(default = UNUSUAL)
    
    # 备注信息
    remark = models.CharField(max_length= 256, null = True)

    # 快递物流信息
    delivery= models.TextField(null=True)
    # 本人是否已删除
    owner_delete = models.SmallIntegerField(default=0)
    # 平台是否已删除
    platform_delete = models.SmallIntegerField(default=0)
    
    # 收货地址 信息：
    # 收货人
    receiver = models.CharField(max_length= 256, null=True)
    # 收货电话
    receiver_phone = models.CharField(max_length= 16, null=True)
    # 收货详细地址
    receiver_address = models.CharField(max_length= 1024, null=True)

    # 快递单号
    express_number = models.CharField(max_length=1024, null=True)
    # 快递公司
    express_company = models.CharField(max_length=128, null=True)
 
    # 配送方式，0 快递，1 自提
    delivery_way = models.PositiveSmallIntegerField(default=0)

    
    class Meta:
        ordering = ['-date']
        default_permissions = () 


class BillSpec(models.Model):
    """订单商品表：一个订单里可以有多个商品"""

    # 数量
    number = models.IntegerField()
    # 名称
    name = models.CharField(max_length=200,null=False)
    # 图片
    picture = models.CharField(max_length=200,null=True)
    # 标题
    title = models.CharField( null=True,max_length=200,)
    # 单价
    price = models.FloatField( null=True,default=None)
    
    # 规格描述
    content = models.CharField(max_length=1024,null=False)
    # 外键
    bill = models.ForeignKey(Bills, on_delete=models.CASCADE  )

    spec = models.ForeignKey(Specifications, on_delete=models.SET_NULL, related_name='bill_specifications', null=True )
     
    # 商品总金额
    money = models.FloatField(default=9999999.99)   

    # 购买的是购物卡的话，这个字段保存的是购物卡
    card = models.ForeignKey(Card, on_delete=models.PROTECT, null = True, unique=True)

    def purchase_way_list(self):
        return [Specifications.COIN, Specifications.CASH,
                Specifications.CASH_AND_COIN ]
    class Meta: 
        ordering = ['-id']
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(fields = ['spec', 'card'],
            name = "bill_card_unique")
         ]



class PayCards(models.Model):
    """
    购物卡支付表:支持一个订单中使用多个购物卡进行支付
    """  
    # 外键
    bill = models.ForeignKey(Bills, on_delete=models.CASCADE  )

    card = models.ForeignKey(Card, on_delete=models.PROTECT, related_name='bill_card')
     
    # 支付金额
    money = models.FloatField(default=9999999.99)    

     
    class Meta:
        default_permissions = ()