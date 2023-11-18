#! -*- coding: utf-8 -*-
import json
import os
import pdb
import traceback
import uuid 
from common.logutils import getLogger
from datetime import datetime
from rest_framework.views import APIView


from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.http import HttpResponse
from community.models import Community
from property import settings
from appuser.models import AdaptorUser as User
from property.code import SUCCESS, ERROR 
from msg.models import Msg, MsgSpecifications
from organize.i18 import *
from msg.comm_msg import msg_infos_lst, msg_info 
logger = getLogger(True, 'msg', False)


class MsgProductView(APIView):
    """
    短信管理
    """

    def get(self, request):
        result = {"status": ERROR}
        kwargs = {}
        user = request.user

        if 'uuid' in request.GET:
            msguuid = request.GET['uuid']
            try:
                msg = Msg.objects.get(uuid=msguuid)
                result['msg'] = msg_info(msg)
                result['status'] = SUCCESS
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Msg.DoesNotExist:
                result['msg'] = "未找到对应套餐"
                return HttpResponse(json.dumps(result), content_type="application/json")
        if 'latest' in request.GET: 
            msg = Msg.objects.latest("-date")
            if msg:
                result['msg'] = msg_info(msg)
            else:
                result['msg'] = {}

            result['status'] = SUCCESS
            return HttpResponse(json.dumps(result), content_type="application/json")
            
        if 'content' in request.GET:
            content = request.GET['content'].strip()
            kwargs['content__icontains'] = content

        if 'title' in request.GET:
            title = request.GET['title'].strip()
            kwargs['title__icontains'] = title
        if 'status' in request.GET:
            status = request.GET['status'].strip()
            kwargs['status'] = status
        msgs = Msg.objects.filter(**kwargs)
        result['status'] = SUCCESS
        result['msg'] = msg_infos_lst(msgs)

        return HttpResponse(json.dumps(result), content_type="application/json")

    def post(self, request):
        # 添加短信套餐
        # 小区的IT技术支持， 超级管理员可以操作
        result = {}
        user = request.user

        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST

        if not user.is_superuser:
            return HttpResponse('Unauthorized', status=401)

        if 'method' in data:
            method = data['method'].lower()
            if method == 'put':
                return self.put(request)
            elif method == 'delete':
                return self.delete(request)

        msg = Msg()
        if 'title' in data and 'content' in data:
            title = data['title'].strip()
            content = data['content'].strip()

            if 'detail' in data:
                detail = data['detail']
                msg.detail = detail

            if 'status' in data:
                status = data['status']
                msg.status = status

            msg.uuid = uuid.uuid4()
            msg.user = user
            msg.content = content
            msg.title = title
            msg.save()

            if 'specifications' in data:
                items = json.loads(data['specifications'].strip())
                for item in items:
                    try:
                        price = float(item['price'])
                        name = item['name']
                        number = item['number']
                        MsgSpecifications.objects.create(
                            product=msg,
                            name=name,
                            price=price,
                            number=number)
                    except ValueError:
                        continue

            result['status'] = SUCCESS
            result['msg'] = "添加成功"

        else:
            result['status'] = ERROR
            result['msg'] = 'content,title,community为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

    def put(self, request):
        # 修改

        result = {}

        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST

        if 'uuid' in data:
            msguuid = data['uuid']
            try:
                msg = Msg.objects.get(uuid=msguuid)
            except Msg.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未能找到该id对应的短信套餐'
                return HttpResponse(json.dumps(result), content_type="application/json")

            if 'title' in data:
                title = data['title'].strip()
                if title:
                    msg.title = title
                else:
                    result['status'] = ERROR
                    result['msg'] = 'title参数不能为空'
                    return HttpResponse(json.dumps(result), content_type="application/json")

            if 'content' in data:
                content = data['content'].strip()
                if content:
                    msg.content = content
                else:
                    result['status'] = ERROR
                    result['msg'] = 'content参数不能为空'
                    return HttpResponse(json.dumps(result), content_type="application/json")

            if 'detail' in data:
                detail = data['detail']
                msg.detail = detail

            if 'status' in data:
                status = data['status']
                msg.status = status

            msg.save()
            if 'specifications' in data:
                MsgSpecifications.objects.filter(product=msg).delete()
                items = json.loads(data['specifications'].strip())
                for item in items:
                    try:
                        price = float(item['price'])
                        name = item['name']
                        number = item['number']
                        MsgSpecifications.objects.create(
                            product=msg,
                            name=name,
                            price=price,
                            number=number)
                    except ValueError:
                        continue
            result['status'] = SUCCESS
            result['msg'] = '修改成功'
        else:
            result['status'] = ERROR
            result['msg'] = 'uuid和小区的communityuuid参数为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self, request):
        # 删除短信套餐
        result = {}

        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST

        if 'uuids' in data  :
            uuids = data['uuids']
            
            uuids_ls = uuids.split(',')
            # 这边正常应该还需要限制范围在小区内部
            Msg.objects.filter(uuid__in=uuids_ls ).delete()

            result['status'] = SUCCESS
            result['msg'] = '删除成功'
        else:
            result['status'] = ERROR
            result['msg'] = '缺少uuids'
        return HttpResponse(json.dumps(result), content_type="application/json")

   