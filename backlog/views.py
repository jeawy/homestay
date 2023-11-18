#! -*- coding: utf-8 -*- 
import json
import os
import pdb
import time
import traceback
import uuid 
from common.logutils import getLogger
from datetime import datetime
from rest_framework.views import APIView 
from django.http import HttpResponse 
from property import settings 
from property.code import SUCCESS, ERROR 
from backlog.models import Backlog    
logger = getLogger(True, 'backlog', False)

 

class BacklogView(APIView):
    """
    管理
    """

    def get(self, request):
        # 查看，应该限制在小区范围内
        result = {"status": ERROR}
        kwargs = {} 
        user = request.user
        
        if 'uuid' in request.GET:
            backloguuid = request.GET['uuid']
            try:
                backlog = Backlog.objects.get(uuid=backloguuid,  user=user) 
                 
                result['msg'] = {
                    "uuid" : backlog.uuid,
                    "picture" : backlog.picture,
                    "content" : backlog.content,
                    "detail" : backlog.detail,
                    "title" : backlog.title,
                    "status" : backlog.status,
                }
                result['status'] = SUCCESS
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Backlog.DoesNotExist:
                result['msg'] = "未找到对应待办事项"
                return HttpResponse(json.dumps(result), content_type="application/json")

        if 'content' in request.GET:
            content = request.GET['content'].strip()
            kwargs['content__icontains'] = content
        if 'status' in request.GET:
            status = request.GET['status'].strip()
            kwargs['status'] = status
        if 'title' in request.GET:
            title = request.GET['title'].strip()
            kwargs['title__icontains'] = title
  
        kwargs['user'] = user
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

        backlogs = list(Backlog.objects.filter(
            **kwargs).values(
                    "uuid", "picture", "content","detail", "title", "status", "date"
                )[page*pagenum: (page+1)*pagenum] )
        total = Backlog.objects.filter(**kwargs).count()
        for backlog in backlogs:
            backlog['date'] = time.mktime(backlog['date'].timetuple())
        result['status'] = SUCCESS
        result['msg'] = {
            "list":backlogs,
            "total": total
        }

        return HttpResponse(json.dumps(result), content_type="application/json")

    def post(self, request):
        # 添加 待办
        result = {
            'status':ERROR
        }
        user = request.user 
        data = request.POST
         
        if 'method' in data:
            method = data['method'].lower() 
            if method == 'put':
                return self.put(request)
            elif method == 'delete':
                return self.delete(request)

        backlog = Backlog()
        if 'title' in data   :
            title = data['title'].strip()
             
            if 'content' in data:
                content = data['content']
                backlog.content = content

            if 'detail' in data:
                detail = data['detail']
                backlog.detail = detail
             
            if 'picture' in data:
                picture = data['picture']
                backlog.picture = picture
            
            backlog.uuid = uuid.uuid4()
            backlog.user = user 
            backlog.title = title 
            backlog.save()
  
            result['status'] = SUCCESS
            result['msg'] = "已保存" 
        else:
            result['status'] = ERROR
            result['msg'] = 'title为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")
    
    def put(self, request):
        # 修改
        # 小区的IT技术支持，小区的管理，工作人员，都可以修改这个

        result = {} 
        data = request.POST
        user = request.user
        if 'uuid' in data  : 
            backloguuid = data['uuid']
            try:
                backlog = Backlog.objects.get(uuid=backloguuid, user = user )
            except Backlog.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未能找到该id对应的信息'
                return HttpResponse(json.dumps(result), content_type="application/json")
           
            if 'title' in data:
                title = data['title']
                backlog.title = title
            
            if 'status' in data:
                status = data['status']
                backlog.status = status

            if 'content' in data:
                content = data['content']
                backlog.content = content

            if 'detail' in data:
                detail = data['detail']
                backlog.detail = detail
             
            if 'picture' in data:
                picture = data['picture']
                backlog.picture = picture

             
            backlog.save()
            result['status'] = SUCCESS
            result['msg'] = '已完成'
        else:
            result['status'] = ERROR
            result['msg'] = 'uuid参数为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")


    def delete(self, request):
        # 删除
        result = {} 
        data = request.POST
        user = request.user
        if 'uuids' in data  :
            uuids = data['uuids'] 
            uuids_ls = uuids.split(',') 
            Backlog.objects.filter(uuid__in=uuids_ls, user = user ).delete() 
            result['status'] = SUCCESS
            result['msg'] = '删除成功'
        else:
            result['status'] = ERROR
            result['msg'] = '缺少uuids和communityuuid参数'
        return HttpResponse(json.dumps(result), content_type="application/json")
  