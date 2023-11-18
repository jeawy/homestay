
from common.logutils import getLogger
import pdb
import json
import uuid
from django.views import View
from django.db.models import Sum
from datetime import datetime
from community.models import Community
from rest_framework.views import APIView
from django.http import HttpResponse
from property.code import ERROR, SUCCESS
from organize.comm import get_organize_dict, getUserOrganize
from organize.i18 import *
from msg.models import MsgSendRecord
from django.conf import settings
from building.models import Room 
logger = getLogger(True, 'msg', False)
from msg.sms_tempalte import * 
from msg.models import MsgOrders
from common.sms import   send_sms
from msg.comm import get_record
from building.models import RoomReminderRecord


class MsgAnonymousRecordView(View):
    def post(self, request):
        """
        """
        result = {
            "status":SUCCESS
        }
        records = MsgSendRecord.objects.filter(status = MsgSendRecord.NOTSENT)
        for record in records:
            if record.params:
                kwargs = json.loads(record.params ) 
                send_sms(smstype = "fee_require", phone=record.phone, code=None, **kwargs)
                record.status = MsgSendRecord.SENT
                record.save()
        return HttpResponse(json.dumps(result), content_type="application/json")
 
class MsgRecordView(APIView):

    def get(self, request):
        #
        content = {
            "status": SUCCESS,
            "msg": []
        }
        kwargs = {} 
        
        if 'communityuuid' in request.GET:
            communityuuid = request.GET['communityuuid']
            kwargs['community__uuid'] = communityuuid
        
        if 'roomuuid' in request.GET:
            roomuuid = request.GET['roomuuid']
            kwargs['room__uuid'] = roomuuid
        
        if 'roomname' in request.GET:
            roomname = request.GET['roomname']
            kwargs['room__name__icontains'] = roomname


        if 'status' in request.GET:
            status = request.GET['status']
            kwargs['status'] = status
        
        if 'msgtype' in request.GET:
            msgtype = request.GET['msgtype']
            kwargs['msgtype'] = msgtype
        
        if 'phone' in request.GET:
            phone = request.GET['phone']
            kwargs['phone__icontains'] = phone

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
        records = MsgSendRecord.objects.filter(**kwargs)\
            .order_by("-date")[page*pagenum: (page+1)*pagenum]
        total = MsgSendRecord.objects.filter(**kwargs).count()
        content['msg'] = {
            "total": total,
            "records": get_record(records)
        }
        return HttpResponse(json.dumps(content), content_type="application/json")

    def post(self, request):
        """ 
        发送短信
        """
        result = {
            'status': ERROR
        }
        user = request.user 
        data = request.POST
        
        if 'template_sms' in data:
            # 获取短信模板 
            if 'roomuuids' in data and 'communityuuid' in data:
                #  批量发送物业费缴费提醒短信
                roomuuids = json.loads( data['roomuuids'])
                communityuuid = data['communityuuid'].strip() 
                sms_content_ls = []
                printTemplate = False
                if 'print' in data:
                    # 打印
                    printTemplate = True
                try:
                    community = Community.objects.get(uuid = communityuuid) 
                    if community.organize:  
                        orguuids = getUserOrganize(user)
                        if community.organize.uuid in orguuids:
                            rooms = Room.objects.filter(uuid__in=roomuuids,
                                            owner__isnull=False, fee_status = Room.ARREARAGED)
                                
                            smscontent = ""
                            for room in rooms: 
                                # 短信内容 
                                if printTemplate:
                                    smscontent = PRINT_TEMPLATE_FEE.format(
                                        room.owner.username, 
                                        community.name,
                                        room.name, 
                                        str(room.arrearage)+"元" if room.arrearage is not None else "", 
                                    
                                    )
                                    sms_content_ls.append( {
                                        "username":room.owner.username, 
                                        "roomname":room.name, 
                                        "communityname":community.name, 
                                        "organize":community.organize.alias, 
                                        "content":smscontent,
                                        "date":datetime.now().strftime("%Y/%m/%d")
                                    })
                                else:
                                    smscontent = SMS_TEMPLATE_FEE.format(
                                        room.owner.username, 
                                        community.name,
                                        room.name, 
                                        str(room.arrearage) if room.arrearage is not None else "",  
                                        community.organize.alias, 
                                    )
                                    sms_content_ls.append( smscontent)
                            result['msg'] = {
                                "sms_content_ls":sms_content_ls,
                                "number":len(sms_content_ls),# 发送短信的数量,
                                "detail":"提交共{0}条，实际可发送{1}条".format(
                                    str(len(roomuuids)),
                                    str(len(sms_content_ls)))
                            }
                            result['status'] = SUCCESS
                             
                except Community.DoesNotExist:
                    result['status'] = ERROR # 引导前端弹出充值界面
                    result['msg'] = "未找到相关小区信息"
            
            return HttpResponse(json.dumps(result), content_type="application/json")

        if 'method' in data:
            method = data['method'].lower().strip()
            if method == 'put':  # 修改
                return self.put(request)
            if method == 'delete':  # 删除
                return self.delete(request)

        if 'roomuuids' in data and 'communityuuid' in data:
            #  批量发送物业费缴费提醒短信
            roomuuids = json.loads(data['roomuuids'])
            communityuuid = data['communityuuid'].strip()
            
            try:
                community = Community.objects.get(uuid = communityuuid) 
                if community.organize:  
                    rooms = Room.objects.filter(uuid__in=roomuuids,
                                        owner__isnull=False, 
                                        fee_status = Room.ARREARAGED)
                    length = len(rooms) 
                    if  community.msg_left < length:
                        # 短信余额不足，请充值
                        result['status'] = 2 # 引导前端弹出充值界面
                        result['msg'] = "短信余额不足，请充短信"
                    else: 
                        if length > 1:
                            # 超过1条短信异步发送, 24小时内发送完毕
                            for room in rooms:
                                phone = room.owner.phone
                                # 短信内容
                                sms_content = SMS_TEMPLATE_FEE.format(
                                    room.owner.username, 
                                    community.name,
                                    room.name, 
                                    str(room.arrearage)  if room.arrearage is not None else "", 
                                    community.organize.alias, 
                                )
                                kwargs = {
                                    "smsSignId":community.smsSignId,
                                    "username":room.owner.username, 
                                    "position":community.name,
                                    "room":room.name, 
                                    "money":str(room.arrearage)  if room.arrearage is not None else ""
                                }
                                msgrecord = MsgSendRecord()
                                msgrecord.user = user 
                                msgrecord.org = community.organize
                                msgrecord.community = community
                                msgrecord.phone = phone
                                msgrecord.room = room
                                msgrecord.message = sms_content
                                msgrecord.status = msgrecord.NOTSENT
                                msgrecord.params = json.dumps(kwargs)
                                msgrecord.save() 

                                rrrecord = RoomReminderRecord()
                                rrrecord.uuid = uuid.uuid4()
                                rrrecord.room = room
                                rrrecord.user = user
                                rrrecord.reminder_date = msgrecord.date
                                rrrecord.detail = sms_content
                                rrrecord.reminder_type = rrrecord.MESSAGE
                                rrrecord.save()

                            result['status'] = SUCCESS
                            result['msg'] = "缴费提醒短信共{0}条，24小时内发送完毕".format(str(length))
                        elif len(rooms) == 1:
                            # 立即发送 
                            phone = rooms[0].owner.phone
                            # 短信内容
                            sms_content = SMS_TEMPLATE_FEE.format(
                                rooms[0].owner.username, 
                                community.name,
                                rooms[0].name, 
                                str(rooms[0].arrearage) ,
                                community.organize.alias, 
                            )
                            # 短信发送记录
                            msgrecord = MsgSendRecord()
                            msgrecord.user = user 
                            msgrecord.org = community.organize
                            msgrecord.community = community
                            msgrecord.phone = phone
                            msgrecord.room = rooms[0]
                            msgrecord.message = sms_content
                            msgrecord.status = msgrecord.SENT
                            msgrecord.save()
 

                            # 提醒记录
                            rrrecord = RoomReminderRecord()
                            rrrecord.uuid = uuid.uuid4()
                            rrrecord.room = rooms[0]
                            rrrecord.user = user
                            rrrecord.reminder_date = msgrecord.date
                            rrrecord.detail = sms_content
                            rrrecord.reminder_type = rrrecord.MESSAGE
                            rrrecord.save()
                             # 短信内容 
                            kwargs = {
                                "smsSignId":community.smsSignId,
                                "username":rooms[0].owner.username,
                                "position":community.name,
                                "room":rooms[0].name, 
                                "money":str(rooms[0].arrearage) 
                            }

                            send_sms(smstype="fee_require", 
                            phone = phone,
                            code = None,  **kwargs)
                            result['status'] = SUCCESS
                            result['msg'] = "已发送"
                        else:
                            result['msg'] = "未找到满足条件：1绑定了业主、2房产处于欠费状态的房产，发送短信0条"
                        
                else: 
                    result['msg'] = "小区{0}未设置物业信息，不能发送缴费短信".format(community.name)  
            except Community.DoesNotExist: 
                result['msg'] = "确实roomuuids和communityuuid字段"  
        else: 
            result['msg'] = "确实roomuuids和communityuuid字段"
        return HttpResponse(json.dumps(result), content_type="application/json")
