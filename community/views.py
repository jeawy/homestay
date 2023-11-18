from datetime import datetime
from operator import mod
from cv2 import ORB_FAST_SCORE
from django.contrib.auth.backends import RemoteUserBackend
from django.db import connections
from common.logutils import getLogger
import pdb
import json
import uuid  
from rest_framework.views import APIView 
from django.http import HttpResponse
from django.views import View
from property.code import ERROR, SUCCESS
from django.db.models import Sum
from community.comm import verify_data, get_community_dict, get_community_detail 
from community.i18 import *
from community.models import Community
from django.conf import settings
from area.models import Area
from common.utils import getStrFirstAplha, getDistance
from appuser.models import AdaptorUser as User
from organize.models import Organize 
from msg.models import MsgOrders
from organize.comm import getUserOrganize
from community.comm import getUserCommunities
from community.comm_statistics import community_statatics
logger = getLogger(True, 'community', False)


class CommunityAnonymousView(View):
    def get(self, request):
        # 匿名获取Communitys列表
        # 
        content={
            "status":SUCCESS,
            "msg" : "uuid缺少"
        }
         
        kwargs = { }
        if 'uuid' in request.GET:
            # 获取详情
            communityuuid = request.GET['uuid']
            try:
                community = Community.objects.get(uuid = communityuuid)
                content['msg'] = get_community_detail(community)
            except Community.DoesNotExist:
                content={
                            "status":ERROR,
                            "msg" : COMMUNITY_NOT_FOUND
                    }
            return HttpResponse(json.dumps(content), content_type="application/json") 
        if 'name' in request.GET:
            name = request.GET['name'].strip() 
            kwargs["name__icontains"] = name
        kwargs["status"] = Community.AVAILABLE 
        nearbycommunities = []

        if 'latitude' in request.GET and 'longitude' in request.GET:
            latitude = request.GET['latitude'].strip()
            longitude = request.GET['longitude'].strip()
            # 按照经纬度搜索附近的小区
            # 这个数据，前端应该存储下来，不应该经常访问。
            kwargs['latitude__isnull'] = False
            kwargs['longitude__isnull'] = False
            try:
                startpoint = {
                    "lat":float(latitude),
                    "lon":float(longitude),
                }
                nearbys = Community.objects.filter(**kwargs).order_by("name")\
                    .values_list("name", "uuid", "latitude", "longitude")
                
                for nearby in nearbys:
                    endpoint = {
                        "lat":float(nearby[2]),
                        "lon":float(nearby[3]),
                    } 
                    distance = getDistance(startpoint, endpoint) 
                    if (distance < 1):
                        # 获取附近小区的条件：距离小于1公里
                        nearbycommunities.append(list(nearby))
                
                content['status'] = SUCCESS
                content['msg'] = nearbycommunities
                return HttpResponse(json.dumps(content), content_type="application/json")
            except ValueError:
                content['status'] = ERROR
                content['msg'] = "经纬度信息错误"
            return HttpResponse(json.dumps(content), content_type="application/json") 
        
        communities = Community.objects.filter(**kwargs).order_by("name").values_list("name", "uuid")
        msg = []
        letters = []
        totalindex = 0 # 为了前端方便选中增加的字段
        for community in communities:
            firstletter = getStrFirstAplha(community[0]) 
            if firstletter not in letters:
                letters.append(firstletter)
                community_dict = {
                    "letter":firstletter,
                    "data":[[community[0], community[1], totalindex]]
                }
                msg.append(community_dict)
            else:
                for msgitem in msg:
                    if msgitem['letter'] == firstletter:
                        msgitem['data'].append([community[0], community[1], totalindex])
                        break
            totalindex += 1
        
        content['msg'] = sorted(msg, key=lambda d:d['letter'])
        content['nearby'] = nearbycommunities
        return HttpResponse(json.dumps(content), content_type="application/json") 
    
      
