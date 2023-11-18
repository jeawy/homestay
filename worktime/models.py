#! -*- coding:utf-8 -*-
from django.db import models


# 节假日时间表 
class WorkTime(models.Model):
    festivalname = models.CharField(verbose_name='节日名字', max_length=200)
    festivalday = models.DateField(verbose_name='日期', unique=True)
    # FESTIVAL代表节假日，LEAVEOFF代表调休
    FESTIVAL = 0
    LEAVEOFF = 1
    state = models.SmallIntegerField(default=FESTIVAL)

    def __str__(self):
        return self.festivalname

    class Meta:
        ordering = ['festivalday']
        # 节假日管理的权限
        default_permissions = () 
        
