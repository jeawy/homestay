# -*- coding:utf-8 -*-
from rest_framework.views import APIView 
from pay.wxpayV3 import WeixinPay
from property.code import ZHIFUBAO, WEIXIN, YUE
from django.db.models import Sum
from paidservice.models import PaidOrder
from property.code import SUCCESS, ERROR
from property.views_pay import alipay
import json
import os
import time
from datetime import datetime
import pdb
from typing import BinaryIO
from django.shortcuts import render
from django.http import HttpResponse
from pay.PayToolUtil import PayToolUtil
from django.conf import settings 
from bills.comm import get_bill_money
from bills.models import Bills, BillSpec 
from common.logutils import getLogger 
from card.comm import get_left_money, reduce_money
from webcoin.comm import reduce_coin
from pay.comm_status import check_orders,\
                            create_aid_service_notice, \
                            create_aid_platform_notice 
logger = getLogger(True, 'pay', False)


class PayView(APIView):
    def get(self, request):
        content = {}
        user = request.user
        money = 9999999
        if 'payway' in request.GET:
            payway = request.GET['payway']
            billno = request.GET['bills']
             
            sub_mch_id = None
            subject = ""  
            kwargs = {} 
            
            kwargs['billno'] = billno 
            try:
                bill = Bills.objects.get(
                    **kwargs)
                subject = bill.subject
                specs = BillSpec.objects.filter(bill = bill)
                money = 0
                for spec in specs:
                    money += spec.number * spec.price
  
            except Bills.DoesNotExist:
                content['msg'] = "未找到订单"
                content['status'] = ERROR
                return HttpResponse(json.dumps(content), content_type="application/json")
             
            if payway == 'zhifubao':
                # 支付宝支付
                alipay_str = alipay(
                    billno, money, subject, pc=False)
                content['msg'] = alipay_str
                content['status'] = SUCCESS
            else:
                # 微信支付  
                mch_id = settings.WEIXINPAY['mch_id']
                app_id = settings.WEIXINPAY['app']['app_id'] 

                trade_type = 'app' 
                if "trade_type" in request.GET:
                    trade_type = request.GET['trade_type']
                if trade_type=="wechatMp":
                    # 小程序 支付 
                    openid = request.GET['openid']  
                    # 支付到平台账户中 
                    wxpay = WeixinPay(md5=True)
                    wxresult = wxpay.unified_order(
                        order_id=billno,
                        openid = openid,
                        # 和支付宝支付不同，微信支付是以分为单位，所以不能传入小数，要支付的金额乘以100作为标价金额参数即可。
                        amount=int(money * 100),
                        desc=subject,
                        notify_url = settings.WEIXINPAY['notifyurl']
                    )
                     
                    content['msg'] = wxresult
                else:
                    # APP 中支付 
                     
                    wxpay = WeixinPay( ) 
                    
                    wxresult = wxpay.unified_order_app(
                        order_id=billno,
                        # 和支付宝支付不同，微信支付是以分为单位，所以不能传入小数，要支付的金额乘以100作为标价金额参数即可。
                        amount=int(money * 100),
                        desc=subject
                    )
                    
                    config = {
                        "appId": app_id,
                        "noncestr": wxresult['nonce_str'],
                        "package": "Sign=WXPay",
                        "partnerid": mch_id,
                        "prepayid": wxresult['prepay_id'],
                        "timestamp": int(wxresult['timestamp']),
                        "sign": wxresult['pay_sign'][:30]
                    }
                    content['msg'] = config
                content['status'] = SUCCESS
            
            return HttpResponse(json.dumps(content), content_type="application/json")
                 

    def post(self, request):
        # 手机APP端：更新订单状态
        content = {}
        user = request.user
        if 'payway' in request.POST:
            payway = request.POST['payway']  
            kwargs = {}
            bills =  request.POST['bills']
            kwargs['billno'] = bills
            kwargs['status'] = Bills.NON_PAYMENT
                  
            if payway == "zhifubao":
                try:
                    order = Bills.objects.get(
                        **kwargs) 
                except Bills.DoesNotExist:
                    content['msg'] = "账单不存在"
                    return HttpResponse(json.dumps(content), content_type="application/json")

                paymsg = json.loads(request.POST['paymsg'])
                logger.debug(paymsg)
                payresult = json.loads(paymsg['result'])
                resp = payresult['alipay_trade_app_pay_response']
                code = resp.get('code')
                if code == "10000":
                    # 支付成功
                    total_amount = resp.get('total_amount') 
                    trade_no = resp.get('trade_no') 

                    # 如果支付金额与订单金额相符，则直接更新订单为已支付
                    if float(total_amount) != order.money:
                        # 支付金额与订单金额不符
                        order.remark = "支付金额与订单金额不符" 
                        order.payway = ZHIFUBAO 
                        order.paybillno = trade_no 
                        order.status = Bills.UNUSUAL
                        order.feerate = order.community.aid_commission_rate # 当时费率
                        order.save() 
                        content['msg'] = "订单异常"
                        content['status'] = ERROR
                        # 此处应该给系统管理人员发短信提醒有异常订单需要处理 
                        create_aid_platform_notice(order)
                    else:
                        order.payway=ZHIFUBAO 
                        order.paybillno=trade_no 
                        order.status=Bills.PAYED
                        order.save()  
                        content['msg'] = "支付成功"
                        content['status'] = SUCCESS
                        create_aid_service_notice(order)
                else:
                    content['msg'] = "未支付成功"
                    content['status'] = ERROR
            elif payway == 'weixin':
                # 微信支付
                try:
                    order = Bills.objects.get(**kwargs)
                    check_orders(order)
                    if order.status == order.PAYED:
                        content['msg'] = "支付成功"
                        content['status'] = SUCCESS
                    else:
                        content['msg'] = "订单异常"
                        content['status'] = ERROR
                        # 此处应该给系统管理人员发短信提醒有异常订单需要处理
                except Bills.DoesNotExist:
                    content['msg'] = "账单不存在"
            elif payway == "yue":
                # 购物卡余额支付
                try:
                    order = Bills.objects.get(**kwargs)  
                    money = get_bill_money(order)
                    status, msg = reduce_money(user, money, order)
                    if status == 2:# "用户已锁定, 请等待"
                        times = 5
                        while True: 
                            time.sleep(3) # 三秒之后刷新
                            status, msg = reduce_money(user, money, order)
                            if status == 2:
                                if times == 0:
                                    break
                                else:
                                    times -= 1
                            else:
                                break

                    if status == 1: # 余额不足
                        content['msg'] = msg
                    elif status == 0: # 已支付
                        content['msg'] = msg
                        content['status'] = SUCCESS
                        order.status = order.PAYED
                        order.payway = YUE # 余额支付
                        order.save() 
                    # 此处应该给系统管理人员发短信提醒有异常订单需要处理
                except Bills.DoesNotExist:
                    content['msg'] = "账单不存在"
              
            return HttpResponse(json.dumps(content), content_type="application/json")
              

