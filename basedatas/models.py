# -*- coding: utf-8 -*-
from django.db import models
from property.code import ZHIFUBAO, WEIXIN
import os


class BaseDate(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    modify_date = models.DateTimeField(auto_now=True)


    class Meta:
        abstract = True


class PayBase(BaseDate):
    """
    支付订单接口基础类
    """
    uuid = models.CharField(max_length= 64, unique=True)
    # 标题
    subject = models.CharField(max_length=128) 
    # 订单号
    billno = models.CharField(max_length = 64, unique=True)
    # 总金额
    money = models.FloatField(default=9999999.99) 

    # 支付方式 
    payway = models.PositiveSmallIntegerField(null = True)
    # 支付宝或者微信的订单号
    paybillno = models.CharField(max_length = 256, null = True)
    # 支付宝或者微信购买者账户 
    buyer = models.CharField(max_length=128 , null = True)
    # 支付金额，支付金额应该要与money相同
    payedmoney = models.FloatField(null = True)
    # 实收金额，单位为元，两位小数。该金额为本笔交易，商户账户能够实际收到的金额
    receipt_amount = models.FloatField(null = True)
    
    # 平台收取的费率
    feerate = models.FloatField(default=0.006)
    
    class Meta:
        abstract = True


class Pic(models.Model):
    url = models.CharField(max_length=4096)
    name = models.CharField(max_length=4096, default='')

    class Meta:
        abstract = True
