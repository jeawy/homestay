#! -*- coding:utf-8 -*-
from django.db import models

from appuser.models import AdaptorUser as User
 

class Address(models.Model):
    """
    收货地址表
    """
    # 具体地址
    detail = models.CharField(max_length=100, null=True)
    # 地址
    address = models.CharField(max_length=200)
    # 是否为默认地址
    YES = 1
    NO = 0
    default = models.SmallIntegerField(default=YES)
    # 收货人的电话号码
    phone = models.CharField(max_length=50)
    # 地址创建人
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='address_creator')
    # 收件人
    receiver = models.CharField(max_length=200)
    
    class Meta:
        default_permissions = ()