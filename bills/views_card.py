#! -*- coding:utf-8 -*-
from ast import Add
import imp
import json
import pdb
import os
import uuid
import time
from django.db.models import Sum
from datetime import datetime
from dateutil.relativedelta import SU, relativedelta
from django.http import HttpResponse
from django.conf import settings
from django.views import View
from address.models import Address
from common.utils import get_final_date
from pay.wxpayV3 import WeixinPay
from property.code import SUCCESS,  ERROR
from cart.models import Cart
from property.code import ZHIFUBAO, WEIXIN
from bills.models import Bills, BillSpec
from bills.comm import getbillno, getbill
from product.models import Specifications 
from rest_framework.views import APIView
from common.logutils import getLogger 
logger = getLogger(True, 'bills', False)
  
 
class CardView(APIView):
    """ 
    """ 
    def get(self, request):
        # 业主获取自己的等待绑定的购物卡
        result = {
            "status": ERROR
        }
        user = request.user
        kwargs = {}
        kwargs['bill__user'] = user
        kwargs['card__isnull'] = False
        kwargs['card__user__isnull'] = True
          
        if "page" in request.GET and "pagenum" in request.GET:
            # 分页
            pagenum = request.GET['pagenum']
            page = request.GET['page']
            try:
                page = int(page) - 1
                pagenum = int(pagenum)
            except ValueError:
                page = 0
                pagenum = settings.PAGE_NUM
        else:
            page = 0
            pagenum = settings.PAGE_NUM 
      
        total = BillSpec.objects.filter(**kwargs).count()  
        orders = list(BillSpec.objects.filter(**kwargs).values(
            "card__uuid",
            "bill__date",
            "card__cardtype",
            "card__money",
            "card__left",
            "card__status"   
        )[page*pagenum: (page+1)*pagenum])
        for order in orders:
            order['uuid'] =  order['card__uuid']
            order['bill__date'] = time.mktime(order['bill__date'].timetuple())
            order['date'] =  order['bill__date']
            order['cardtype'] =  order['card__cardtype']
            order['money'] =  order['card__money']
            order['left'] =  order['card__left']
            order['status'] =  order['card__status']
        result['status'] = SUCCESS
        result['msg'] = {
                            "total": total,
                            "orders": orders
                        }  
        return HttpResponse(json.dumps(result), content_type='application/json')  
 
    def post(self, request):
        """
        提交订单：先提交到数据库，
        然后将订单id存入redis，
        进行排队减库存
        """
        result = {
            "status": ERROR
        }
        user = request.user
        data  = request.POST
        if 'method' in data:
            method = data['method'].lower()
            if method == 'put':
                return self.put(request) 

        if 'specs' in data and 'addressid' in data: 
            # specids 规格id列表
            # addressid 收货地址，如果是实物addressid是必须的 
            specs = data['specs'] 
            specs = json.loads(specs)
            addressid = data['addressid'] 
             
             
        return HttpResponse(json.dumps(result), content_type="application/json")
 