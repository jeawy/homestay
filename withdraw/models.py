from django.db import models
from basedatas.models import BaseDate
from appuser.models import AdaptorUser as User 
from property.code import ZHIFUBAO, WEIXIN
import os
from django.conf import settings
from community.models import Community


class WithDraw(BaseDate):
    """
    提现记录
    """
    uuid = models.CharField(max_length= 64, unique=True) # UUID
    # 提现申请人
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    # 申请提现的小区，这个字段为空时，表示是业主申请的，
    # 如果是物业申请，则该字段必须填
    community = models.ForeignKey(Community,null=True, on_delete=models.PROTECT)

    # 提现金额
    money = models.FloatField()
    # 支付时间
    payed_date = models.DateTimeField(null=True)
    APPLY = 0 # 已申请
    PAYED = 1 # 已支付
    REJECTED = 2 # 已拒绝
    status = models.PositiveSmallIntegerField(default = APPLY)
    
    # 备注
    remark = models.TextField(null=True)
    # 支付订单号
    payed_billno = models.CharField(max_length = 56, null = True)
    # 支付宝、微信或者银行转账
    payway = models.PositiveSmallIntegerField(null = True)
    
    class Meta:
        ordering = ['-date']
        default_permissions = ()
        # 仅平台用户的管理权限,以platform_开头的权限为平台权限
        permissions = [
            ("platform_manage_withdraw", "提现管理")
        ]

class ImageQuerySet(models.QuerySet):
    def delete(self, *args, **kwargs):  
        for obj in self:
            path = os.path.join(settings.FILEPATH, obj.filepath)  
            if os.path.isfile(path):
                os.remove(path)
            obj.delete()
             

class WithdrawImgs(models.Model):
    """
    支付凭证表
    """ 
    # 用来保存任务主表或工作流主表的id
    withdraw = models.ForeignKey(WithDraw, related_name='feedback', on_delete=models.CASCADE ) 
    # 附件名称
    filename = models.CharField(max_length=128)
    # 附件地址
    filepath = models.CharField(max_length=1024) 
    objects = ImageQuerySet.as_manager() 
    class Meta: 
        default_permissions = () 