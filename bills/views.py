#! -*- coding:utf-8 -*-
from ast import Add
import imp
import json
import pdb
import os
import uuid
import time
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
from common.sms import send_sms
from pay.views_alipay import get_alipy_url 
from pay.controller import MainController
from area.comm import get_parent
from common.redisconf import RedisSubscri
from webcoin.comm import reduce_coin
from common.express import get_express


 
class OrderConsumerView(View):
    def post(self, request):
        # 减库存
        result = {}
        result['status'] = ERROR 
        myredis = RedisSubscri()
        redisconn = myredis.getconn()
        while True:
            billinfo = redisconn.rpop("bills") # 发布到队列中
            if billinfo is None:
                break
            logger.debug("billno:"+str(billinfo))  
            try:
                billinfo = billinfo.split(",")
                if len(billinfo) == 2:
                    if billinfo[1] == 1 or billinfo[1] == '1': # 减库存操作
                        bill = Bills.objects.get(uuid = billinfo[0])

                        if bill.status in [2,3,4,5]:
                            continue

                        specs = BillSpec.objects.filter(bill = bill)
                        for spec in specs:
                            if spec.number > spec.spec.number:
                                # 库存不足
                                bill.status = bill.NOTENOUGH 
                                bill.save()
                                result['msg'] = "库存不足"
                                return HttpResponse(json.dumps(result), content_type="application/json")
                        needcoin  = 0 # 总积分，只有当有效
                        for spec in specs:
                            # 减库存
                            spec.spec.number = spec.spec.number - spec.number  
                            spec.spec.save()
                            needcoin += spec.number * spec.price

                        bill.status = bill.NON_PAYMENT
                        bill.save()
                        if bill.ordertype == bill.COIN:
                            # 积分换礼订单，直接减积分
                            times = 5
                            while True:
                                status, msg = reduce_coin(bill, needcoin)
                                if status == 2:# 用户锁定了，继续查询
                                    times -= 1
                                    time.sleep(3)
                                else:
                                    break
                                if times == 0:
                                    # 订单超时
                                    break


                        result['status'] =  SUCCESS
                        result['msg'] = "订单已更新" 
                    else: # 退库操作 
                        bill = Bills.objects.get(uuid = billinfo[0]) 
                        if bill.status in [2,3,4]:# 进行中的订单无法退库
                            continue

                        specs = BillSpec.objects.filter(bill = bill)
                        logger.debug("billno:"+str(bill.billno)+"执行退库操作")  
                        for spec in specs:
                            # 减库存
                            spec.spec.number = spec.spec.number + spec.number  
                            spec.spec.save()
                        if bill.status in [0, 6, -1]: # 无效订单，可以删除
                            bill.delete() # 退库后删除订单
                        
                        result['status'] =  SUCCESS
                        result['msg'] = "已退库"  
                else:
                    # 参数错误，应该是用英文逗号隔开的uuid以及操作标识符
                    logger.error("参数错误，应该是用英文逗号隔开的uuid以及操作标识符:"+str(billinfo))  
                    result['msg'] = "参数错误"
            except Bills.DoesNotExist: 
                result['msg'] = "订单不存在"
         
        result['msg'] = "参数错误"
        return HttpResponse(json.dumps(result), content_type="application/json")


