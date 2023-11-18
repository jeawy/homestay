from statistics import mode
from django.db import models
from basedatas.models import BaseDate
from appuser.models import AdaptorUser as User
from organize.models import   Organize 
from building.models import Room
from community.models import Community
from property.code import ZHIFUBAO, WEIXIN


class Msg(BaseDate):
    """短信套餐表"""

    # 创建人
    user = models.ForeignKey(User, on_delete=models.CASCADE )
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
    DRAFT = 0 
    PUBLISHED = 1
    # 商品状态
    status = models.PositiveSmallIntegerField(default = PUBLISHED)

    class Meta:
        default_permissions = ()
        ordering = ['-date'] 

class MsgSpecifications(models.Model):
    """规格表"""

    # 数量
    number = models.IntegerField()
    # 名称
    name = models.CharField(max_length=200,null=False)
    # 单价
    price = models.DecimalField(max_digits=8, decimal_places=2,null=True,default=None)
     
    # 外键
    product = models.ForeignKey(Msg, on_delete=models.CASCADE, related_name='msg_specifications')
      
    class Meta:
        default_permissions = ()


class MsgOrders(BaseDate):
    """
    物业的短信充值记录
    充值记录不允许删除
    """ 
    # 标题
    subject = models.CharField(max_length=128)
    org = models.ForeignKey(Organize, on_delete=models.PROTECT)
    # 短信的充值记录与小区是挂钩的
    community = models.ForeignKey(Community, on_delete=models.PROTECT)
    # 订单号
    billno = models.CharField(max_length = 64, unique=True)
    # 短信充值的总条数
    total = models.PositiveIntegerField(default = 0)
    # 购买数量
    number = models.PositiveIntegerField(default=1)
    # 总金额
    money = models.FloatField(default=0) 

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    # 支付方式 
    payway = models.PositiveSmallIntegerField(default= ZHIFUBAO)
    # 支付宝或者微信的订单号
    paybillno = models.CharField(max_length = 256, null = True)
    # 支付宝或者微信购买者账户 
    buyer = models.CharField(max_length=128 , null = True)
    # 支付金额，支付金额应该要与money相同
    payedmoney = models.FloatField(null = True)
    # 实收金额，单位为元，两位小数。该金额为本笔交易，商户账户能够实际收到的金额
    receipt_amount = models.FloatField(null = True)
    # 对应规格
    spc = models.ForeignKey(MsgSpecifications, on_delete=models.SET_NULL, null=True)
     # 未支付
    NON_PAYMENT = 0 
    # 已支付
    PAYED = 2 
    CLOSED = 3 # 已关闭
    status = models.SmallIntegerField(default=NON_PAYMENT)
    
    class Meta:
        ordering = ['-date'] 
        default_permissions = () 
 

class MsgSendRecord(BaseDate):
    """
    物业的短信发送记录
    """
    # 操作者
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    # 短信来自哪个订单
    order = models.ForeignKey(MsgOrders, on_delete=models.CASCADE, null = True)
    # 哪个物业发的
    org = models.ForeignKey(Organize, on_delete=models.CASCADE, null = True)
    # 短信在哪个社区
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    # 短信接收人号码
    phone = models.CharField(max_length = 11) 
    # 关联的房屋
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null = True)
    # 短信内容
    message = models.CharField(max_length = 256)
    # 当批量发送短信条数较多的时候，设置status为not sent，
    # 将来异步发送，确保发送成功
    SENT = 0 # 已发送 
    NOTSENT = 1 # 未发送
    MSG = 2 # 短信余额不足，未发送
    status = models.SmallIntegerField(default=SENT) 
    # 短信类型
    FEE = 0 # 缴费提醒类型
    msgtype = models.PositiveSmallIntegerField(default = FEE) 
    
    # 发送短信的参数，延时发送时，需要将参数存入这个字段
    params = models.TextField(null = True)
 
    class Meta: 
        default_permissions = () 