class CommunityView(APIView): 

    def get(self, request):
        # 获取Communitys列表
        # 
        content={
            "status":SUCCESS,
            "msg" : []
        }
        kwargs = {}
        user = request.user
        pc = False
        feedetail = False
        perm = False # 敏感信息查看权限，如银行信息，余额信息，物业员工都可以看
        communityuuids = []
        if 'pc' in request.GET:
            # 验证是否有权限查看pc端
            pc = True
            communityuuids = getUserCommunities(user)
            # pc端限制小区查询范围 
            kwargs['uuid__in'] = list(communityuuids)
            feedetail = True
            perm = True # 设置为True, 方便获取权限范围内的小区的银行等信息

        if 'uuid' in request.GET:
            # 获取详情
            communityuuid = request.GET['uuid']
            if pc:
                perm = user.is_superuser
                if communityuuid in list(communityuuids):
                    perm = True 
            try:
                community = Community.objects.get(uuid = communityuuid)
                if perm:
                    if 'update' in request.GET:
                        update = request.GET['update']
                        try:
                            if int(update) == 1:
                                # 强制更新收入信息
                                print(datetime.now())
                                community_statatics(community)
                                print(datetime.now()) 
                        except ValueError:
                            pass
                if 'msg' in request.GET:
                    # 只获取短信的配置信息
                    content['msg'] =  {
                        "uuid":community.uuid,
                        "paidservice_msg":community.paidservice_msg,
                        "repaire_msg":community.repaire_msg,
                        "fee_msg":community.fee_msg,
                    }
                else:
                    content['msg'] = get_community_detail(community, perm=perm)
            except Community.DoesNotExist:
                content={
                            "status":ERROR,
                            "msg" : COMMUNITY_NOT_FOUND
                    }
            return HttpResponse(json.dumps(content), content_type="application/json") 
        if 'name' in request.GET:
            name = request.GET['name']
            kwargs['name__icontains'] = name
        if 'area' in request.GET:
            area = request.GET['area']
            kwargs['area__ID'] = area
         
        if 'IT' in request.GET  :
            # IT manager get all community he managed
            IT = request.GET['IT']
            if IT == 'ALL':# 平台管理员获取所有community
                communities = list(Community.objects.all().values("uuid", "name") )
                content['msg'] = { 
                    "comnunity":communities
                    } 
                return HttpResponse(json.dumps(content), content_type="application/json") 

            kwargs['IT_MANAGER'] = user
            communities = Community.objects.filter(**kwargs) 
            total = Community.objects.filter(**kwargs).count()  
            content['msg'] = {
                "total" :total,
                "comnunity":get_community_dict(communities, pc, feedetail)
                } 
            return HttpResponse(json.dumps(content), content_type="application/json") 
        if "communityuuid" in request.GET:
            # 按小区信息获得Community记录(这个功能先放着)
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
        communities = Community.objects.filter(**kwargs)\
            .order_by("-date")[page*pagenum : (page+1)*pagenum]
        total = Community.objects.filter(**kwargs).count() 
        content['msg'] = {
            "total" :total,
            "comnunity":get_community_dict(communities, perm, feedetail)
            } 
 
        return HttpResponse(json.dumps(content), content_type="application/json") 
    

    def post(self, request):
        """
        新建小区：仅超级管理员可以
        
        """
        result = {
            'status': ERROR
        }
        user = request.user
        if not user.is_superuser:
            # 不是超级管理员，返回权限错误
            result['msg'] = COMMUNITY_AUTH_ERROR
            return HttpResponse(json.dumps(result), content_type="application/json")
         
        data = request.POST
         
        if 'method' in data:
            method = data['method'].lower().strip()
            if method == 'put':  # 修改
                return self.put(request)
            if method == 'delete':  # 删除
                return self.delete(request)
 
        if 'name' in data :
            # 创建
            verify_result = verify_data(data)
            if verify_result[0] == ERROR:
                # 验证失败
                result['status'] = ERROR
                result['msg'] = verify_result[1]
                return HttpResponse(json.dumps(result), content_type="application/json")

            community = Community()
            name = data['name'].strip() 
            community.user = user
            community.name = name
            community.uuid = uuid.uuid4() 
            
            if 'longitude' in data:
                longitude = data['longitude'].strip() 
                community.longitude = longitude
            if 'latitude' in data:
                latitude = data['latitude'].strip()
                community.latitude = latitude  
            
            if 'address' in data:
                address = data['address'].strip()
                community.address = address  
            if 'shequ' in data:
                shequ = data['shequ'].strip()
                community.shequ = shequ 
            if 'jiedaoban' in data:
                jiedaoban = data['jiedaoban'].strip()
                community.jiedaoban = jiedaoban 

            if 'wx_sub_mch_id' in data:
                # 微信商户号
                wx_sub_mch_id = data['wx_sub_mch_id'].strip()
                community.wx_sub_mch_id = wx_sub_mch_id

            if 'bank_owner_name' in data:
                bank_owner_name = data['bank_owner_name'].strip()
                community.bank_owner_name = bank_owner_name   
            if 'bank_name' in data:
                bank_name = data['bank_name'].strip()
                community.bank_name = bank_name  
            if 'deposit_bank' in data:
                deposit_bank = data['deposit_bank'].strip()
                community.deposit_bank = deposit_bank 
            if 'bank_number' in data:
                bank_number = data['bank_number'].strip()
                community.bank_number = bank_number 
            
            if 'total_area' in data:
                total_area = data['total_area'].strip()
                community.total_area = total_area 
            if 'total_rooms' in data:
                total_rooms = data['total_rooms'].strip()
                community.total_rooms = total_rooms 
 
            if 'itmanager' in data:
                itmanager = data['itmanager'].strip()
                try:
                    itmanager_instance = User.objects.get(uuid = itmanager)
                    community.IT_MANAGER = itmanager_instance 
                except User.DoesNotExist:
                    result['msg'] = "没有找到IT用户"
                    return HttpResponse(json.dumps(result), content_type="application/json")
            if 'organize' in data:
                organize = data['organize'].strip()
                try:
                    organize_instance = Organize.objects.get(uuid = organize) 
                    community.organize = organize_instance  
                except Organize.DoesNotExist: 
                    result['msg'] = "没有找到相关物业"
                    return HttpResponse(json.dumps(result), content_type="application/json")

            if 'area' in data: 
                area = data['area'].strip()
                try:
                    area_instance = Area.objects.get(ID = area)
                    community.area = area_instance 
                except Area.DoesNotExist:
                    result['msg'] = COMMUNITY_AREA_ERROR
                    return HttpResponse(json.dumps(result), content_type="application/json")

            if 'detail' in data:
                detail = data['detail'].strip()
                community.detail = detail  
            
            if 'smsSignId' in data:
                # 物业的短信签名
                smsSignId = data['smsSignId']
                community.smsSignId = smsSignId
                
            community.save()
            result['status'] = SUCCESS
            result['msg'] = COMMUNITY_ADD_SUCCESS
            
            return HttpResponse(json.dumps(result), content_type="application/json")
        else: 
            result['status'] = ERROR
            result['msg'] = COMMUNITY_NAME_ERROR
        return HttpResponse(json.dumps(result), content_type="application/json")
 
    def put(self, request):
        """
        编辑 
        """
        result = {
            'status': ERROR,
            'msg': ''
        }
        # 处理前端发送数据 
        data = request.POST
        verify_result = verify_data(data)
        if verify_result[0] == ERROR:
            # 验证失败
            result['status'] = ERROR
            result['msg'] = verify_result[1]
            return HttpResponse(json.dumps(result), content_type="application/json")
 
        if 'uuid' in data:
            communityuuid = data['uuid'].strip()
            try:
                community = Community.objects.get(uuid = communityuuid)
                 
                if 'name' in data:
                    name = data['name'].strip()
                    community.name = name

                if 'longitude' in data:
                    longitude = data['longitude'].strip() 
                    community.longitude = longitude
                if 'latitude' in data:
                    latitude = data['latitude'].strip()
                    community.latitude = latitude  

                if 'address' in data:
                    address = data['address'].strip()
                    community.address = address  
                if 'shequ' in data:
                    shequ = data['shequ'].strip()
                    community.shequ = shequ 

                if 'wx_sub_mch_id' in data:
                    # 微信商户号
                    wx_sub_mch_id = data['wx_sub_mch_id'].strip()
                    community.wx_sub_mch_id = wx_sub_mch_id

                if 'jiedaoban' in data:
                    jiedaoban = data['jiedaoban'].strip()
                    community.jiedaoban = jiedaoban 
                if 'detail' in data:
                    detail = data['detail'].strip()
                    community.detail = detail  

                
                if 'bank_owner_name' in data:
                    bank_owner_name = data['bank_owner_name'].strip()
                    community.bank_owner_name = bank_owner_name   
                if 'bank_name' in data:
                    bank_name = data['bank_name'].strip()
                    community.bank_name = bank_name  
                if 'deposit_bank' in data:
                    deposit_bank = data['deposit_bank'].strip()
                    community.deposit_bank = deposit_bank 
                if 'bank_number' in data:
                    bank_number = data['bank_number'].strip()
                    community.bank_number = bank_number 
                
                if 'total_area' in data:
                    total_area = data['total_area'].strip()
                    community.total_area = total_area 
                if 'total_rooms' in data:
                    total_rooms = data['total_rooms'].strip()
                    community.total_rooms = total_rooms 
                    
                if 'itmanager' in data:
                    itmanager = data['itmanager'].strip()
                    try:
                        itmanager_instance = User.objects.get(uuid = itmanager)
                        community.IT_MANAGER = itmanager_instance 
                    except User.DoesNotExist:
                        result['msg'] = "没有找到IT用户"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                if 'organize' in data:
                    organize = data['organize'].strip()
                    try:
                        organize_instance = Organize.objects.get(uuid = organize)
                   
                        community.organize = organize_instance  
                    except Organize.DoesNotExist: 
                        result['msg'] = "没有找到相关物业"
                        return HttpResponse(json.dumps(result), content_type="application/json")


                if 'area' in data: 
                    area = data['area'].strip()
                    try:
                        area_instance = Area.objects.get(ID = area)
                        community.area = area_instance 
                    except Area.DoesNotExist:
                        result['msg'] = COMMUNITY_AREA_ERROR
                        return HttpResponse(json.dumps(result), content_type="application/json")

  
                community.save()
                result['status'] = SUCCESS
                result['msg'] = COMMUNITY_MODIFY_SUCCESS
                result['uuid'] = community.uuid
            except Community.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = COMMUNITY_PARAM_ERROR_NEED_UUID
                 
        return HttpResponse(json.dumps(result), content_type="application/json")
 
    def delete(self, request):
        """
        删除
        """
        result = {
            'status': ERROR,
            'msg': '暂时不支持删除'
        }
        data = request.POST
        if 'uuids' in data  :
            uuids = data['uuids'] 
            Community.objects.filter(uuid__in = uuids.split(",")).delete()  
            result['status'] = SUCCESS
            result['msg'] ='已删除'
        else: 
            result['msg'] ='Need uuids, level, communityuuid in POST'
        
        
        return HttpResponse(json.dumps(result), content_type="application/json")
        
