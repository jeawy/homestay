from importlib import import_module
import requests
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse 
from django.views import View
import os
from rest_framework.views import APIView 
from pay.views import checkbill
from django.conf import settings   
from property.code import SUCCESS, ERROR 
import pdb  
import json 
from pay.wxpayV3 import WeixinPay
from property.code import ZHIFUBAO, WEIXIN
from common.logutils import getLogger
logger = getLogger(True, 'weixin', False)
 

class PayWxView(APIView):
    def get(self, request):  
        if 'checkbill' in request.GET and 'billno' in request.GET:
            # 微信查询网页支付订单
            billno = request.GET['billno'] 
            sub_mch_id = request.GET.get('sub_mch_id', None) 
            content = checkbill(billno, sub_mch_id)

            if content['status'] == SUCCESS:
                # 更新订单
                pass
        return HttpResponse(json.dumps(content), content_type="application/json") 
    
    def post(self, request):
        bill = "M20211221014001795261690"  
        wxpay = WeixinPay( )
        result = wxpay.checkBillStatus( bill  )
        return JsonResponse(result)
          
def alipay_notify(request):
    """

    """
    
    return HttpResponse("get from alipay")
 