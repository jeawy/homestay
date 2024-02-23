#! -*- coding:utf-8 -*-
from ast import Add
import imp
import json
import pdb
import os
import uuid
import time
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.conf import settings   
from django.db.models import Sum
from numpy import blackman
from property.code import SUCCESS,  ERROR
from property.code import ZHIFUBAO, WEIXIN, YUE 
from bills.models import Bills, BillSpec
from bills.comm import getbillno, getbill
from product.models import Specifications 
from rest_framework.views import APIView
from common.logutils import getLogger 
logger = getLogger(True, 'bills', False)
from property.entity import EntityType 
from common.msg import send_notice
from common.redisconf import RedisSubscri 
from pay.comm_status import check_orders


class BillAdminView(APIView):
    """ 
    """ 
    def get(self, request):
        # 平台管理员获取已支付的订单
        result = {
            "status": ERROR
        }
        user = request.user
        if not user.is_superuser:
            # 权限不足
            result['msg'] = "权限不足" 
            return HttpResponse(json.dumps(result), content_type='application/json')  
        
        if 'count' in request.GET:
            # pc端统计
            today = datetime.now().date()
            bills = Bills.objects.filter(
                platform_delete = 0,
                status__in = [Bills.PAYED, Bills.DELIVERIED, Bills.FINISHED],
                ).values("payway", "ordertype")
            totalbills = len(bills) # 总订单数
            cashcount = 0 # 现金支付总数
            yuecount = 0 # 余额支付总数
            todaymoney =  0 
            for bill in bills:
                if bill['payway'] in [ZHIFUBAO, WEIXIN] and bill['ordertype'] == Bills.MONEY:
                    cashcount += 1
                elif bill['payway'] == YUE:
                    yuecount += 1
                

            todaymoney = BillSpec.objects.filter(bill__date__gte = today,
                bill__ordertype = Bills.MONEY,
                platform_delete = 0,
                bill__status__in = [Bills.PAYED, Bills.DELIVERIED, Bills.FINISHED]).aggregate(
                    Sum("money")
                )['money__sum'] # 今日订单总金额

            
            totalcoin = BillSpec.objects.filter(
                 bill__ordertype = Bills.COIN,
                 platform_delete = 0,
                 bill__status__in = [Bills.PAYED, \
                     Bills.DELIVERIED, Bills.FINISHED]).count() # 积分订单数

            result['status'] = SUCCESS
            result['msg'] = {
                "totalbills":totalbills,
                "cashcount":cashcount,
                "yuecount":yuecount,
                "todaymoney":todaymoney if todaymoney is not None else 0,
                "totalcoin":totalcoin,
            }
            return HttpResponse(json.dumps(result), content_type='application/json')  


        if 'billuuid' in request.GET : 
            billuuid = request.GET['billuuid'] 
            try:
                bill = Bills.objects.get(platform_delete = 0, uuid = billuuid )
                if 'checkbill' in request.GET:
                    # 查询支付状态
                    check_orders(bill) 
                result['status'] = SUCCESS
                result['msg'] = getbill(bill)
            except Bills.DoesNotExist:
                result['msg'] = "未找到订单信息"
            return HttpResponse(json.dumps(result), content_type="application/json")

        kwargs = {
            "platform_delete" : 0 
        }
        if 'status' in request.GET:
            status = request.GET['status']
            if status != -1 and status != '-1':
                kwargs['status'] = status
            else:
                kwargs['status__in'] = [2,3,4,5]
                 
        else:
            kwargs['status__in'] = [2,3,4,5]
             

        if 'billno' in request.GET:
            billno = request.GET['billno']
            kwargs['billno__icontains'] = billno
        
        if 'username' in request.GET:
            username = request.GET['username']
            kwargs['user__username__icontains'] = username

        
        if 'coinbill' in request.GET:
            coinbill = request.GET['coinbill']
            if int(coinbill) == 1: # 积分订单
                kwargs['ordertype'] = Bills.COIN 
        
        if 'billtype' in request.GET:
            billtype = request.GET['billtype'] 
            kwargs['billtype'] = billtype

        if 'cashbill' in request.GET: # 查询现金账单
            cashbill = request.GET['cashbill']
            if int(cashbill) == 1:
                kwargs['payway__in'] = [ZHIFUBAO, WEIXIN]
                kwargs['ordertype'] = Bills.MONEY
        
        if 'yuebill' in request.GET:
            yuebill = request.GET['yuebill']
            if int(yuebill) == 1:
                kwargs['payway'] = YUE
        
        if 'delivery_way' in request.GET:
            delivery_way = request.GET['delivery_way']
            kwargs['delivery_way'] = delivery_way

        if 'daterange2' in request.GET:
            daterange2 = request.GET['daterange2'].strip() 
            if daterange2:
                daterange_list = daterange2.split("-")
                if len(daterange_list) == 2: 
                    try:
                        startdate = datetime.strptime(daterange_list[0].strip(), "%Y/%m/%d").date()
                        enddate = datetime.strptime(daterange_list[1].strip(), "%Y/%m/%d").date() 
                        kwargs['date__gte'] = startdate
                        kwargs['date__lte'] = enddate
                    except ValueError:
                        pass
                
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
            "user__username",
            "user__phone",
            "receiver_phone",
            "receiver_address",
            "remark",  
            "ordertype",
            "delivery_way",
            "extras" ,
            "status",  
        )[page*pagenum: (page+1)*pagenum])
        for order in orders:
            order['date'] = time.mktime(order['date'].timetuple())
            if order['extras']:
                order['extras'] = json.loads(order['extras'])
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
        发货
        """
        result = {
            "status": ERROR
        }
        user = request.user 
        if not user.is_superuser:
            # 权限不足
            result['msg'] = "权限不足" 
            return HttpResponse(json.dumps(result), content_type='application/json')  
        data  = request.POST
        if 'method' in data:
            method = data['method'].lower()
            if method == 'put':
                return self.put(request)
             
        if 'billuuid' in data and 'express_number' in data \
            and 'express_company' in data: 
            billuuid = data['billuuid'] 
            express_number = data['express_number'].upper()
            express_company = data['express_company']
            try:
                bill = Bills.objects.get(uuid = billuuid )
                if bill.status == bill.PAYED:# 等待发货
                    bill.status = bill.DELIVERIED
                    if express_number.startswith("SF"):
                        express_number = express_number+":"+ bill.receiver_phone[-4:]
                    bill.express_number = express_number
                    bill.express_company = express_company
                    bill.save()
                    result['status'] = SUCCESS
                    result['msg'] = "发货成功" 

                    # 发送通知
                    title = "您的订单已发货"
                    content = "您的订单已发货,点击查看物流状态"
                    appurl = "/pages/order/detail?uuid="+str(bill.uuid)
                    entity_type=  EntityType.BILL
                    send_notice(title = title,
                                content = content,
                                appurl = appurl, 
                                entity_type = entity_type,
                                user = bill.user,
                                msg = True,
                                smstype = "fahuo",
                                phone = bill.user.phone,
                                code = bill.subject,
                                wx = True
                            )
                else: 
                    result['msg'] = "该订单无需发货"
            except Bills.DoesNotExist:
                result['msg'] = "未找到订单信息"
            return HttpResponse(json.dumps(result), content_type="application/json")
        elif   'billuuid' in data and 'status' in data :
            billuuid = data['billuuid'] 
            status = data['status'] 
            try:
                
                bill = Bills.objects.get(uuid = billuuid )  
                bill.status = status
                bill.save()

                result['msg'] = "标记完成"
                result['status']  = SUCCESS
            except Bills.DoesNotExist:
                result['msg'] = "未找到订单信息" 
        elif   'billuuid' in data:
            billuuid = data['billuuid'] 
            try:
                
                bill = Bills.objects.get(uuid = billuuid ) 
                if bill.status == bill.PAYED and bill.delivery_way == 1:
                    # 自提发货
                    bill.status = bill.FINISHED
                    bill.save()
                result['msg'] = "标记完成"
                result['status']  = SUCCESS
            except Bills.DoesNotExist:
                result['msg'] = "未找到订单信息" 
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
                     
                    else:
                        bill.platform_delete = 1
                        bill.save()
                    
            result['status'] = SUCCESS
            result['msg'] = '删除成功'
        else:
            result['status'] = ERROR
            result['msg'] = '缺少ids参数'
        return HttpResponse(json.dumps(result), content_type="application/json")
