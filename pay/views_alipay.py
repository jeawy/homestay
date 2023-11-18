import requests
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from alipay import AliPay
from django.views import View
from property.code import ZHIFUBAO, WEIXIN
import os
from django.conf import settings 
from mobile.detectmobilebrowsermiddleware import DetectMobileBrowser
from community.comm_statistics import community_statatics
from property.code import SUCCESS, ERROR
from msg.models import MsgOrders 
dmb     = DetectMobileBrowser()
import pdb 
import json
from common.logutils import getLogger
logger = getLogger(True, 'alipay', False)


def get_alipy_url(order_id, total_amount, subject ):
    alipay = AliPay(
        appid=settings.ALIPAY_APPID,
        app_notify_url=None,  # 默认回调url
        app_private_key_string=settings.APP_PRIVATE_KEY_STRING,
        alipay_public_key_string=settings.ALIPAY_PUBLIC_KEY_STRING, 
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=False  # 默认False  配合沙箱模式使用
    ) 

    # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
    order_string = alipay.api_alipay_trade_page_pay(
        out_trade_no = order_id,
        total_amount = str(total_amount),  # 将Decimal类型转换为字符串交给支付宝
        subject = subject,
        return_url = settings.ALIPAY_RETURN_URL,
        notify_url = settings.ALIPAY_NOTIFY_URL  # 可选, 不填则使用默认notify url
    )

    # 让用户进行支付的支付宝页面网址
    url = settings.ALIPAY_URL + "?" + order_string 
    return url


class PayAlipayView(View):
    def get(self, request): 
        # 支付宝的网站支付回调地址
        if 'out_trade_no' in request.GET:
            # 支付宝回调地址
            order_id = request.GET['out_trade_no']
            logger.debug("order no: "+ order_id)
            alipay = AliPay(
                appid=settings.ALIPAY_APPID,
                app_notify_url=None,  # 默认回调url
                app_private_key_string=settings.APP_PRIVATE_KEY_STRING,
                alipay_public_key_string=settings.ALIPAY_PUBLIC_KEY_STRING,
                # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
                sign_type="RSA2",  # RSA2,官方推荐，配置公钥的时候能看到
                debug=False  # 默认False  配合沙箱模式使用
            )
 
            # 调用alipay工具查询支付结果
            resp = alipay.api_alipay_trade_query(order_id)  # resp是一个字典
            # 判断支付结果
            code = resp.get("code")  # 支付宝接口调用成功或者错误的标志
            trade_status = resp.get("trade_status")  # 用户支付的情况
            
            # {'code': '10000', 'msg': 'Success', 'buyer_logon_id': 'fet***@sandbox.com', 
            # 'buyer_pay_amount': '0.00', 'buyer_user_id': '2088102175947174', 
            # 'buyer_user_type': 'PRIVATE', 'invoice_amount': '0.00', 
            # 'out_trade_no': '3232423111443234ASU', 'point_amount': '0.00', 
            # 'receipt_amount': '0.00', 'send_pay_date': '2018-03-29 23:12:40', 
            # 'total_amount': '0.01', 'trade_no': '2018032921001004170200926730', 
            # 'trade_status': 'TRADE_SUCCESS'}
            logger.debug("支付宝通知到位")
            logger.debug(str(resp))

            if code == "10000" and trade_status == "TRADE_SUCCESS":
                # 表示用户支付成功
                # 返回前端json，通知支付成功 
                trade_no = resp.get("trade_no")
                total_amount = resp.get("total_amount")
                send_pay_date = resp.get("send_pay_date")
                buyer = resp.get("buyer_logon_id")
                payedmoney = resp.get("total_amount")
                receipt_amount = resp.get("receipt_amount")  
                if order_id.startswith("M"):
                    # 短信充值订单
                    order = MsgOrders.objects.get(billno = order_id)
                    order.paybillno = trade_no
                    order.buyer = buyer 
                    order.payway = ZHIFUBAO
                    order.payedmoney = payedmoney
                    order.receipt_amount = receipt_amount
                    order.status = order.PAYED  
                    order.save()
                    community_statatics(order.community) 
                    return JsonResponse({"status": 0, "msg": "支付成功"})
                 
            elif code == "40004" or (code == "10000" and trade_status == "WAIT_BUYER_PAY"):
                # 表示支付宝接口调用暂时失败，（支付宝的支付订单还未生成） 后者 等待用户支付
                # 继续查询
                print(code)
                print(trade_status)
                return JsonResponse({"status": code, "msg": "继续查询订单状态"})  
            else:
                # 支付失败
                # 返回支付失败的通知
                logger.debug("支付失败")
                return JsonResponse({"status": 1, "msg": "支付失败，请联系平台技术支持"})
        else:
            logger.debug("参数错误")
            return JsonResponse({"status": 1, "msg": "参数错误"})
          
def alipay_notify(request):
    """

    """
    
    return HttpResponse("get from alipay")
 