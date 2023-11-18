#! -*- coding:utf-8 -*-  
import json
import pdb
import os
import uuid
import time
from datetime import datetime 
from django.http import HttpResponse
from django.conf import settings 
from property.code import SUCCESS,  ERROR  
from card.models import Card   
from rest_framework.views import APIView
from common.logutils import getLogger 
from property.entity import EntityType
logger = getLogger(True, 'card', False)
from common.sms import send_sms    
from notice.comm import NoticeMgr 


class CardAdminView(APIView):
    """ 
    """ 
    def get(self, request):
        # 平台管理员
        result = {
            "status": ERROR
        }
        user = request.user
        if not user.is_superuser :
            # 只有管理员可以激活
            return HttpResponse("无权限", status=401)  
        kwargs = {}
        if 'status' in request.GET:
            status = request.GET['status']
            if status == -1 or status == '-1':
                kwargs['status__in'] = [Card.BIND, Card.ACTIVATED]
            else:
                kwargs['status'] = status
        else:
            # 默认获取待激活的卡
            kwargs['status'] = Card.BIND
        if 'cardtype' in request.GET:
            cardtype = request.GET['cardtype']
            kwargs['cardtype'] = cardtype
        
        if 'username' in request.GET:
            username = request.GET['username']
            kwargs['user__username__icontains'] = username
             
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
            "status",
            "cardtype",
            "money",
            "left",
            "date",  
            "user__uuid",
            "user__username",
            "user__thumbnail_portait",
            "activedate",
            "saledate"
        )[page*pagenum: (page+1)*pagenum])

        for card in cards:
            card['date'] = time.mktime(card['date'].timetuple())
            if card['activedate']:
                card['activedate'] = time.mktime(card['activedate'].timetuple())
            if card['saledate']:
                card['saledate'] = time.mktime(card['saledate'].timetuple())
                
        result['status'] = SUCCESS
        result['msg'] = {
                            "total": total,
                            "cards": cards
                        }  
        return HttpResponse(json.dumps(result), content_type='application/json')  
 
    def post(self, request):
        """
        #  激活
        """
        result = {
            "status": ERROR
        }
        user = request.user 
        data  = request.POST

        if not user.is_superuser :
            # 只有管理员可以激活
            return HttpResponse("无权限", status=401)  
        
        
        if 'carduuid' in data  :  
            # 激活，只有超级管理员可以激活卡
            carduuid = data['carduuid']
            try:
                card = Card.objects.get(uuid = carduuid)   
                if card.status != card.BIND:
                    if card.status == card.UNSALLED:
                        result['msg'] = "该卡未出售"
                    elif card.status == card.SALLED:
                        result['msg'] = "卡片未绑定用户"
                    elif card.status == card.ACTIVATED:
                        result['msg'] = "该卡已激活"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                
                card.status = card.ACTIVATED # 
                card.manager = user
                card.left = card.money
                card.activedate = datetime.now()
                card.save()

                # 发送通知及短信
                content = "您的购物卡已激活，祝您购物愉快."
                NoticeMgr.create(
                                title = "您的购物卡已激活",
                                content = content, 
                                user = card.user,
                                appurl = "/pages/card/cards",
                                entity_type=  EntityType.CARD
                            )
                 
                send_sms(smstype="cardactivate", phone=card.user.phone )
                result['msg'] = "已激活"
                result['status'] = SUCCESS
            except Card.DoesNotExist:
                result['msg'] = "未找该购物卡"
        else:
            # 批量导入实体购物卡
            cards_json = request.data  
            result = {}
            content = {}
            # 创建消息列表
            msg_list = []
            # 创建批量添加失败,成功数
            fail_num = 0
            success_num = 0
            # 迭代次数与数据索引
            i = 0
            # 获取请求数据并以json格式进行解析
             
            # 获取数据中的keys-values
            keys_data = cards_json["keys"]
            values_data = cards_json["values"]
            for value_data in values_data:
                i += 1
                password_index = keys_data.index("password")
                password = value_data[password_index]

                money_index = keys_data.index('money')
                money = value_data[money_index]

                if len(password) != 12: 
                    # 长度错误
                    fail_num += 1 
                    msg_list.append("第{0}条的错误信息(卡密:{1},金额:{2})是{3}<br/>".\
                        format(i, password,money,  "卡密长度错误"))
                    continue
                
                try: 
                    money = int(money)
                    if money < 100:
                        # 金额错误
                        fail_num += 1 
                        msg_list.append("第{0}条的错误信息(卡密:{1},金额:{2})是{3}<br/>".\
                        format(i, password,money,  "金额不能小于100"))
                        continue
                except ValueError:
                    # 金额错误
                    fail_num += 1 
                    msg_list.append("第{0}条的错误信息(卡密:{1},金额:{2})是{3}<br/>".\
                        format(i, password,money,  "金额错误"))
                    continue
                try:
                    card = Card.objects.get(password = password)
                    
                    # 卡密重复
                    fail_num += 1
                    msg_list.append("第{0}条的错误信息(卡密:{1},金额:{2})是{3}<br/>".format(i, password,money,  "卡密重复"))
                    continue

                except Card.DoesNotExist:
                    
                    Card.objects.create(password = password, 
                        money = money, cardtype = Card.REAL, 
                        uuid = str(uuid.uuid4()))
                    success_num += 1
                     
            result['status'] = SUCCESS if success_num + fail_num == i else ERROR
            result['msg'] = msg_list
            result['success_num'] = success_num
            result['fail_num'] = fail_num

       
        return HttpResponse(json.dumps(result), content_type="application/json")
 