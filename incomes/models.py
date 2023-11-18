from django.db import models 
from basedatas.models import BaseDate
from community.models import Community
from organize.models import Organize
from appuser.models import AdaptorUser as User
from django.conf import settings

#  收入
class Incomes(BaseDate):
    """
    收入表
    """
    
    uuid = models.CharField(max_length=64, unique=True)
    # 收入来源对应model的uuid，如来自互助，则为Aid表的uuid
    appuuid = models.CharField(max_length= 64 )
    # 收入来源：互助、有偿服务等
    apptype = models.PositiveSmallIntegerField(default=settings.AID)
    # 正表示收入，负表示支出
    money = models.FloatField() 
    # 收入说明：如平台分成多少、物业分成多少
    detail = models.TextField() 
    YES = 1
    NO = 0 
    # 是否已经提现
    withdraw = models.PositiveSmallIntegerField(default = NO)

    class Meta:
        abstract = True 

class UserIncomes(Incomes):
    # 业主收入
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    class Meta: 
        ordering = ['-date']
        default_permissions = ()

class OrgIncomes(Incomes):
    # 物业收入
    org = models.ForeignKey(Organize, on_delete=models.PROTECT)
    class Meta: 
        ordering = ['-date']
        default_permissions = ()

class PlaformIncomes(Incomes):
    # 平台收入 
    class Meta: 
        ordering = ['-date']
        default_permissions = ()