class OrderView(APIView):
    """ 
    """ 
    def get(self, request):
        # 业主获取自己的账单
        result = {
            "status": ERROR
        }
        user = request.user
        if 'count' in request.GET and user.is_superuser:
            # 只有超级管理员可以获取订单统计
            payed_count = Bills.objects.filter(status = Bills.PAYED).count()
            deliveried_count = Bills.objects.filter(status = Bills.DELIVERIED).count()
            finished_count = Bills.objects.filter(status = Bills.FINISHED).count()
             
            result['status'] = SUCCESS
            result['msg'] = {
                "payed_count":payed_count,
                "deliveried_count":deliveried_count,
                "finished_count":finished_count,
            }
            return HttpResponse(json.dumps(result), content_type="application/json")
        if 'billuuid' in request.GET and 'status' in request.GET:
            # 获取订单总金额
            billuuid = request.GET['billuuid'].strip()
            try:
                bill = Bills.objects.get(uuid = billuuid)
                result['status'] = SUCCESS
                money = 0
                specs = BillSpec.objects.filter(bill = bill)
                gifttype = 0
                for spec in specs:
                    money += spec.number * spec.price
                    gifttype = spec.spec.product.gifttype
                money = float(money)
                result['msg'] = {
                    'status':bill.status,
                    'billno':bill.billno,
                    'money':money,
                    "gifttype":gifttype} 
            except Bills.DoesNotExist:
                result['msg'] = "未找到订单信息"
            return HttpResponse(json.dumps(result), content_type="application/json")
        if 'billuuid' in request.GET and 'delivery' in request.GET:
            # 获取订单物流信息:如果已签收了，则直接从数据库中获取物流信息，
            # 如果还没有签收，则实时查询物流信息
            billuuid = request.GET['billuuid'].strip()
            try:
                bill = Bills.objects.get(uuid = billuuid) 
                if bill.status == bill.FINISHED and bill.delivery_way ==0: # 已签收 
                    ss = bill.delivery.replace("'", '"')
                    result['msg'] = json.loads(ss)  
                elif bill.status == bill.DELIVERIED: # 已发货
                    express_result = get_express(bill.express_number) 
                    if express_result[0] == SUCCESS:
                        # 查询成功
                        express_result_json = express_result[1]
                        if express_result_json['issign'] == "1" or express_result_json['issign'] == 1:
                            # 已签收 
                            bill.status = bill.FINISHED 
                            bill.delivery = express_result_json['list']
                            bill.save()
                         
                        result['msg'] = express_result_json['list']
                    else:
                        result['status'] = ERROR
                        result['msg'] = express_result[1] 
                        return HttpResponse(json.dumps(result), content_type="application/json")
                else:
                    result['msg'] = []
                result['status'] = SUCCESS
                 
            except Bills.DoesNotExist:
                result['msg'] = "未找到订单信息"
            return HttpResponse(json.dumps(result), content_type="application/json")
        
        elif 'billuuid' in request.GET :
            # 获取订单详情
            billuuid = request.GET['billuuid']
            try:
                bill = Bills.objects.get(uuid = billuuid, user = user)
                result['status'] = SUCCESS
                result['msg'] = getbill(bill)
            except Bills.DoesNotExist:
                result['msg'] = "未找到订单信息"
            return HttpResponse(json.dumps(result), content_type="application/json")

        kwargs = {}
        if 'status' in request.GET:
            status = request.GET['status']
            if status != -1 and status != '-1':
               kwargs['status'] = status
             
        if 'billno' in request.GET:
            billno = request.GET['billno']
            kwargs['billno__icontains'] = billno
        
        kwargs['user'] = user
        kwargs['owner_delete'] = 0 # 本人未删除的订单
              
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

        total = Bills.objects.filter(**kwargs).count() 

        orders = list(Bills.objects.filter(**kwargs).values(
            "uuid",
            "billno",
            "subject",
            "date",
            "money", 
            "payway",
            "paybillno",
            "express_number",
            "express_company",
            "receiver",
            "receiver_phone",
            "receiver_address",
            "remark",  
            "status",  
        )[page*pagenum: (page+1)*pagenum])
        for order in orders:
            order['date'] = time.mktime(order['date'].timetuple())
            order['specs'] = list(BillSpec.objects.filter(bill__uuid = order['uuid']).values(
                "number",
                "name",
                "picture",
                "title",
                "price",
                "content",
                "money" 
                ))
            money = 0
            for spec in order['specs']:
               money +=  spec['price'] * spec['number']
            
            order['money'] = money
             
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
            elif method == 'delete':
                return self.delete(request)


        if 'specs' in data and 'addressid' in data: 
            # specids 规格id列表
            # addressid 收货地址，如果是实物addressid是必须的 
            specs = data['specs'] 
            specs = json.loads(specs)
            addressid = data['addressid'] 
            if len(specs) > 0: 
                address = None
                if int(addressid) == -1:
                    # 自提
                    delivery_way = 1
                else: 
                    delivery_way = 0
                    try:
                        address = Address.objects.get(id = addressid, 
                                                user = user)
                    except Address.DoesNotExist:
                        result['msg'] = "未找到收货地址"
                        return HttpResponse(json.dumps(result), content_type="application/json")


                subject = ""
                bill = Bills()
                bill.delivery_way = delivery_way
                bill.billno = getbillno()
                bill.uuid = str(uuid.uuid4())
                bill.user = user
                if delivery_way == 0: # 快递配送
                    bill.receiver_address =address.address  + address.detail
                    bill.receiver_phone = address.phone
                    bill.receiver = address.receiver
                bill.subject = subject
                
                if 'ordertype' in data:
                    ordertype = int(data['ordertype'])
                    if ordertype == bill.COIN:
                        # 积分兑换 
                        bill.ordertype = ordertype
                
                if 'remark' in data:
                    remark = data['remark'] 
                    bill.remark = remark

                bill.save() 
                for spec in specs:
                    number = spec['number']
                    spec_instance = Specifications.objects.get(id = spec['id'])
                    if spec_instance.number < number:
                        # 库存不足，订单提交失败
                        bill.delete()
                        result['msg'] = spec_instance.name + "库存不足"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    else:
                        # 先不减库存，redis中减库存 
                        if bill.ordertype == bill.COIN:
                            # 如果是积分订单，则price存的是积分数量
                            price = spec_instance.coin
                        else:
                            price = spec_instance.price
                        BillSpec.objects.create(
                            number = number,
                            name = spec_instance.name,
                            price = price,
                            title = spec_instance.product.title,
                            picture = spec_instance.product.picture,
                            content = spec_instance.content,
                            bill = bill, 
                            spec = spec_instance,
                            money = number * price 
                        ) 
                        if subject == "":
                            subject =  spec_instance.name
                        else:
                            subject += ","+spec_instance.name
                bill.subject = subject
                
                bill.save()
                
                # 存入redis队列
                myredis = RedisSubscri()
                redisconn = myredis.getconn()
                # uuid和操作标识符，1表示减库存 操作也就是下单，0表示退库操作
                redisconn.lpush("bills", bill.uuid+",1") # 发布到队列中
                print(myredis.publish("consumer", "bills")) # 通知订阅者进行消费，更新库存

                result['status'] = SUCCESS
                result['msg'] = str(bill.uuid)
            
            
            
        elif 'webpay' in data  \
            and 'orderuuid' in data and 'auth_code' in data:
            # auth_code 扫码字符串
            # 物业网页版支付 
            orderuuid = data['orderuuid']
            # 微信支付码规则：18位纯数字，以10、11、12、13、14、15开头 
            # 支付宝支付码规则：25 - 30开头的长度为16~24位的数字，实际字符串长度以开发者获取的付款码长度为准
            auth_code = data['auth_code']
            payway = int(auth_code[:2])

            if payway > 9 and payway < 16:
                payway = WEIXIN
            elif payway <= 30 and payway >= 25:
                payway = ZHIFUBAO
            else:
                result['msg'] = "不支持的付款类型"
                result['status'] = ERROR 
                return HttpResponse(json.dumps(result), content_type="application/json")

            try:
                order = RoomFeeOrders.objects.get(uuid = orderuuid, 
                        status = RoomFeeOrders.NON_PAYMENT)
                if int(payway) == ZHIFUBAO:
                    url = get_alipy_url(order.billno, order.money, order.subject)
                    result['msg'] = { 
                        "payway":payway,
                        "orderno":order.billno
                    } 
                else:
                    # 微信支付
                    """
                    kwargs = {}
                    kwargs["order_id"] = order.billno
                    kwargs["goodsName"] = order.subject
                    kwargs['goodsPrice'] = order.money
                    # 二维码地址
                    # weixinpay_ctl = MainController() 
                    # url = weixinpay_ctl.getWeChatQRCode( **kwargs)
                    """
                    # 直接支付到子商户中
                    kwargs = {}
                    kwargs["order_id"] = order.billno 
                    kwargs['amount'] = order.money
                    kwargs["desc"] = order.subject
                    kwargs['auth_code'] = auth_code 
                    wxpay = WeixinPay(sub_mch_id = sub_mch_id)
                    payresult = wxpay.native_order( **kwargs)
                    logger.debug(str(payresult))
                    
                    result['msg'] = { 
                        "payway":payway, 
                        "orderno":order.billno,
                        "sub_mch_id":sub_mch_id
                    }  
                result['status'] = SUCCESS

            except RoomFeeOrders.DoesNotExist:
                result['msg'] = "未找到该订单"
            
        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self,request):
        # 删除礼品
        result = {}

        user = request.user
        data = request.POST

        if 'uuids' in data:
            uuids = data['uuids']
            uuids = uuids.split(',')
 
            for uuiditem in uuids:
                try:
                    bill = Bills.objects.get(user = user, uuid = uuiditem)
                except Bills.DoesNotExist:
                    continue
                else:
                    # 删除礼品时删除磁盘中对应的图片和轮播图文件
                    if bill.status == bill.NON_PAYMENT:
                         
                        # 还要进行退库
                        # 存入redis队列
                        myredis = RedisSubscri()
                        redisconn = myredis.getconn()
                        # uuid和操作标识符，1表示减库存 操作也就是下单，0表示退库操作
                        redisconn.lpush("bills", bill.uuid+",0") # 发布到队列中
                        print(myredis.publish("consumer", "bills")) # 通知订阅者进行消费，更新库存
 
                    bill.owner_delete = 1
                    bill.save()
                    
            result['status'] = SUCCESS
            result['msg'] = '删除成功'
        else:
            result['status'] = ERROR
            result['msg'] = '缺少ids参数'
        return HttpResponse(json.dumps(result), content_type="application/json")
