#! -*- coding:utf-8 -*-
import json
import pdb
import os
import traceback
import time
import operator 
from django.views.decorators.csrf import csrf_exempt 
from django.http import HttpResponse
from django.utils.translation import ugettext as _ 
from appuser.models import AdaptorUser as User
from django.conf import settings  
from rest_framework.views import APIView 
from property.code import  SUCCESS,  ERROR 
from common.logutils import getLogger   
from community.models import Community
logger = getLogger(True, 'building', False)  
from building.comm import create_asset  


class BatchView(APIView): 
    def post(self, request):
        """
        批量创建资产
        post发送的json请求
        {"keys": ["building_name", "unit_name", "roomname", "area"],
                      "values":
                          [["22栋", "1单元", "1023", "100",],
                          ["22栋", "1单元", "1023", "100",],
                          ["22栋", "1单元", "1023", "100",],
                          ["22栋", "1单元", "1023", "100",] ],
                      "community_uuid":""}
        """

        user = request.user
        # 验证是否有新建资产的权限
        if not user.has_role_perm('assets.building.manage_building'):
            return HttpResponse('Forbidden', status=403)

        asset_json = request.data
        result = {}
        data = {}
        try:
            community_uuid = asset_json['community_uuid'] 
            # 权限需要满足：1 是物业角色或者超级管理员、2 有编辑资产的权限
            # 3、物业自己管理的小区，这些需要待完善2021年11月28日20:35:11
            community = Community.objects.get(uuid=community_uuid)
            user = request.user
            result = create_asset(asset_json, community, user)
            # 临时字典,保存通过excel创建资产的信息
            temp = {}
            temp['msg'] = "批量创建资产"
            temp['failure_num'] = result['failure_num']
            temp['success_num'] = result['success_num']
            # 把temp字典保存到data字典
            data = temp
            data['status'] = SUCCESS
               
        except Community.DoesNotExist:
            data["status"] = ERROR
            data["msg"] = "uuid不存在"
        return HttpResponse(json.dumps(data), content_type="application/json")

 