#! -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from basedatas.models import BaseDate
from appuser.models import AdaptorUser as User
from community.models import Community


class Repair(BaseDate):
    """维修请求"""
    uuid = models.CharField(max_length= 64, unique=True) # UUID 
    # 维修
    AVERAGE = 0
    URGENT = 1
    SUPOR_URGENT = 2
    user = models.ForeignKey(User,  on_delete=models.PROTECT)

    # 编码
    # 大楼编号+类型号（比如A、B、C）+ 房号+ 日期时分秒毫秒
    code = models.CharField(_('code'), max_length=64, unique = True) 
    community = models.ForeignKey(Community, on_delete = models.PROTECT)
    # 等待维修的设施名称
    facilities = models.CharField(_('facilities'), max_length = 2048)
    # 紧急程度
    urgency_level = models.SmallIntegerField(default = AVERAGE)

    # 期望的起始时间，可以为空
    prefertime_start = models.DateTimeField(null = True)
    prefertime_end = models.DateTimeField(null=True)
    # 物业来之前是否需要提前联系，默认0，表示不需要
    # 1 表示需要
    need_contact = models.SmallIntegerField(default = 0)
    phone = models.CharField(null = True, max_length=32)
    email = models.CharField(null = True, max_length=128)
    # 备注
    note = models.TextField(null = True)

    # user delete it
    owner_delete = models.SmallIntegerField(default=0)

    # organize delete it
    org_delete = models.SmallIntegerField(default=0)


    # 0 draft
    # 1 ongoing
    # 2 completed
    DRAFT = 0
    ONGOING = 1
    COMPLETED = 2
    CANCEL = 3
    ACCEPT = 4
    DECLINE = 5
    status = models.SmallIntegerField(default = ONGOING)

    replied_note = models.CharField(max_length= 256 , null = True)
    replied_date = models.DateTimeField(null = True)
    # 维修人员姓名
    replied_user = models.CharField(max_length= 32 , null = True)

    # 维修记录
    record_date = models.CharField(null = True, max_length=128)
    record_repairedby = models.CharField(null = True, max_length=128)


    class Meta:
        default_permissions = () 
        db_table = 'repair'
        ordering = ['-date']

    def __str__(self):
        return self.facilities

    def level_list(self):
        return [self.AVERAGE, self.URGENT, self.SUPOR_URGENT]

    def status_list(self):
        return [self.DRAFT, self.ONGOING, self.COMPLETED, self.CANCEL, self.ACCEPT, self.DECLINE]