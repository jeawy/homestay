#! -*- coding: utf-8 -*-
import json
import os
import pdb
import traceback
import uuid 
from common.logutils import getLogger
from datetime import datetime
from rest_framework.views import APIView 
from django.views import View
from django.http import HttpResponse
from community.models import Community
from property import settings
from appuser.models import AdaptorUser as User
from property.code import SUCCESS, ERROR 
from paidservice.models import PaidService
from paidservice.comm import get_paidservice, get_paidservice_detail
from paidservice.comm import verify_data
logger = getLogger(True, 'paidservice', False)



class PaidServiceAnonymousView(View):
    """
    用户端在未登录的时候获取
    """

    def get(self, request):
        result = {"status": ERROR}
        kwargs = {} 
        data = request.GET 
        if 'communityuuid' not in data:
            result['msg'] = "缺少 community uuid"
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            communityuuid = data['communityuuid']
            kwargs['community__uuid'] = communityuuid
  
        if 'uuid' in request.GET:
            paidserviceuuid = request.GET['uuid']
            try:
                paidservice = PaidService.objects.get(uuid = paidserviceuuid)
                result['msg'] = get_paidservice_detail(paidservice)
                result['status'] = SUCCESS
                return HttpResponse(json.dumps(result), content_type="application/json")
            except PaidService.DoesNotExist:
                result['msg'] = "未找到对应服务项目"
                return HttpResponse(json.dumps(result), content_type="application/json")
        
        if 'category' in data:
            category = data['category'].strip()
            kwargs['category'] = category


        if 'content' in request.GET:
            content = request.GET['content'].strip()
            kwargs['content__icontains'] = content
        
        if 'title' in request.GET:
            title = request.GET['title'].strip()
            kwargs['title__icontains'] = title
        if 'status' in request.GET:
            status = request.GET['status'].strip()
            kwargs['status'] = status
        paidservices = PaidService.objects.filter(**kwargs)
        result['status'] = SUCCESS
        result['msg'] = get_paidservice(paidservices)

        return HttpResponse(json.dumps(result), content_type="application/json")



