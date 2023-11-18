from django.db import models 
from appuser.models import AdaptorUser as User 
from community.models import Community
from basedatas.models import BaseDate, PayBase
from property.code import ZHIFUBAO, WEIXIN


class PaidService(BaseDate):
    """
    内容登记主表
    """
    uuid = models.CharField(max_length= 64, unique=True) # UUID
    # 服务类别：固定几类：五金类、厨卫类、电器类、供排水、上门服务、其他
    # 服务类别固定方便APP端UI设计
    # 
    WUJIN = 0 # 五金类
    CHUWEI = 1 # 厨卫类
    DIANQI = 2 # 电器类
    SHUI = 3 # 供排水
    SHANGMEN = 4 # 上门服务
    QITA = 5 # 其他
    category = models.PositiveSmallIntegerField(default = WUJIN)
    # 哪个社区的有偿服务
    community = models.ForeignKey(Community, on_delete=models.PROTECT)
    # 服务标题
    title = models.CharField(max_length=64)
    # 服务内容
    content = models.TextField(null = True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # 金额：一口价
    money = models.FloatField()
    # 单位：如，次、个
    unit = models.CharField(max_length= 10)
 
    DRAFT = 0 # 草稿
    PUBLISHED = 1 # 已发布 
    status = models.PositiveSmallIntegerField(default = PUBLISHED)
     
    def get_category_ls(self):
        return [self.WUJIN,self.CHUWEI,self.DIANQI,self.SHUI,self.SHANGMEN,self.QITA]

    class Meta:
        ordering = ['-date']
        default_permissions = ()
        permissions = [
            ("manage_paidservice", "发布、修改、删除有偿服务权限")
        ]

 
class PaidOrder(PayBase):
    """
    有偿服务订单
    超过1天未支付的订单会被自动删除
    """ 
    # 当服务删除之后，可以用community来查询
    community = models.ForeignKey(Community, on_delete=models.PROTECT) 
     
    # 支付时的服务单价
    servicenprice = models.CharField(max_length=128, null= True)
    # 支付时的服务单位
    servicenunit = models.CharField(max_length=128, null= True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
      
     
    # 如果订单是批量支付的，那么这个字段存储的是提交给支付宝或者微信的订单号billno
    # 如果订单是一条一条支付的，那么这个字段与billno一致
    out_trade_no = models.CharField(max_length = 64, null=True)
     
    # 购买数量
    number = models.PositiveIntegerField(default=1)
     
    # 用户评分
    score = models.PositiveSmallIntegerField(default = 0)
      
     # 未支付
    NON_PAYMENT = 0 
    # 已支付
    PAYED = 2 
    CLOSED = 3 # 已完成
    UNUSUAL = 4 # 异常订单：如支付金额与订单金额不符
    status = models.SmallIntegerField(default=NON_PAYMENT)
    # 订单备注，如：支付金额与订单金额不符
    remark = models.CharField(max_length=128, null = True)
    
    class Meta:
        ordering = ['-date'] 
        default_permissions = ()
        