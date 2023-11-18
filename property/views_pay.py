from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from alipay import AliPay
import os
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


import pdb 
def init():
    app_private_key_string = settings.APP_PRIVATE_KEY_STRING
    alipay_public_key_string = settings.ALIPAY_PUBLIC_KEY_STRING
    alipay_intance = AliPay(
        appid=settings.ALIPAY_APPID,
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,
        alipay_public_key_string=alipay_public_key_string,

        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=False  # 默认False  配合沙箱模式使用
    )
    return alipay_intance

def alipay(order_id, total_amount, subject, pc = True, app = True):
    #request.POST.get("order_id")
    # 创建用于进行支付宝支付的工具对象
    total_amount = str(total_amount) 
    alipay = init()

    
    if pc :
        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no = order_id,
            total_amount = str(total_amount),  # 将Decimal类型转换为字符串交给支付宝
            subject = subject,
            return_url = settings.ALIPAY_RETURN_URL,
            notify_url = settings.ALIPAY_NOTIFY_URL  # 可选, 不填则使用默认notify url
        )
        # 让用户进行支付的支付宝页面网址
        return settings.ALIPAY_URL + "?" + order_string
    elif app :
        order_string = alipay.api_alipay_trade_app_pay(
            out_trade_no=order_id,
            total_amount=str(total_amount),
            subject=subject,
            notify_url= settings.ALIPAY_NOTIFY_URL # this is optional
        )  
        return order_string   
    else: 
        # 手机网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_wap_pay(
            out_trade_no= order_id,
            total_amount=str(total_amount),
            subject=subject,
            return_url=settings.ALIPAY_RETURN_URL,
            notify_url=settings.ALIPAY_NOTIFY_URL  # 可选, 不填则使用默认notify url
        )
        # 让用户进行支付的支付宝页面网址
        return settings.ALIPAY_URL + "?" + order_string
     
    
def alipay_refund(order_id, total_amount):
    # 退款
    # 创建用于进行支付宝支付的工具对象
    alipay =  init()
   
    # 2018042723221914
    result = alipay.api_alipay_trade_refund(str(total_amount), order_id)
    #return redirect(url)
     
    return result


def alipay_notify(request):
    """

    """
    
    return HttpResponse("get from alipay")

 