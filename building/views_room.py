#! -*- coding:utf-8 -*- 
import json
import pdb
import os 
import time
import uuid
from datetime import datetime
from django.db.models import Q 
from django.http import HttpResponse
from django.utils.translation import ugettext as _
from appuser.models import AdaptorUser as User
from django.conf import settings
from building.models import Building, Room, Unit, RoomDynamicFeeDetail
from rest_framework.views import APIView
from property.code import SUCCESS,  ERROR
from common.logutils import getLogger
from common.utils import verify_phone
from community.models import Community
from community.comm import getUserCommunities
from building.models import RoomFeeOpHistory
from building.comm_history import add_history
from building.comm import get_room_detail, get_single_room_dict, get_room_feestatus_txt
from building.comm import varify_data
from building.comm_fee import single_dynamicfee_calculate, fixedfee_calculate
from fee.models import FixedFee, DynamicFee

logger = getLogger(True, 'building', False)


class RoomView(APIView):
    def get(self, request):
        """
        谁可以获取：物业、超级管理员
        """
        result = {
            'status': SUCCESS,
        }
        kwargs = {}
        user = request.user

        if 'minerooms' in request.GET:
            # 获取我的房产
            rooms = list(Room.objects.filter(owner = user).values("name", "area",
            "unit__name", "unit__building__name", 
            "community__name", 
            "community__shequ", 
            "community__jiedaoban", 
            "community__organize__alias", 
            "community__organize__logo", 
            "community__tel", 
            "community__uuid",  
            ))
            result['msg'] = rooms
            return HttpResponse(json.dumps(result), content_type="application/json")
            

        if 'roomuuid' in request.GET and 'communityuuid' in request.GET:
            roomuuid = request.GET['roomuuid']
            communityuuid = request.GET['communityuuid']
            try:
                room = Room.objects.get(uuid=roomuuid,
                                        community__uuid=communityuuid)
                # 如果已欠费，并且应缴费日期小于当前日期，且没有未支付的物业费账单，
                # 则创建一个物业费账单，并更新房屋的应缴费金额
                fixedfee_calculate(room)
                result['msg'] = get_room_detail(room)
            except Room.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = "未找到对应房屋信息"
            return HttpResponse(json.dumps(result), content_type="application/json")

        fee = False
        if 'fee' in request.GET:
            fee = True
        if 'uuid' in request.GET and 'level' in request.GET:
            assetuuid = request.GET['uuid']
            level = int(request.GET['level'])
            if level == 1:
                kwargs['unit__building__uuid'] = assetuuid
            else:
                kwargs['unit__uuid'] = assetuuid
        if 'name' in request.GET:
            name = request.GET['name']
            kwargs['name__icontains'] = name
        
        if 'username' in request.GET:
            username = request.GET['username']
            kwargs['owner__username__icontains'] = username

        if 'fee_status' in request.GET:
            # 表示业主已欠费
            fee_status = request.GET['fee_status']
            kwargs['fee_status'] = fee_status
 
        if 'communityuuid' in request.GET:
            communityuuid = request.GET['communityuuid']
            kwargs['community__uuid'] = communityuuid
        
        if 'communityuuids' in request.GET:
            # 首页获取相关统计接口
            communityuuids = getUserCommunities(user)
            kwargs['community__uuid__in'] = list(communityuuids)
            # 仅获取未设置过催缴记录的
            kwargs['press_fee'] = 0
            

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

        qfilter = None
        if 'cannot_cal_fee' in request.GET:
            # 查询所有无法计算物业费的房产信息  
            qfilter = Q(fixed_fee__isnull = True)|Q(arrearage_start_date__isnull = True)|Q(area__isnull = True)
        
        if 'unbinderoomer' in request.GET:
            # 点击筛选出所有未绑定业主的房产  
            if qfilter is not None:
               qfilter &= Q(owner__isnull = True) 
            else:
               qfilter = Q(owner__isnull = True) 
        if qfilter is None:
            total = Room.objects.filter(**kwargs ).count() 
            rooms = Room.objects.filter(**kwargs)[page*pagenum: (page+1)*pagenum]
        else:
            total = Room.objects.filter(Q(**kwargs), qfilter).count() 
            rooms = Room.objects.filter(Q(**kwargs), qfilter)[page*pagenum: (page+1)*pagenum]
         
        room_ls = []
        for room in rooms:
            room_ls.append(get_single_room_dict(room, fee))
        result['msg'] = {
            "total": total,
            "rooms": room_ls
        }
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

        # 新建 
        if 'method' in request.POST:
            method = request.POST['method'].lower()
            if method == 'put':  # 修改
                return self.put(request)
            elif method == 'delete':  # 删除
                return self.delete(request)

        if 'name' in request.POST:
            name = request.POST['name'].strip()
            
            if 'buildinguuid' in request.POST:
                buildinguuid = request.POST['buildinguuid']
                # 新建单元号
                try:
                    unit = Unit.objects.get(
                        building__uuid=buildinguuid,
                        name=name)
                    result['status'] = SUCCESS
                    result['msg'] = '已完成'
                except Unit.DoesNotExist:
                    try:
                        building = Building.objects.get(
                            uuid=buildinguuid)
                        Unit.objects.create(
                            building=building,
                            name=name,
                            uuid=uuid.uuid4())
                        result['status'] = SUCCESS
                        result['msg'] = '已完成'
                    except Building.DoesNotExist:
                        result['msg'] = '未找到楼号'
            else: 
                # 新建楼号
                try:
                    building = Building.objects.get(
                        community=community,
                        name=name)
                except Building.DoesNotExist: 
                    Building.objects.create(
                        community=community,
                        name=name,
                        uuid=uuid.uuid4())
                result['status'] = SUCCESS
                result['msg'] = '已完成' 
        else:
            result['msg'] = 'Need name in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")

    def put(self, request):
        """
        修改
        """
        result = {
            "status": ERROR
        }
        user = request.user
        data = request.POST
        if 'roomuuid' in data and 'communityuuid' in data:
            roomuuid = data['roomuuid']
            communityuuid = data['communityuuid']
            status, msg = varify_data(data)
            if status == 1:
                result['status'] = ERROR
                result['msg'] = msg
                return HttpResponse(json.dumps(result), content_type="application/json")
            try:
                msg = "保存成功"
                room = Room.objects.get(uuid=roomuuid,
                                        community__uuid=communityuuid)
                if 'name' in data:
                    name = data['name'].strip()
                    room.name = name

                if 'area' in data:
                    area = data['area'].strip()
                    room.area = area

                if 'status' in data:
                    status = data['status'].strip()
                    room.status = status
  
                if 'unituuid' in data:
                    unituuid = data['unituuid'].strip()
                    if unituuid:
                        try:
                            unit = Unit.objects.get(uuid=unituuid)
                            room.unit = unit
                        except Unit.DoesNotExist:
                            result['status'] = ERROR
                            result['msg'] = "单元号未找到"
                            return HttpResponse(json.dumps(result), content_type="application/json")
                if 'fixed_fee' in data:
                    fixed_fee_uuid = data['fixed_fee']
                    try:
                        fixed_fee = FixedFee.objects.get(uuid=fixed_fee_uuid)
                        room.fixed_fee = fixed_fee
                    except FixedFee.DoesNotExist:
                        result['status'] = ERROR
                        result['msg'] = "统一收费制度未找到"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                
                if 'arrearage_start_date' in data:
                    arrearage_start_date = data['arrearage_start_date'] 
                    if arrearage_start_date:
                        try:
                            arrearage_start_date = datetime.strptime(arrearage_start_date, settings.DATEFORMAT)
                            
                            # 记录操作日志
                            org_date = room.arrearage_start_date 
                            if org_date:
                                org_date = org_date.strftime(settings.DATEFORMAT)
                            else:
                                org_date = "未设置" 
                            detail = "修改起始计费日期，原值:{0}, 新值:{1}".format(\
                                org_date , 
                                data['arrearage_start_date']
                                ) 
                            add_history(user, room, detail)

                            room.arrearage_start_date = arrearage_start_date
                        except ValueError:
                            result['status'] = ERROR
                            result['msg'] = "起始计费日期格式错误"
                            return HttpResponse(json.dumps(result), content_type="application/json")


                if 'fee_status' in data:
                    # 表示业主已欠费
                    fee_status = data['fee_status'].strip()
                    if room.fee_status != int(fee_status): 
                        room.fee_status = fee_status 
                        # 记录操作日志  
                        detail = "修改缴费状态，原值:{0}, 新值:{1}".format(\
                            get_room_feestatus_txt(room.fee_status) , 
                            get_room_feestatus_txt(fee_status) 
                            ) 
                        add_history(user, room, detail)
                 
                if 'dynamic_fees' in data:
                    dynamic_fees = data['dynamic_fees'] 
                    dynamic_fees_json = json.loads(dynamic_fees)
                    if len(dynamic_fees_json) == 0:
                        # 删除所有的非固定性收费项
                        RoomDynamicFeeDetail.objects.filter(room = room).delete()
                    else:
                        # 以前存在的收费项：更新start_date
                        # 以前不存在的，直接新建
                        # 删除本次剔除的 
                        exclude_uuids = []
                        for dynamic_fee in dynamic_fees_json: 
                            exclude_uuids.append(dynamic_fee['dynamicfee__uuid'])
                            try:
                                dynamicfee = DynamicFee.objects.get(
                                    uuid=dynamic_fee['dynamicfee__uuid'])
                                start_date = dynamic_fee['start_date']
                                start_date = datetime.strptime(start_date, settings.DATEFORMAT)
                                try:
                                    dynamicdetail = RoomDynamicFeeDetail.objects.get(room = room, dynamicfee = dynamicfee)
                                    dynamicdetail.start_date = start_date
                                except RoomDynamicFeeDetail.DoesNotExist:
                                    dynamicdetail = RoomDynamicFeeDetail()
                                    dynamicdetail.uuid = uuid.uuid4()
                                    dynamicdetail.room = room
                                    dynamicdetail.dynamicfee = dynamicfee
                                    dynamicdetail.start_date = start_date
                                dynamicdetail.save()
                                single_dynamicfee_calculate(dynamicdetail, final_date=None, user = user )
                                
                            except DynamicFee.DoesNotExist:
                                result['msg'] = "收费项不存在" 
                                return HttpResponse(json.dumps(result), content_type="application/json")
                        RoomDynamicFeeDetail.objects.filter(room = room).exclude(dynamicfee__uuid__in = exclude_uuids).delete()
                      
                if 'roomers' in data:
                    roomers = data['roomers']
                    print(roomers)
                    room.roomers.clear()
                    roomers_json = json.loads(roomers)
                    for roomer in roomers_json:
                        roomer_phone = roomer['phone']
                        if verify_phone(roomer_phone):
                            try:
                                user = User.objects.get(phone=roomer_phone)
                            except User.DoesNotExist:
                                user = User.objects.create(phone=roomer_phone,
                                                        uuid=uuid.uuid4())
                            user.username = roomer['name']
                            user.save()
                            room.roomers.add(user)
                        else:
                            msg = "业主手机号码格式错误，业主信息未保存"
                 
                
                if   'phone' in data:
                    username = data['username']
                    phone = data['phone']  
                    if phone: 
                        if  verify_phone(phone):
                            try:
                                user = User.objects.get(phone=phone)
                            except User.DoesNotExist:
                                user = User.objects.create(phone=phone,
                                                        uuid=uuid.uuid4())
                            if 'username' in data:
                                username = data['username'].strip()
                                if len(username) > 0:
                                    user.username = username
                                    user.save()
                            room.owner = user 
                        else:
                            msg = "业主手机号码格式错误，业主信息未保存"
                room.save()
                result['status'] = SUCCESS
                result['msg'] = msg
            except Room.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = "未找到对应房屋信息"
        elif 'uuid' in data and 'level' in data:
            assetuuid = data['uuid']
            level = data['level']
            if int(level) == 1:
                # 楼号修改
                try:
                    building = Building.objects.get(uuid=assetuuid)
                    if 'name' in data:
                        name = data['name'].strip()
                        building.name = name
                        building.save()
                except Building.DoesNotExist:
                    result['msg'] = "未找到对应楼号"
                    return HttpResponse(json.dumps(result), content_type="application/json")

            else:
                # 单元号修改
                try:
                    unit = Unit.objects.get(uuid=assetuuid)
                    if 'name' in data:
                        name = data['name'].strip()
                        unit.name = name
                        unit.save()
                except Unit.DoesNotExist:
                    result['msg'] = "未找到对应单元号"
                    return HttpResponse(json.dumps(result), content_type="application/json")

            result['status'] = SUCCESS
            result['msg'] = '已完成'
        else:
            result['msg'] = 'Need uuid 和level  in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self, request):
        """
        删除房号
        """
        result = {
            "status": ERROR
        }
        data = request.POST
        if 'uuids' in data:
            uuids = data['uuids']
            Room.objects.filter(uuid__in=uuids.split(",")).delete()
            result['status'] = SUCCESS
            result['msg'] = '已删除'
        else:
            result['msg'] = 'Need uuids, level, communityuuid in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")
