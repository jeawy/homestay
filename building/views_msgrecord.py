#! -*- coding:utf-8 -*-
from building.comm import create_asset
import json
import pdb
import os
import traceback
import time
import uuid
from datetime import datetime
import operator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils.translation import ugettext as _
from appuser.models import AdaptorUser as User
from django.conf import settings
from building.models import Building, Room, Unit
from rest_framework.views import APIView
from property.code import SUCCESS,  ERROR
from common.logutils import getLogger
from common.utils import verify_phone
from community.models import Community
from building.comm import get_room_detail, get_single_room_dict
from building.comm import varify_data, get_msgrecord_dict
from fee.models import FixedFee, DynamicFee
from building.models import RoomReminderRecord
logger = getLogger(True, 'building', False)


class MsgRecordView(APIView):
    """
    催缴记录：短信和上门催缴
    """
    def get(self, request):
        """
        谁可以获取：物业、超级管理员
        """
        result = {
            'status': SUCCESS,
        }
        kwargs = {}
        if 'roomuuid' in request.GET:
            roomuuid = request.GET['roomuuid']
            kwargs['room__uuid'] = roomuuid
             
        
        if 'start' in request.GET and 'end' in request.GET:
            start = request.GET['start']
            end = request.GET['end']
            start_date = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
            end_date = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
            kwargs['reminder_date__gte'] = start_date
            kwargs['reminder_date__lte'] = end_date
             
        records = RoomReminderRecord.objects.filter(**kwargs) 
             
        result['msg'] = get_msgrecord_dict(records)  
        result['status'] = SUCCESS
        return HttpResponse(json.dumps(result), content_type='application/json')

    def post(self, request):
        """
        新建
        """
        result = {
            "status": ERROR
        }
        user = request.user
        community = None
        if 'communityuuid' in request.POST:
            communityuuid = request.POST['communityuuid']
            try:
                community = Community.objects.get(uuid=communityuuid) 
            except Community.DoesNotExist:
                result['msg'] = '未找到楼号'
                return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['msg'] = '缺少参数community uuid'
            return HttpResponse(json.dumps(result), content_type="application/json")

        
        # 验证是否有权限
        if not user.has_community_perm('building.building.manage_building', community):
            return HttpResponse('Forbidden', status=403)

        
        if 'roomuuid' in request.POST and 'detail' in request.POST:
            roomuuid = request.POST['roomuuid'].strip()
            detail = request.POST['detail'].strip()
            
            try:
                room = Room.objects.get( uuid=roomuuid ) 
                rrrecord = RoomReminderRecord()
                if 'reminder_date' in request.POST:
                    reminder_date = request.POST['reminder_date']
                    reminder_date = datetime.strptime(reminder_date, "%Y-%m-%d %H:%M:%S")
                    rrrecord.reminder_date =  reminder_date
                rrrecord.uuid = uuid.uuid4()
                rrrecord.room = room 
                rrrecord.user = user
                rrrecord.detail = detail
                rrrecord.reminder_type = rrrecord.VISITED
                rrrecord.save() 
                result['status'] = SUCCESS
                result['msg'] = '已完成'
            except Room.DoesNotExist: 
                result['msg'] = '未找到楼号' 
        else:
            result['msg'] = 'Need roomuuid, detail in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")
  