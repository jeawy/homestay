#! -*- coding:utf-8 -*-
import json
import pdb
import os
import time
from django.http import HttpResponse
from django.conf import settings
from property.code import SUCCESS,  ERROR 
from building.models import Room
from community.models import Community
from aid.models import AidOrders
from property.billno import get_fee_bill_no
from rest_framework.views import APIView
from common.logutils import getLogger
logger = getLogger(True, 'aid_order', False)


class AidOrderView(APIView):
    """ 
    """

    def get(self, request):
        result = {
            "status": ERROR
        }
        user = request.user
        community = None
        if 'communityuuid' in request.GET:
            communityuuid = request.GET['communityuuid']
            try:
                community = Community.objects.get(uuid=communityuuid)
            except Community.DoesNotExist:
                result['msg'] = "未找到小区信息"
                return HttpResponse(json.dumps(result), content_type="application/json")

            if 'billno' in request.GET:
                # 获取订单总金额
                billno = request.GET['billno']
                try:
                    bill = AidOrders.objects.get(billno=billno)
                    result['status'] = SUCCESS
                    result['msg'] = bill.money
                except AidOrders.DoesNotExist:
                    result['msg'] = "未找到订单信息"
                return HttpResponse(json.dumps(result), content_type="application/json")
            
           
        else:
            result['msg'] = "缺少community uuid"
        return HttpResponse(json.dumps(result), content_type="application/json")

    def post(self, request):
        """
         
        """
        result = {
            "status": ERROR
        }
        user = request.user
        if 'roomuuid' in request.POST:
            # 提交物业费订单
            roomuuid = request.POST['roomuuid']
            communityuuid = request.POST['communityuuid']
            try:
                room = Room.objects.get(uuid=roomuuid)
                if room.arrearage_start_date is None:
                    result['msg'] = "起始计费日期未设置"
                    return HttpResponse(json.dumps(result), content_type="application/json")

                if room.arrearage_end_date is None:
                    result['msg'] = "结束计费日期未设置"
                    return HttpResponse(json.dumps(result), content_type="application/json")

                community = room.unit.building.community
                org = community.organize
                detail = room.arrearage_start_date.strftime(
                    settings.DATEFORMAT)
                detail += "至" + \
                    room.arrearage_end_date.strftime(settings.DATEFORMAT)
                detail += "物业费：" + str(room.money) + "元"
                subject = "【{0}】{1}{2}{3}物业费".format(org.alias, room.unit.building.name,
                                                     room.unit.name, room.name)
                billno = get_fee_bill_no(org, user, "F")  # F for 固定性收费
                money = room.arrearage

            except Room.DoesNotExist:
                result['msg'] = "未找到对应房屋信息"
        elif 'dynamicfeeuuid' in request.POST:
            # 提交非固定收费订单

            result['msg'] = "参数错误"
        return HttpResponse(json.dumps(result), content_type="application/json")


 