#! -*- coding:utf-8 -*-
import json
import pdb
import uuid
from datetime import datetime 
from django.http import HttpResponse 
from django.utils.translation import ugettext as _
from repair.models import Repair 
from django.core import serializers
from community.models import Community
from appuser.models import AdaptorUser as User 
from common.customjson import  LazyEncoder
from notice.comm import NoticeMgr
from common.request import Code 
from property.code import SUCCESS, ERROR
from django.utils import timezone 
from rest_framework.views import APIView
 
REPAIR = 2 

class RepairView(APIView): 
    def get(self, request):
        content = {} 

        user = request.user
        if 'repair_id' in request.GET:
            repair_id = request.GET['repair_id']
            try:
                if user.organize is not None:
                    repair = Repair.objects.get( property__building__org = user.organize,
                                                 id=repair_id, org_delete = 0)
                else:
                    repair = Repair.objects.get(user=user, id=repair_id, owner_delete=0)

                content['status'] = SUCCESS
                repair_content = {}
                repair_content['building'] = repair.property.building.name + " | " + repair.property.number
                repair_content['facilities'] = repair.facilities
                repair_content['level'] = repair.urgency_level
                repair_content['confirm'] = repair.need_contact
                repair_content['code'] = repair.code
                if repair.phone:
                    repair_content['phone'] = repair.phone
                else:
                    repair_content['phone'] = ''
                if repair.email:
                    repair_content['email'] = repair.email
                else:
                    repair_content['email'] = ''
                if repair.note:
                    repair_content['note'] = repair.note
                else:
                    repair_content['note'] = ''

                if repair.prefertime_start:
                    repair_content['start'] = repair.prefertime_start.strftime("%d/%m/%Y %H:%M:%S")
                else:
                    repair_content['start'] = ''

                if repair.prefertime_end:
                    repair_content['end'] = repair.prefertime_end.strftime("%d/%m/%Y %H:%M:%S")
                else:
                    repair_content['end'] = ''
                repair_content['status'] =  repair.status
                content['msg'] =  repair_content
            except Repair.DoesNotExist:
                content['status'] = ERROR
                content['msg'] = 'Repair does not exist'
                repair = []
           
            return HttpResponse(json.dumps(content), content_type="application/json")
             
        else:
            start = 0
            end = 10
            if 'start' in request.GET and 'end' in request.GET:
                start = request.GET['start']
                end = request.GET['end']
                try:
                    start = int(start)
                    end = int(end)
                except ValueError :
                    pass
            kwargs = {}

            if user.organize is not None:
                kwargs['org_delete'] = 0
                kwargs['property__building__org'] = user.organize
            else:
                kwargs['owner_delete'] = 0
                kwargs['user'] = user

            if 'status' in request.GET :
                status = request.GET['status']
                if status :
                    if  int(status) != -1:
                        kwargs['status'] = status
                try:
                    content['repairstatus'] = int(status)
                except ValueError:
                    pass
            else:
                content['repairstatus'] = -1

            if 'building' in request.GET :
                building = request.GET['building']
                kwargs['property__building__id'] = building
                try:
                    content['buildingid'] = int(building)
                except ValueError:
                    pass

            if 'room' in request.GET :
                room = request.GET['room']
                kwargs['property__number__icontains'] = room
                content['room'] = room

            if 'code' in request.GET :
                code = request.GET['code']
                kwargs['code__icontains'] = code
                content['code'] = code
            if 'datestart' in request.GET:
                datestart = request.GET['datestart'].strip()
                if datestart:
                    try:
                        startdate = datetime.strptime(datestart, "%d-%m-%Y")
                        kwargs['date__gt'] = startdate
                        content['datestart'] = datestart
                    except ValueError:
                        pass

            if 'dateend' in request.GET:
                dateend = request.GET['dateend'].strip()
                if dateend:
                    try:
                        enddate = datetime.strptime(dateend, "%d-%m-%Y")
                        kwargs['date__lt'] = enddate
                        content['dateend'] = dateend
                    except ValueError:
                        pass
            if user.organize is not None:
                repairs = Repair.objects.filter(**kwargs).exclude(status = Repair.CANCEL)
            else:
                repairs = Repair.objects.filter(**kwargs)

            repaire_json = serializers.serialize('json',repairs, cls=LazyEncoder)
            if user.organize is not None:
                repairnum = Repair.objects.filter(property__building__org = user.organize,
                                                  status = Repair.ONGOING,
                                                  org_delete = 0).count()
                  
                content['repairnum'] = repairnum
            content['status'] = SUCCESS

        
        content['msg'] = json.loads(repaire_json)
        return HttpResponse(json.dumps( content),content_type="application/json")
        
    
    def post(self, request):
        """
        新建
        """
        result = {}
        user = request.user
        
        community = None
        if 'communityuuid' in request.POST:
            communityuuid = request.POST['communityuuid'].strip()
            try:
                community = Community.objects.get(uuid = communityuuid) 
            except Community.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = "小区信息不存在"
                return HttpResponse(json.dumps(result), content_type="application/json")

        if 'method' in request.POST:
            method = request.POST['method'].lower()
            if method == 'put':  # 修改
                return self.put(request, community)
            elif method == 'delete':  # 删除
                return self.delete(request, community)

        if  'facility' in request.POST: 
            facility = request.POST['facility'].strip() 
            codestr = datetime.now().strftime('%Y%m%d%H%M%S%f')
            repair = Repair.objects.create(user = user, community = community,
                                            facilities= facility, code = codestr)
            if 'level' in request.POST:
                level = request.POST['level'].strip()
                if level not in repair.level_list():
                    repair.urgency_level = level
                else:
                    print("level  value error:"+str(level))
            if 'starttime' in request.POST:
                starttime = request.POST['starttime'].strip()
                start = datetime.strptime(starttime, "%Y-%m-%d %H:%M:%S")
                repair.prefertime_start = start

            if 'endtime' in request.POST:
                endtime = request.POST['endtime'].strip()
                end = datetime.strptime(endtime, "%Y-%m-%d %H:%M:%S")
                repair.prefertime_end = end

            if 'confirm' in request.POST:
                confirm = request.POST['confirm'].strip()
                if int(confirm) == 1:
                    if 'phone' in request.POST:
                        phone = request.POST['phone'].strip()
                        repair.phone = phone
                    if 'email' in request.POST:
                        email = request.POST['email'].strip()
                        repair.email = email
                    repair.need_contact = 1

            if 'note' in request.POST:
                note = request.POST['note'].strip()
                repair.note = note

            repair.save()

            # 添加通知
            NoticeMgr.create(title =   "新维修单",
                                level = 0, 
                                content = facility,
                                community=community,
                                url='/repair/repair/?uuid='+str(repair.uuid),
                                entity_type=REPAIR, 
                                entity_uuid=repair.uuid)
            # 【待完成】发送短信通知功能待完成
            result['status'] = SUCCESS
            result['msg'] = "已提交"
            result['uuid'] = repair.uuid 
        else:
            result['status'] = ERROR
            result['msg'] = "参数错误" 
        return HttpResponse(json.dumps(result), content_type="application/json")

    def put(self, request, community):
        """
        修改
        """
        result = {}
        user = request.user
        
        
        if 'uuid' in request.POST:
            repairuuid = request.POST['uuid']

            try:  
                owner = False # 标记是否是业主本人
                repair_instance = Repair.objects.get( uuid=repairuuid  )  
                if user == repair_instance:
                    owner = True
                if owner == False and not user.has_community_perm("repair.repair.manage_repair", community):
                    return HttpResponse('Unauthorized', status=401)
                
                if 'replied_note' in request.POST:
                    replied_note = request.POST['replied_note']
                    repair_instance.replied_note = replied_note
                if 'record_date' in request.POST :
                    record_date = request.POST['record_date']
                    repair_instance.record_date = record_date
                if 'record_repairedby' in request.POST :
                    record_repairedby = request.POST['record_repairedby']
                    repair_instance.record_repairedby = record_repairedby

                    
                if 'status' in request.POST :
                    try:
                        status = int(request.POST['status'])
                        if status in repair_instance.status_list():
                            repair_instance.status = status 
                            # 添加通知
                            if status == repair_instance.COMPLETED:
                                # ACCEPTED
                                title = "维修单已完成"
                                notice_detail =  repair_instance.replied_note 
                                # 删除原来的通知
                                NoticeMgr.delete( category=REPAIR, task_id=repair_instance.uuid ) 

                                NoticeMgr.create(user = repair_instance.user,
                                             title = title,
                                             level = 0, 
                                             content = notice_detail,
                                             url='/repair/repair/?uuid=' + str(repair_instance.uuid),
                                             entity_type = REPAIR,
                                            entity_uuid = repair_instance.uuid)
                                
                        else:
                            result['status'] = ERROR
                            result['msg'] = "状态码错误"
                    except ValueError:
                        result['status'] = ERROR
                        result['msg'] = "状态码类型错误"
                repair_instance.save()
                result['status'] = SUCCESS
                result['msg'] = "已保存"
            except Repair.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = "维修单不存在"
        else:
            result['status'] = ERROR
            result['msg'] = "参数错误，缺少uuid"

        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self, request, community):
        """
        删除
        """
        result = {} 
        user = request.user
        if 'repairuuid' in request.POST:
            repairuuid = request.POST['repairuuid']
            try: 
                repair = Repair.objects.get(uuid = repairuuid )
                if user == repair.user:
                    # 发起人本人删除时，可以从数据库删除物业没有处理的，
                    # 如果物业处理了，那么只能将状态设置为owner_delete = 1
                    if repair.status == repair.COMPLETED:
                        repair.owner_delete = 1
                        repair.save()
                    else:
                        repair.delete()
                    
                elif not user.has_community_perm("repair.repair.manage_repair", community):
                    return HttpResponse('Unauthorized', status=401)
                else:
                    repair.org_delete = 1
                    repair.save() 
                result['status'] = SUCCESS
                result['msg'] = "删除成功"
            except Repair.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = "维修单不存在"
         
        else:
            result['status'] = ERROR
            result['msg'] = "参数错误，需要uuid"

        return HttpResponse(json.dumps(result), content_type="application/json")

