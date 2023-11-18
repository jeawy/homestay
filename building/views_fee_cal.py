#! -*- coding:utf-8 -*-
import json
import pdb
import os
import time
from datetime import datetime 
from django.http import HttpResponse
from django.conf import settings
from django.views import View 
from property.code import SUCCESS,  ERROR
from building.comm_fee import fixedfee_calculate, dynamicfee_calculate
from building.models import Room 
from common.logutils import getLogger 
logger = getLogger(True, 'building_fee_order', False)

 
class RoomFeeCalculateView(View):

    def post(self, request):
        """
        物业费计算：
        每个季度前5天重置cal_fee_status字段为NOT_CALCALATED未更新
        每个季度5号之后，更新cal_fee_status字段值为未更新的记录 
        # 不计算非固定收费， 固定费率手动计算
        """
        result = {
            "status": ERROR
        }
        now = datetime.now()
        CAL_DAY = 5
        
        if now.month == 1 or now.month == 4 or now.month == 7 or now.month == 10:
            if now.day < CAL_DAY:
                # 固定费率每季度更新
                # 重置Room的cal_fee_status为NOT_CALCALATED
                Room.objects.all().update(cal_fee_status=Room.NOT_CALCALATED)
        else:
            # 5天之后，更新收费金额, 每次更新1000条
            rooms = Room.objects.filter(cal_fee_status=Room.NOT_CALCALATED,
                                        area__isnull=False,
                                        fixed_fee__isnull=False,
                                        arrearage_start_date__isnull=False
                                        )[:1000]
            for room in rooms:
                fixedfee_calculate(room)
                dynamicfee_calculate(room)

        return HttpResponse(json.dumps(result), content_type="application/json")
