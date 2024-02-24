# -*- coding:utf-8 -*-
import json
from datetime import datetime
import pdb  
from django.conf import settings
from common.logutils import getLogger
from property.entity import EntityType
logger = getLogger(True, 'pay', False)  
from property.code import SUCCESS, ERROR  
from property.code import ZHIFUBAO, WEIXIN
from pay.wxpayV3 import WeixinPay
from notice.comm import NoticeMgr 
from common.sms import send_sms 
from django.conf import settings
from common.utils import verify_phone 
from msg.comm import msgSendRecord
from bills.models import Bills, BillSpec
from bills.comm import get_bill_money
from card.comm import create_card
from card.models import Card
 

def check_orders(order):
    """
    查询订单支付状态
    """
    # 微信支付 查询订单状态
    wxpay = WeixinPay() 
    # 依次查询微信、支付宝看看是否已经支付
    # 先查微信支付
    wxresult = wxpay.checkBillStatus( out_trade_no = order.billno )
     
    if wxresult['status'] == SUCCESS and 'trade_state' in wxresult['msg']:
        # 获取支付订单状态失败  
        if wxresult['msg']['trade_state'] == "SUCCESS":
            # 支付成功
            payedmoney = wxresult['msg']['amount']['payer_total'] # 单元是分 
            payedmoney = payedmoney  / 100 # 单元换算成元 
             
            if get_bill_money(order) == payedmoney:
                # 金额一致, 更新订单状态 
                order.status = Bills.PAYED  
                order.paybillno = wxresult['msg']['transaction_id']  
                order.payway = WEIXIN 
                order.payedmoney = payedmoney 
                order.save() 
                for billspec in BillSpec.objects.filter(bill = order): 
                    if billspec.spec.product.gifttype == 1: # 购物卡
                        # 如果购买的是购物卡，则创建购物卡，购物卡和实物商品不在一个订单中进行支付
                        card = create_card(billspec.money, cardtype=Card.VIRTUAL )
                        billspec.card = card
                        billspec.save() 
 
                # 短信及通知 发给管理员
                for phone in settings.MANAGERS_PHONES:
                    send_sms(smstype="newbills",phone=phone)
                
                NoticeMgr.create(
                    title="{0}新订单已支付".format(order.billno)  , 
                    content = "",
                    pcurl = "/order-manage/order-detail?uuid="+str(order.uuid),
                    platform =1,
                    entity_type= EntityType.BILL
                )
            else:
                logger.error(json.dumps(wxresult))
                # 金额不一样，标记为异常订单 
                order.status = order.UNUSUAL 
                order.remark = "支付金额与订单金额不一致，标记为异常订单"
                order.save()
                # 短信及通知(发给系统管理用户) 
                for phone in settings.SYS_PHONES:
                    send_sms(smstype="sys",phone=phone, code="订单金额不符:"+order.billno)
    else:
        # 查支付宝订单
        logger.error(json.dumps(wxresult))
        
  
def create_fee_platform_notice(order):
    # 短信及通知(发给系统管理用户) 
    NoticeMgr.create(
        title="物业费账单异常，请关注",
        level = 2,
        content = "物业费账单:{0},订单金额与支付金额不一致,请及时排查".format(order.billno),
        pcurl = "/fee/list",
        platform=1 ,
        entity_type= EntityType.FEE
    )  

def create_aid_service_notice( order): 
    NoticeMgr.create(
        title="有偿求助:" + order.aid.title, 
        content = order.aid.content,
        appurl = "/pages/aid/detail?uuid="+str(order.aid.uuid), 
        entity_type= EntityType.AID
    )
    
      
def create_aid_platform_notice(order):
    # 短信及通知(发给系统管理用户) 
    NoticeMgr.create(
        title="交易异常订单，请关注",
        level = 2,
        content = "互助订单:{0},订单金额与支付金额不一致,请及时排查".format(order.billno),
        pcurl = "/paidservice/paidservice",
        platform=1 ,
        entity_type= EntityType.AID
    ) 
      
def create_paid_platform_notice(order):
    # 短信及通知(发给系统管理用户) 
    NoticeMgr.create(
        title="交易异常订单，请关注",
        level = 2,
        content = "有偿服务订单:{0},订单金额与支付金额不一致,请及时排查".format(order.billno),
        pcurl = "/paidservice/paidservice",
        platform=1 ,
        entity_type= EntityType.PAIDSERVICE
    ) 

def create_paid_service_notice(community):
    # 有偿服务
    # thread = Thread(target=thread_create_paid_service_notice, args=(community,))
    # thread.start()
    thread_create_paid_service_notice(community)
   

def thread_create_paid_service_notice(community):
    NoticeMgr.create(
        title="新的有偿服务请求", 
        content = "有新的有偿服务订单",
        pcurl = "/paidservice/paidservice", 
        entity_type= EntityType.PAIDSERVICE
    )
    if community.paidservice_msg:
        # 发短信通知给verify_phone
        kwargs = {
            "smsSignId":community.smsSignId
        }
        phones = community.paidservice_msg.split(",")
        for phone in phones:
            if verify_phone(phone):
                msg_result = send_sms(smstype="paidservice", 
                phone=phone, 
                code=community.name,
                **kwargs)
                msgSendRecord(community, phone, msg_result[1], status=0,msgtype=1 )
                
  
 