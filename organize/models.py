#! -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from basedatas.models import BaseDate
from appuser.models import AdaptorUser as User
from property.code import ZHIFUBAO, WEIXIN
 
 

class Organize(BaseDate):
    """物业类""" 
    uuid = models.CharField(max_length= 64, unique=True )  
    # 物业公司名称
    name = models.CharField(_('name'), max_length=128, unique=True)
    # 物业别名、简称
    alias = models.CharField(max_length=32 , null=True)
    # 管理员：可以在这个小区内部分配权限和角色
    manager  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    # 统一社会信息代码
    code = models.CharField(max_length=64 , null=True)

    logo = models.CharField(max_length=256 , null=True)
    # 营业执照路径
    license = models.CharField(max_length=256 , null=True)
     
    def __str__(self):
        return self.name

    class Meta:
        db_table = 'organize'
        default_permissions = ()
        permissions = [("manager_organize", "编辑物业基本信息")]

 