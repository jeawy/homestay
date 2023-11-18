# -*- coding: utf-8 -*- 
from common.logutils import getLogger 
from django.shortcuts import render
from django.http import HttpResponse 
from django.conf import settings 
import pdb
from django.views.decorators.csrf import csrf_exempt 
import os
import uuid
from appuser.models import AdaptorUser as User 
from django.utils.translation import ugettext as _
import json 
from rest_framework.views import APIView 

from appuser.verify import check_email_exist, check_name_exist,  check_name, check_email, \
     check_number, check_bool, check_sex, check_phone_exist
from common.utils import verify_phone, verify_email 
from community.models import Staff, Community  
from role.models import Role
from property.code import *
 

logger = getLogger(True, 'users', False)
 
class UserCommunityView(APIView):
 
    
    def post(self, request):
        """
         
        """
        content = {
            'status': ERROR
        }
        user = request.user

        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST
        community = None
        if 'communityuuid' in data:
                #  物业获取自己的员工列表
                communityuuid = data['communityuuid'].strip() 
                try:
                    community = Community.objects.get(uuid = communityuuid)
                    perm = user.has_community_perm('appuser.baseuser.admin_management', community)
                    if not perm:
                        # 无权限
                        return HttpResponse('Forbidden', status=403)
                except Community.DoesNotExist:
                    content['status'] = ERROR
                    content['msg'] = "未找到相关小区"  
                    return HttpResponse(json.dumps(content), content_type='application/json')
        else:
            content['status'] = ERROR
            content['msg'] = "缺少communityuuid" 
            return HttpResponse(json.dumps(content), content_type='application/json')

        if 'method' in data:
            method = data['method'].lower().strip()
            if method == 'put':  # 修改
                return self.put(request)
            if method == 'delete':  # 删除
                return self.delete(request)

        
         
        if 'username' in data and 'phone' in data:
            # 创建用户 
            username = data['username'].strip()
            
            result = check_name(username)
            phone = data['phone'].strip()  
            # 检查phone格式是否正确
            result = verify_phone(phone)
            if result:
                # 检查phone是否重复
                try:
                    user = User.objects.get(phone = phone)
                except User.DoesNotExist: 
                    user = User.objects.create(phone = phone, uuid= uuid.uuid4())
            else:
                content['msg'] = '手机号码格式错误'
                return HttpResponse(json.dumps(content), content_type="application/json")

            user.username = username
            if 'email' in data:
                email = data['email'].strip()
                user.email = email 
                result = verify_email(email)
                if result:
                    # 验证email是否重复
                    if not check_email(email):
                        if check_email_exist(email):
                            content['msg'] = '邮箱重复不可使用'
                            return HttpResponse(json.dumps(content), content_type="application/json")
                        else:
                            user.email = email
                    else:
                        content['msg'] = '邮箱长度需要在0与128之间'
                        return HttpResponse(json.dumps(content), content_type="application/json")
                else:
                    content['msg'] = '邮箱格式错误'
                    return HttpResponse(json.dumps(content), content_type="application/json")

            
            if 'sex' in data:
                sex = data['sex'].strip()
                result = check_sex(sex, content)
                if result:
                    user.sex = sex
                else:
                    content['msg'] = '性别只能为男或女'
                    return HttpResponse(json.dumps(content), content_type="application/json")

            
            if 'password' in data:
                pwd = data['password'].strip()
                # 判断用户输入密码是否为空，若为空则返回提示
                if pwd:
                    user.set_password(pwd)
                else:
                    content['msg'] = '未输入密码'
                    return HttpResponse(json.dumps(content), content_type="application/json")
            Staff.objects.create
            user.save()
            # 添加到物业员工部门
            if community is not None:
                staff = Staff()
                staff.user = user
                staff.community = community
                try:
                    staff.save()
                except Exception:
                    pass
                
            content['status'] = SUCCESS
            content['msg'] = '添加成功'
            return HttpResponse(json.dumps(content), content_type="application/json")
        else:
            # 支持批量创建
            content['status'] = ERROR
            content['msg'] = '缺少关键字段无法创建用户'
        return HttpResponse(json.dumps(content), content_type="application/json")

    
    def put(self, request):
        """
        编辑用户
        """
        content = {
            'status': ERROR,
            'msg': ''
        }
        # 处理前端发送数据
        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST

        user = request.user 
        # 管理员修改用户信息
        if 'id' in data:
            userid = data['id']
            try:
                userid = int(userid)
            except ValueError:
                content['msg'] = '用户id应该是一个整数'
                return HttpResponse(json.dumps(content), content_type="application/json")
            try:
                user = User.objects.get(id=userid)
            except User.DoesNotExist:
                content['msg'] = '找不到用户id'
                return HttpResponse(json.dumps(content), content_type="application/json")

            # 获取name字段
            if 'username' in data:
                username = data['username'].strip()
                # 检查name是否可用与重复
                result = check_name_exist(username, userid)
                if result:
                    content['msg'] = '用户名重复不可使用'
                    return HttpResponse(json.dumps(content), content_type="application/json")
                else:
                    result = check_name(username)
                if result:
                    content['msg'] = '用户名长度需要在0与128之间'
                    return HttpResponse(json.dumps(content), content_type="application/json")
                else:
                    user.username = username
            
            # 获取email字段
            if 'email' in data:
                email = data['email'].strip()
                # 检查email格式是否正确
                result = verify_email(email)
                if result:
                    # 验证email是否重复
                    if check_email_exist(email, userid):
                        content['msg'] = '邮箱重复不可使用'
                        return HttpResponse(json.dumps(content), content_type="application/json")
                    else:
                        user.email = email
                else:
                    content['msg'] = '邮箱格式错误'
                    return HttpResponse(json.dumps(content), content_type="application/json")

            # 获取phone字段
            if 'phone' in data:
                phone = data['phone'].strip()
                if len(phone) :
                    # 检查phone格式是否正确
                    result = verify_phone(phone)
                    if result:
                        # 检查phone是否重复
                        if check_phone_exist(phone, userid):
                            content['msg'] = '手机号码已被注册不可使用'
                            return HttpResponse(json.dumps(content), content_type="application/json")
                        else:
                            user.phone = phone
                    else:
                        content['msg'] = '手机号码格式错误'
                        return HttpResponse(json.dumps(content), content_type="application/json")
                else:
                    user.phone = phone # 设置手机号码为空
            # 获取isactive字段
            if 'isactive' in data:
                isactive = data['isactive'].strip()
                try:
                    isactive = int(isactive)
                except ValueError:
                    content['msg'] = "isactive需要是整数"
                    return HttpResponse(json.dumps(content), content_type="application/json")
                if isactive in [0, 1]:
                    user.is_active = isactive
                else:
                    content['msg'] = "isactive需要是0或者1 "
                    return HttpResponse(json.dumps(content), content_type="application/json")

            # 获取sex字段
            if 'sex' in data:
                sex = data['sex'].strip()
                if sex in ['男', '女']:
                    if sex == '男':
                        user.sex = '男'
                    else:
                        user.sex = '女'
                else:
                    content['msg'] = "性别需要是男或女 "
                    return HttpResponse(json.dumps(content), content_type="application/json")

            # 获取password字段
            if 'password' in data:
                pwd = data['password'].strip()
                # 判断用户输入密码是否为空，若为空则返回提示
                if pwd:
                    user.set_password(pwd)
                else:
                    content['msg'] = '未输入密码'
                    return HttpResponse(json.dumps(content), content_type="application/json")

            user.save()
            content['status'] = SUCCESS
            content['msg'] = '修改成功'
        else:
            content['msg'] = '参数错误：需要用户id'
          
        return HttpResponse(json.dumps(content), content_type="application/json")

 
    def delete(self, request):
        """
        用户删除
        """
        content = {
            'status': ERROR,
            'msg': ''
        }
        # 处理前端发送数据
        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST
 
        # 管理员修改用户信息
        if 'ids' in data and 'communityuuid' in data:
            userids = data['ids'].split(",")
            communityuuid = data['communityuuid']
            Staff.objects.filter(user__id__in=userids, community__uuid = communityuuid).delete()
             
            content['status'] = SUCCESS
            content['msg'] = '移除成功' 
        else:
            content['msg'] = '缺少ids和communityuuid参数'
        return HttpResponse(json.dumps(content), content_type="application/json")
        

  