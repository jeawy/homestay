#! -*- coding:utf-8 -*-
from ast import Add
import imp
import json
import pdb
import os
import uuid
import time
from datetime import datetime 
from django.http import HttpResponse
from django.conf import settings
from django.views import View 
from pay.wxpayV3 import WeixinPay
from property.code import SUCCESS,  ERROR 
from property.code import ZHIFUBAO, WEIXIN
from card.models import Card   
from rest_framework.views import APIView
from common.logutils import getLogger 
from property.entity import EntityType
logger = getLogger(True, 'card', False)
from common.sms import send_sms   
from bills.models import BillSpec
from notice.comm import NoticeMgr
from card.comm import get_left_money


class CardView(APIView):
    """ 
    """ 
    def get(self, request):
        # 业主获取自己的账单
        result = {
            "status": ERROR
        }
        user = request.user
        if 'mine' in request.GET: 
            result['msg'] =  get_left_money(user)
            result['status'] = SUCCESS
            return HttpResponse(json.dumps(result), content_type='application/json')  
 
        if 'billuuid' in request.GET and 'status' in request.GET:
            # 获取订单总金额
            billuuid = request.GET['billuuid'].strip()
            try:
                card = Card.objects.get(uuid = billuuid)
                result['status'] = SUCCESS
                money = 0
                specs = BillSpec.objects.filter(card = card)
                for spec in specs:
                    money += spec.number * spec.price
                money = float(money)
                result['msg'] = {
                    'status':card.status,
                    'billno':card.billno,
                    'money':money} 
            except Card.DoesNotExist:
                result['msg'] = "未找到订单信息"
            return HttpResponse(json.dumps(result), content_type="application/json")
        
        elif 'billuuid' in request.GET :
            # 获取订单详情
            billuuid = request.GET['billuuid']
            try:
                card = Card.objects.get(uuid = billuuid, user = user)
                result['status'] = SUCCESS
                result['msg'] = getbill(card)
            except Card.DoesNotExist:
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

        
        if 'tag' in request.GET:
            tag = int(request.GET['tag'])
            if tag == 1:
                # 已使用完的购物卡
                kwargs['left'] = 0
                kwargs['status'] = Card.ACTIVATED
             
        kwargs['user'] = user 
              
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

        total = Card.objects.filter(**kwargs).count() 

        cards = list(Card.objects.filter(**kwargs).values(
            "uuid", 
            "cardtype",
            "date",
            "money", 
            "left",
            "status",   
        )[page*pagenum: (page+1)*pagenum])
         
        for card in cards:
            card['date'] = time.mktime(card['date'].timetuple())     
        result['status'] = SUCCESS
        result['msg'] = {
                            "total": total,
                            "cards": cards
                        }  
        return HttpResponse(json.dumps(result), content_type='application/json')  
 
    def post(self, request):
        """
        # 绑卡、激活
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

        if 'password' in data and 'bind' in data: 
            password = data['password'] 
            try:
                card = Card.objects.get(password = password)
                if card.status != card.SALLED:
                    if card.status == card.UNSALLED:
                        result['msg'] = "该卡未出售"
                    elif card.status == card.BIND:
                        result['msg'] = "等待激活"
                    elif card.status == card.ACTIVATED:
                        result['msg'] = "该卡已激活"
                else:
                    card.status = card.BIND # 等待激活
                    card.user = user
                    card.save() 
                    # 发送通知及短信
                    content = "有新的购物卡等待激活"
                    NoticeMgr.create(
                                    title = "请激活购物卡",
                                    content = content, 
                                    appurl = "/pages/card/list?uuid="+str(carduuid),
                                    entity_type=  EntityType.CARD
                                )
                    for phone in settings.MANAGERS_PHONES:
                        send_sms(smstype="card", phone=phone )
                    result['msg'] = "请等待激活"
                    result['status'] = SUCCESS
            except Card.DoesNotExist:
                result['msg'] = "卡密错误"

        elif 'carduuid' in data and 'bind' in data:  
            # 绑卡或者激活 
            carduuid = data['carduuid']
            try:
                card = Card.objects.get(uuid = carduuid)  
                if 'password' in data:
                    # 绑定新卡:通过卡密导入
                    password = data['password']
                    if card.password != password:
                        result['msg'] = "卡密错误"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    if card.status != card.SALLED:
                        if card.status == card.UNSALLED:
                            result['msg'] = "该卡未出售"
                        elif card.status == card.BIND:
                            result['msg'] = "等待激活"
                        elif card.status == card.ACTIVATED:
                            result['msg'] = "该卡已激活"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                elif 'getpassword' in data:
                    # 获取卡密
                    if BillSpec.objects.filter(
                        bill__user = user,
                            card__uuid = carduuid
                        ).count() > 0: 
                        # 只能获取自己订单中的卡密
                        int_time = int(time.time())
                        if 'time' in request.session: 
                            old_int_time = request.session['time']
                            request.session['time'] = int_time
                            if int_time - old_int_time < 60:  # 60秒，频率太高
                                result['status'] = ERROR
                                result['msg'] = "勿频繁操作"  # u'操作频率太快...'
                                return HttpResponse(json.dumps(result), content_type="application/json")
                            else:
                                send_sms(smstype = "getpassword", 
                                   phone=user.phone, code=card.password) 
                        else:
                            old_int_time = 0
                            send_sms(smstype = "getpassword", 
                                   phone=user.phone, code=card.password) 
                            request.session['time'] = int_time 
                        result['msg'] = "卡密已发送"
                        result['status'] = SUCCESS 
                    else:
                        result['msg'] = "卡密错误" 
                else:
                    # 绑定自己的卡
                    try:
                        BillSpec.objects.get(bill__user = user,
                        card = card) 
                        if card.status != card.SALLED:
                            if card.status == card.UNSALLED:
                                result['msg'] = "该卡未出售"
                            elif card.status == card.BIND:
                                result['msg'] = "等待激活"
                            elif card.status == card.ACTIVATED:
                                result['msg'] = "该卡已激活"
                            return HttpResponse(json.dumps(result), content_type="application/json") 
                    except BillSpec.DoesNotExist:
                        result['msg'] = "未找该购物卡"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                
                card.status = card.BIND # 等待激活
                card.user = user
                card.save()

                # 发送通知及短信
                content = "有新的购物卡等待激活"
                NoticeMgr.create(
                                title = "请激活购物卡",
                                content = content, 
                                appurl = "/pages/card/list?uuid="+str(carduuid),
                                entity_type=  EntityType.CARD
                            )
                for phone in settings.MANAGERS_PHONES:
                    send_sms(smstype="card", phone=phone )
                result['msg'] = "请等待激活"
                result['status'] = SUCCESS
            except Card.DoesNotExist:
                result['msg'] = "未找该购物卡"
        else:
            # 激活卡片
            if not user.is_superuser :
                # 只有管理员可以激活
                return HttpResponse("无权限", status=401)        
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
                    card = Card.objects.get(user = user, uuid = uuiditem)
                except Card.DoesNotExist:
                    continue
                else:
                    # 删除礼品时删除磁盘中对应的图片和轮播图文件
                    if card.status == card.NON_PAYMENT:
                         
                        # 还要进行退库
                        # 存入redis队列
                        myredis = RedisSubscri()
                        redisconn = myredis.getconn()
                        # uuid和操作标识符，1表示减库存 操作也就是下单，0表示退库操作
                        redisconn.lpush("card", card.uuid+",0") # 发布到队列中
                        print(myredis.publish("consumer", "card")) # 通知订阅者进行消费，更新库存
 
                    card.owner_delete = 1
                    card.save()
                    
            result['status'] = SUCCESS
            result['msg'] = '删除成功'
        else:
            result['status'] = ERROR
            result['msg'] = '缺少ids参数'
        return HttpResponse(json.dumps(result), content_type="application/json")


