#! -*- coding:utf-8 -*- 
from django.db import models
from appuser.models import AdaptorUser as User
from basedatas.models import BaseDate  

class WebCoin(BaseDate):
    """
    积分表
    积分不是全平台通用的，是跟某个小区绑定的，表示在某个小区获得的积分。
    """
    user = models.ForeignKey(User, related_name="coin_owner", on_delete=models.PROTECT)
    
    # 实体类别 
    PROPERTY_MGE_FEE = 0 # 物业管理费 
    entity = models.SmallIntegerField(default=PROPERTY_MGE_FEE)
    # 存放对应实体类别下的实体uuid
    instanceuuid = models.CharField(max_length=64)
    # 积分变动情况，若增加50则为+50，减少50为-50
    action = models.IntegerField(default=0)
    # 变动理由
    reason = models.CharField(max_length=200)

    class Meta:
        default_permissions = ()
        ordering = ['-date']
 
class InviteCode(models.Model):
    """
    邀请码
    """
    # 邀请人
    user = models.ForeignKey(User, related_name='invite_user',
                                on_delete=models.PROTECT)
    # 邀请码
    code = models.CharField(max_length=20)
    class Meta:
        default_permissions = ()

 