def weixin(request):
    """
    微信支付查询API
    """
    content = {}
    content['status'] = 'error'

    billno = request.GET.get('billno')
    if billno is None:
        content['msg'] = '请在GET中提供billno订单号.'
        return HttpResponse(json.dumps(content), content_type="application/json")

    content = checkbill(billno)
    if content['status'] == 'ok':

        if 'book' in content:
            content['book'] = content['book'].id
            content['status'] = 'go'  # 跳转

    return HttpResponse(json.dumps(content), content_type="application/json")


def checkbill(billno, sub_mch_id=None):
    """
    检查bill订单状态,查询网址支付订单
    """
    if sub_mch_id is None:
        paycheck = PayToolUtil(way = "platform")
    else:
        paycheck = PayToolUtil()
    weixin_returned = paycheck.getQueryUrl(billno, sub_mch_id)
    weixin_returned = weixin_returned['xml']

    return_code = weixin_returned['return_code']
    result_code = weixin_returned['result_code']

    content = {}
    content['status'] = ERROR
    if return_code == PayToolUtil._SUCCESS and result_code == PayToolUtil._SUCCESS:
        """
        trade_state:
        SUCCESS—支付成功
        REFUND—转入退款
        NOTPAY—未支付
        CLOSED—已关闭
        REVOKED—已撤销（刷卡支付）
        USERPAYING--用户支付中
        PAYERROR--支付失败(其他原因，如银行返回失败)
        支付状态机请见下单API页面
        """
        trade_state = weixin_returned['trade_state']

        if trade_state == PayToolUtil._SUCCESS:
            # 订单支付成功，更新bill 
            transaction_id = weixin_returned['transaction_id']
            total_fee = int(weixin_returned['total_fee']) / 100
            order_id = weixin_returned['out_trade_no']
            send_pay_date = weixin_returned['time_end']
            send_pay_date = datetime.strptime(send_pay_date, '%Y%m%d%H%M%S')
 
            # 删除生成的二维码
            erweimafile = os.path.join(settings.FILEPATH, 'pay', order_id+'weixinqr.png')
            if os.path.isfile(erweimafile):
                os.remove(erweimafile)

            content['status'] = SUCCESS
            content['msg'] = {
                "transaction_id":transaction_id,
                "total_fee" : total_fee
            }
        else:
            # 未成功
            """
            SUCCESS—支付成功

            REFUND—转入退款

            NOTPAY—未支付

            CLOSED—已关闭

            REVOKED—已撤销（刷卡支付）

            USERPAYING--用户支付中

            PAYERROR--支付失败(其他原因，如银行返回失败)
            """
            if trade_state == 'REFUND':
                content['msg'] = '转入退款'
            elif trade_state == 'NOTPAY':
                content['status'] = 'ok'
                content['msg'] = '未支付'
            elif trade_state == 'CLOSED':
                content['msg'] = '已关闭'
            elif trade_state == 'REVOKED':
                content['msg'] = '已撤销（刷卡支付）'
            elif trade_state == 'USERPAYING':
                content['msg'] = '用户支付中'
            else:
                content['msg'] = '支付失败(其他原因，如银行返回失败)'

    return content
