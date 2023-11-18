#! -*- coding:utf-8 -*-
import json
import pdb
import time
import os

from datetime import datetime 
from django.http import HttpResponse 
from django.views import View 
from appuser.models import AdaptorUser as User
from property.entity import EntityType
from rest_framework.views import APIView 
from property import settings
from property.code import SUCCESS, ERROR 
from aid.models import AidOrders, Aid
from building.models import RoomFeeOrders
from paidservice.models import PaidOrder
from common.logutils import getLogger  
from incomes.comm import statisticsMoney
from withdraw.models import WithDraw
logger = getLogger(True, 'incomes', False)


class IncomesView(APIView): 
    """
    收支接口
    思维导图:https://www.processon.com/mindmap/618b72cd1e0853689b03e663
    """
    def get(self, request):
        content = { }
        user = request.user
       
        if 'total' in request.GET:
            # 单个业主的收支总和
            # 收入：提供的帮助
            logger.debug("开始计算收支费用:"+str(datetime.now()))
            income_total,expend_total,left = statisticsMoney(user)
            content = {
                      "status":SUCCESS,
                      "msg":{
                          "income_total":round(income_total, 2),
                          "expend_total":round(expend_total, 2),
                          "left":round(left, 2),
                      }      
              }
            logger.debug("结束计算收支费用:"+str(datetime.now()))

        elif "page" in request.GET and "pagenum" in request.GET:
            pagenum = request.GET['pagenum']
            page = request.GET['page']
            keyword = None
            if 'keyword' in request.GET:
                keyword = request.GET['keyword'].strip()
                
            try:
                page = int(page) - 1
                pagenum = int(pagenum)
            except ValueError:
                page = 0
                pagenum = settings.PAGE_NUM
            if 'entity_type' in request.GET and 'incomes' in request.GET:
                # 收支接口
                kwargs = {} 
                entity_type = request.GET['entity_type'] 
                incomes = request.GET['incomes'] 
                try:
                    entity_type = int(entity_type)  
                    incomes = int(incomes)  
                except ValueError:
                    content['status'] = ERROR
                    content['msg'] = "entity_type或者incomes参数不是int"
                    return HttpResponse(json.dumps(content), content_type="application/json")
                
                if entity_type == EntityType.FEE:
                    # 物业费账单
                    if incomes == 0: #支出
                        kwargs={} 
                        kwargs['status'] = RoomFeeOrders.PAYED
                        kwargs['user'] = user 
                        if keyword:
                            kwargs['feename__icontains'] = keyword 
                        fees = list(RoomFeeOrders.objects.filter(**kwargs).order_by('-date')[page * pagenum: (page + 1) * pagenum]\
                            .values("date","detail", "money", 
                            "community__name", "feename"))
                        for fee in fees:
                            fee['date'] = time.mktime(fee['date'].timetuple())
                        content['status'] = SUCCESS
                        content['msg'] = fees
                        return HttpResponse(json.dumps(content), content_type="application/json")
                elif  entity_type == EntityType.AID:   
                    # 邻里互助 
                    if incomes == 0: #支出
                        kwargs={} 
                        kwargs['status'] = AidOrders.PAYED
                        kwargs['user'] = user  
                        if keyword:
                            kwargs['aid__title__icontains'] = keyword  
                        aids = list(AidOrders.objects.filter(**kwargs).order_by('-date')[page * pagenum: (page + 1) * pagenum]\
                            .values("date","aid__title", "money","subject", 
                            "community__name"))
                        for aid in aids:
                            aid['date'] = time.mktime(aid['date'].timetuple())
                        content['status'] = SUCCESS
                        content['msg'] = aids
                    elif incomes == 1: # 收入
                        kwargs={}
                        kwargs['aid__answer'] = user
                        kwargs['status'] = AidOrders.PAYED
                        kwargs['aid__status__gte'] = Aid.ACCEPTED # 已完成的订单
                        if keyword:
                            kwargs['aid__title__icontains'] = keyword 
                        aidorders = list(AidOrders.objects.filter(**kwargs).order_by('-date')[page * pagenum: (page + 1) * pagenum].values(
                            "date",
                            "aid__title",
                            "money",
                            "aid__community__name",
                            "aid__community__aid_commission_rate"))
                        for aidorder in aidorders:
                            aidorder['date'] = time.mktime(aidorder['date'].timetuple()) 
                            aidorder['mymoney'] = round(aidorder['money'] * (1 - aidorder['aid__community__aid_commission_rate']), 2)
                        
                        content['status'] = SUCCESS
                        content['msg'] = aidorders
                elif  entity_type == EntityType.PAIDSERVICE:   
                    # 有偿服务  
                    if incomes == 0: #支出
                        kwargs={} 
                        kwargs['status'] = PaidOrder.PAYED
                        kwargs['user'] = user  
                        if keyword:
                            kwargs['subject__icontains'] = keyword 
                        paidservices = list(PaidOrder.objects.filter(**kwargs).order_by('-date')[page * pagenum: (page + 1) * pagenum]\
                            .values("date","subject", "money", 
                            "community__name"))
                        for paidservice in paidservices:
                            paidservice['date'] = time.mktime(paidservice['date'].timetuple())
                        content['status'] = SUCCESS
                        content['msg'] = paidservices
                else:
                    content['status'] = ERROR
                    content['msg'] = "参数错误"
            else: #提现 
                kwargs={}  
                kwargs['user'] = user
                withdraws = WithDraw.objects.filter(**kwargs)\
                    .order_by('-date')[page * pagenum: (page + 1) * pagenum]\
                        .values("date","money", "status", "remark")
                for withdraw in withdraws:
                    withdraw['date'] = time.mktime(withdraw['date'].timetuple())
                content['status'] = SUCCESS 
                content['msg'] = withdraws
        else:
            content['status'] = ERROR
            content['msg'] = "参数错误123" 
        return HttpResponse(json.dumps(content), content_type="application/json")
         
   