class PaidServiceView(APIView):
    """
    物业端获取
    """ 
    def get(self, request):
        result = {"status": ERROR}
        kwargs = {} 
        data = request.GET
        if 'communityuuid' not in data:
            result['msg'] = "缺少 community uuid"
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            communityuuid = data['communityuuid']
            try:
                community = Community.objects.get(uuid=communityuuid)
                kwargs['community'] = community 
            except Community.DoesNotExist:
                result['msg'] = "Community Not Exist"
                return HttpResponse(json.dumps(result), content_type="application/json")
        
         
        if 'uuid' in request.GET:
            paidserviceuuid = request.GET['uuid']
            try:
                paidservice = PaidService.objects.get(uuid = paidserviceuuid)
                result['msg'] = get_paidservice_detail(paidservice)
                result['status'] = SUCCESS
                return HttpResponse(json.dumps(result), content_type="application/json")
            except PaidService.DoesNotExist:
                result['msg'] = "未找到对应服务项目"
                return HttpResponse(json.dumps(result), content_type="application/json")
        
        if 'category' in data:
            category = data['category'].strip()
            kwargs['category'] = category 
        if 'content' in request.GET:
            content = request.GET['content'].strip()
            kwargs['content__icontains'] = content
        
        if 'title' in request.GET:
            title = request.GET['title'].strip()
            kwargs['title__icontains'] = title
        if 'status' in request.GET:
            status = request.GET['status'].strip()
            kwargs['status'] = status
        
        paidservices = PaidService.objects.filter(**kwargs)
        result['status'] = SUCCESS
        result['msg'] = get_paidservice(paidservices)

        return HttpResponse(json.dumps(result), content_type="application/json")

    def post(self, request):
        # 添加 
        # 小区的IT技术支持， 超级管理员可以操作
        result = {
            "status":ERROR
        }
        user = request.user

        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST
        community = None

        if 'communityuuid' not in data:
            result['msg'] = "缺少 community uuid"
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            communityuuid = data['communityuuid']
            try:
                community = Community.objects.get(uuid=communityuuid)
                if not user.has_community_perm("paidservice.paidservice.manage_paidservice", community):
                    return HttpResponse('Unauthorized', status=401)
            except Community.DoesNotExist:
                result['msg'] = "Community Not Exist"
                return HttpResponse(json.dumps(result), content_type="application/json")
 
        if 'method' in data:
            method = data['method'].lower()
            if method == 'put':
                return self.put(request)
            elif method == 'delete':
                return self.delete(request)

        
        if 'title' in data   \
            and 'category' in data and 'unit' in data\
                and 'money' in data:
            verify_result = verify_data(data)
            if  verify_result[0] == ERROR:
                result['msg'] = verify_result[1]
                return HttpResponse(json.dumps(result), content_type="application/json")

            title = data['title'].strip()
            
            category = data['category'].strip()
            unit = data['unit'].strip()
            money = data['money'].strip()

            paidservice = PaidService() 
            if int(category) not in paidservice.get_category_ls():
                result['msg'] = "类别不存在"
                return HttpResponse(json.dumps(result), content_type="application/json")
 
            paidservice.uuid = uuid.uuid4()
            paidservice.user = user
             
            paidservice.title = title
            paidservice.unit = unit
            paidservice.community = community
            paidservice.category = category
            paidservice.money = money
            if 'status' in data:
                status = data['status']
                paidservice.status = status
            if 'content' in data:
                content = data['content'].strip()
                paidservice.content = content 
            paidservice.save()
 
            result['status'] = SUCCESS
            result['msg'] = "添加成功" 
        else:
            result['status'] = ERROR
            result['msg'] = 'content,title,category等必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

    def put(self, request):
        # 修改

        result = {}

        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST

        if 'uuid' in data:
            paidserviceuuid = data['uuid']
            try:
                paidservice = PaidService.objects.get(uuid=paidserviceuuid)
            except PaidService.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未能找到该id对应的服务'
                return HttpResponse(json.dumps(result), content_type="application/json")
            
            verify_result = verify_data(data)
            if  verify_result[0] == ERROR:
                result['msg'] = verify_result[1]
                return HttpResponse(json.dumps(result), content_type="application/json")
            
            if 'title' in data:
                title = data['title'].strip()
                if title:
                    paidservice.title = title
                else:
                    result['status'] = ERROR
                    result['msg'] = 'title参数不能为空'
                    return HttpResponse(json.dumps(result), content_type="application/json")

            if 'content' in data:
                content = data['content'].strip() 
                paidservice.content = content
                 
            if 'unit' in data:
                unit = data['unit']
                paidservice.unit = unit

            if 'status' in data:
                status = data['status']
                paidservice.status = status
            
            if 'money' in data:
                money = data['money']
                paidservice.money = money

            if 'category' in data:
                category = data['category']
                if int(category) not in paidservice.get_category_ls():
                    result['msg'] = "类别不存在"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                paidservice.category = category

            paidservice.save()
             
            result['status'] = SUCCESS
            result['msg'] = '修改成功'
        else:
            result['status'] = ERROR
            result['msg'] = 'uuid和小区的communityuuid参数为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self, request):
        # 删除套餐
        result = {}

        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST

        if 'uuids' in data  :
            uuids = data['uuids']
            
            uuids_ls = uuids.split(',')
            # 这边正常应该还需要限制范围在小区内部
            PaidService.objects.filter(uuid__in=uuids_ls ).delete() 
            result['status'] = SUCCESS
            result['msg'] = '删除成功'
        else:
            result['status'] = ERROR
            result['msg'] = '缺少uuids'
        return HttpResponse(json.dumps(result), content_type="application/json")

   