from django.db import models
from basedatas.models import BaseDate
from appuser.models import AdaptorUser as User
from common.logutils import ModuleLogger

class Card(BaseDate):
    # 购物卡
    uuid = models.CharField(max_length= 64, unique=True)
    # 购物卡的类型
    VIRTUAL = 0 # 虚拟卡
    REAL = 1 # 实体卡
    cardtype = models.PositiveSmallIntegerField(default=VIRTUAL)
    
    # 购物卡金额
    money = models.PositiveIntegerField()
    # 购物卡剩余金额：每次下单的时候，减该数据
    left = models.FloatField(default= 0 )
    
    # 卡密
    password = models.CharField(max_length=12, unique=True)
    
    # 未售出
    UNSALLED = 0  
    # 待绑定
    SALLED = 1  # 
    # 已绑定，待激活
    BIND = 2 
    # 已激活
    ACTIVATED = 3 # 只有激活之后才是可用的
    status = models.PositiveSmallIntegerField(default = UNSALLED)
    
    # 购物卡绑定的用户
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
 
    # 是谁激活的
    manager = models.ForeignKey(User, related_name="card_manager", on_delete=models.PROTECT, null=True)
    # 激活日期
    activedate = models.DateTimeField(null=True)
    # 出售日期
    saledate = models.DateTimeField(null=True)

    class META:
        default_permissions = ()
        permissions = [('can_activate_card', '激活购物卡的权限')]
