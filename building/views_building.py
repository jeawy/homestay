#! -*- coding:utf-8 -*-
import json
import pdb
import os
import traceback
import time
import operator 
import uuid
from django.core.checks.messages import Error
from django.views.decorators.csrf import csrf_exempt 
from django.http import HttpResponse
from django.utils.translation import ugettext as _ 
from appuser.models import AdaptorUser as User
from django.conf import settings
from building.models import Building, Unit  
from rest_framework.views import APIView 
from property.code import  SUCCESS,  ERROR 
from common.logutils import getLogger   
from community.models import Community
from building.comm import get_single_building_dict,get_units
logger = getLogger(True, 'building', False)  
from building.comm import create_asset  


class BuildingView(APIView): 
    def get(self, request):
        """
        谁可以获取：物业、超级管理员
        """
        result = {
            'status':SUCCESS,
        }
        kwargs = {}
        if 'buildinguuid' in request.GET:
            # 获取单元信息
            buildinguuid = request.GET['buildinguuid']
            units = Unit.objects.filter(building__uuid = buildinguuid)
            result['msg'] = get_units(units)
            result['status'] = SUCCESS
            return HttpResponse(json.dumps(result), content_type='application/json')
        if 'communityuuid' in request.GET:
            communityuuid = request.GET['communityuuid']
            kwargs['community__uuid'] = communityuuid
        
        buildings = Building.objects.filter(**kwargs)
        building_ls = []
        for building in buildings:
            building_ls.append(get_single_building_dict(building))
        result['msg'] = building_ls
        result['status'] = SUCCESS
        return HttpResponse(json.dumps(result), content_type='application/json')

    
    def post(self, request):
        """
        新建
        """
        result = {
            "status":ERROR
        } 
        user = request.user 
        # 验证是否有权限
        if not user.has_role_perm('building.building.manage_building'):
            return HttpResponse('Forbidden', status=403)
        
        # 新建
        if len(request.POST) == 0:
            request.POST = request.data
        if 'method' in request.POST:
            method = request.POST['method'].lower()
            if method == 'put':  # 修改
                return self.put(request)
            elif method == 'delete':  # 删除
                return self.delete(request)
 
        if 'name' in request.POST :
            name = request.POST['name'].strip()
            if 'communityuuid' in request.POST:
                communityuuid = request.POST['communityuuid']
                # 新建楼号
                try:
                    building = Building.objects.get(
                        community__uuid = communityuuid,
                        name = name)
                except Building.DoesNotExist: 
                    try:
                        community = Community.objects.get(
                            uuid =  communityuuid) 
                        Building.objects.create(
                            community = community,
                            name = name,
                            uuid = uuid.uuid4())
                        result['status'] = SUCCESS
                        result['msg'] ='已完成'
                    except Community.DoesNotExist: 
                        result['msg'] ='未找到楼号'
                    

            elif 'buildinguuid' in request.POST:
                buildinguuid = request.POST['buildinguuid']
                # 新建单元号 
                try:
                    unit = Unit.objects.get(
                        building__uuid = buildinguuid,
                        name = name)
                except Unit.DoesNotExist:
                    try:
                        building = Building.objects.get(
                            uuid =  buildinguuid) 
                        Unit.objects.create(
                            building = building,
                            name = name,
                            uuid = uuid.uuid4())
                        result['status'] = SUCCESS
                        result['msg'] ='已完成'
                    except Building.DoesNotExist: 
                        result['msg'] ='未找到楼号' 
        else: 
            result['msg'] ='Need name in POST'
   
        return HttpResponse(json.dumps(result), content_type="application/json")


    def put(self, request):
        """
        修改
        """
        result = {
            "status":ERROR
        }
           
        data = request.POST 
        if 'uuid' in data and 'level' in data:
            assetuuid = data['uuid']
            level = data['level']
            if int(level) == 1:
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
            result['msg'] ='已完成'
            
        else: 
            result['msg'] ='Need uuid 和level  in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")


    def delete(self, request):
        """
        删除
        """
        result = {
            "status":ERROR
        } 
        data = request.POST
        if 'uuids' in data and 'level' in data and 'communityuuid' in data:
            uuids = data['uuids']
            level = int(data['level'])
            communityuuid = data['communityuuid'] 
            if level == 1:
                Building.objects.filter(uuid__in = uuids.split(","),
                 community__uuid=communityuuid).delete()  
            elif level == 2:
                Unit.objects.filter(uuid__in = uuids.split(","),
                 building__community__uuid=communityuuid).delete() 
                 
            result['status'] = SUCCESS
            result['msg'] ='已删除'
        else: 
            result['msg'] ='Need uuids, level, communityuuid in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")

 