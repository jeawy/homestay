#! -*- coding:utf-8 -*-
import json
from json.encoder import INFINITY
import pdb
import uuid
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.translation import ugettext as _
from role.models import Role, Cert
from appuser.models import AdaptorUser as User
from community.models import Community

from rest_framework.views import APIView
from role.comm import RoleMgr
from django.views import View
from django.contrib.auth.models import Permission
from property.code import *
from appuser.comm import get_user_info
from common.logutils import getLogger
logger = getLogger(True, 'crt', False)


class RoleCrtView(APIView):
    def get(self, request):
        content = {}
        user = request.user
        kwargs = {"user":user}
        if 'code' in request.GET:
            code = request.GET['code']
            kwargs['role__code'] = code
        if 'communityuuid' in request.GET:
            # 获取某个小区的身份认证信息
            communityuuid = request.GET['communityuuid']
            kwargs['community__uuid'] = communityuuid
              
        content['status'] = SUCCESS
        content['msg'] = list(Cert.objects.filter(
            **kwargs).values_list("community__uuid", "community__name", "role__name"))
        return HttpResponse(json.dumps(content), content_type="application/json")

    def post(self, request):
        """
        添加、修改认证
        """
        result = {
            "status" : ERROR
        } 
        data = request.POST
        if 'communityuuid' in data:
            communityuuid = data['communityuuid'].strip()
            try:
                community = Community.objects.get(uuid=communityuuid) 
            except Community.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = "未找到相关小区"
                return HttpResponse(json.dumps(result), content_type="application/json")
           
            if 'method' in data:
                method = data['method'].lower()
                if method == 'delete':  # 删除
                    return self.delete(request, community)

            if 'roleid' in data  :
                roleid = data['roleid'].strip()  
                try:
                    role = Role.objects.get(id=roleid)
                    if role.role_sort == role.INTERNAL or role.community == community:
                        try:
                            Cert.objects.get(role=role,
                                                user=request.user,
                                                community=community)
                        except Cert.DoesNotExist:
                            Cert.objects.create(
                                uuid = uuid.uuid4(),
                                role=role,
                                                user=request.user,
                                                community=community)
                        result['status'] = SUCCESS
                        result['msg'] = '创建成功'
                    else: 
                        result['status'] = ERROR
                        result['msg'] = '当前小区不存在该权限'
                except Role.DoesNotExist:
                    result['msg'] = "角色信息不存在" 
        else:
            result['msg'] = "参数错误，缺少community role信息"
        return HttpResponse(json.dumps(result), content_type="application/json")
 
    def delete(self, request, community):
        """
        删除
        """
        result = {}
        user = request.user
        perm = user.has_community_perm("role.cert.manage_cert", community)
        if not perm:
            # 权限不足
            return HttpResponse('没有权限', status=401)

        data = request.POST
        if 'ids' in data:
            crt_ids = data['ids'] 
            Cert.objects.filter(id__in=crt_ids.split(",")).delete() 
            result['status'] = SUCCESS
            result['msg'] = '已完成' 
            return HttpResponse(json.dumps(result), content_type="application/json") 
        else:
            result['status'] = ERROR
            result['msg'] = 'Need id in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")
