#! -*- coding:utf-8 -*-
import json
import pdb 
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime 
from django.http import HttpResponse, HttpResponseForbidden 
from django.utils.translation import ugettext as _
from dept.models import Dept
from django.http import QueryDict
from appuser.comm import get_user_info 
from appuser.models import AdaptorUser as User 
from django import forms
from django.utils import timezone
from django.shortcuts import redirect 
from community.models import Community

from rest_framework.views import APIView
from property.code import * 
from dept.comm import get_dept_dict, check_name_exist, check_alias
from common.logutils import getLogger
logger = getLogger(True, 'dept', False)

class DeptView(APIView):
     
    def get(self, request):

        content = {} 
        user = request.user 
        if 'communityuuid' in request.GET:
            #  物业获取自己的员工列表
            communityuuid = request.GET['communityuuid'].strip() 
            try:
                community = Community.objects.get(uuid = communityuuid)
                perm = user.has_community_perm('dept.dept.can_manage_dept', community)
               
                content['auth'] = {
                    "manage_dept":perm
                }
            except Community.DoesNotExist:
                content['status'] = ERROR
                content['msg'] = "未找到相关小区" 
                content['auth'] = {
                    "manage_dept":False
                }
                return HttpResponse(json.dumps(content), content_type='application/json')
        else: 
            perm = user.has_role_perm('dept.dept.can_manage_dept')
            
            content['auth'] = {
                "manage_dept":perm
            }
        
        if 'id' in request.GET:
            
            dept_id = request.GET['id']
            try:
                dept_id = int(dept_id)
            except ValueError:
                content['status'] = ERROR
                content['msg'] = 'id not int'
                return HttpResponse(json.dumps(content), content_type="application/json")

            try:
                dept = Dept.objects.get(id=dept_id)
                content['status'] = SUCCESS
                content['msg'] = get_dept_dict(dept)
                users = dept.users.all()
                content['users'] = get_user_info(users) 
            except Dept.DoesNotExist:
                content['status'] = ERROR
                content['msg'] = '404 Not found the id'
            return HttpResponse(json.dumps(content), content_type="application/json")
        elif 'user' in request.GET:
            user = request.GET['user']
            try:
                user = User.objects.get(id=user)
                depts = user.user_depts.all()
                depts_id = [dept.id for dept in depts]
                users = User.objects.filter(depts__id__in  = depts_id)
                
                content['status'] = SUCCESS
                content['msg'] = get_user_info(users)
            except User.DoesNotExist:
                content['status'] = ERROR
                content['msg'] = '用户不存在'
        else:
            kwargs = {}
            if 'parentid' in request.GET:
                parentid = request.GET['parentid']
                kwargs['parent__id'] = parentid
            else:
                kwargs['level'] = 1
            
            if 'communityuuid' in request.GET:
                #  物业获取自己的员工列表
                communityuuid = request.GET['communityuuid'].strip() 
                kwargs['community__uuid'] = communityuuid
                depts = Dept.objects.filter( **kwargs )
                depts_list = []
                for dept in depts:
                    depts_list.append(get_dept_dict(dept))
                content['msg'] = depts_list
                content['status'] = SUCCESS
            else:
                content['msg'] = "参数错误，缺少community uuid"
                content['status'] = ERROR
             
        return HttpResponse(json.dumps(content), content_type="application/json")


    
    def post(self, request):
        """
        新建
        """
        result = {} 
        user = request.user 
        community = None
        # 小区uuid是必须参数
        if 'communityuuid' in request.POST:
            #  物业获取自己的员工列表
            communityuuid = request.POST['communityuuid'].strip() 
            try:
                community = Community.objects.get(uuid = communityuuid)
                perm = user.has_community_perm('dept.dept.can_manage_dept', community)
               
                if not perm:
                    return HttpResponse('Forbidden', status=403)
            except Community.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = "未找到相关小区" 
                result['auth'] = {
                    "manage_dept":False
                }
                return HttpResponse(json.dumps(result), content_type='application/json')
        else:
            result['msg'] = "参数错误，缺少community uuid"
            result['status'] = ERROR
            return HttpResponse(json.dumps(result), content_type='application/json')
             
         
        if 'method' in request.POST:
            method = request.POST['method'].lower()
            if method == 'put':  # 修改
                return self.put(request, community)
            elif method == 'delete':  # 删除
                return self.delete(request)

        
        
        # 新建部门
        # name字段是必须的；如果提供了parentid，则新的部门为parent部门的子部门
        # 否则添加为父部门
        if 'name' in request.POST :
            name = request.POST['name'].strip()
            parentid = request.POST.get('parentid') 
            chargerid = request.POST.get('chargerid')
            charger = None # 部门负责人

            if len(name) > 1024 :
                result['status'] = ERROR
                result['msg'] ="部门名字太长，不能超过512个字"
                return HttpResponse(json.dumps(result), content_type="application/json") 
            elif len(name) == 0:
                result['status'] = ERROR
                result['msg'] ="部门名字不能为空"
                return HttpResponse(json.dumps(result), content_type="application/json")
            elif check_name_exist(name, community):
                # 部门名称已经存在
                result['status'] = ERROR
                result['msg'] ="部门名字已存在"
                return HttpResponse(json.dumps(result), content_type="application/json")
 
            if chargerid:
                # 部门负责人
                # 为当前用户添加部门负责人角色
                try:
                    charger = User.objects.get(id=chargerid)
                except User.DoesNotExist:
                    result['status'] = DEPT_ARGUMENT_ERROR_CHANGR_NOT_FOUND
                    result['msg'] = 'charnger  not found.'
                    return HttpResponse(json.dumps(result), content_type="application/json")

            alias = None
            if 'alias' in request.POST :
                alias = request.POST['alias'].strip()
                result = check_alias(alias)
                if result['status'] != SUCCESS:
                    return HttpResponse(json.dumps(result), content_type="application/json")


            if parentid:
                # 创建顶级子部门
                try: 
                    dept = Dept.objects.get(id=parentid) 
                    level = dept.level
                    dept = Dept.objects.create(name=name, 
                              level=level+1, 
                              parent=dept, 
                              alias=alias,
                              community = community) 
                    if charger:
                        # 添加部门负责人
                        dept.charger = charger
                        dept.save()
                    result['id'] = dept.id
                    result['status'] = SUCCESS
                    result['msg'] ='已完成'
                except Dept.DoesNotExist:
                    result['status'] = DEPT_PARENTID_NOTFOUND
                    result['msg'] = [parentid] #'404 Parent Dept not found ID:{}'.format(parentid) 
            else:
                # 创建顶级部门
                dept = Dept.objects.create(name=name,
                                     alias=alias,
                                    community = community)
                if charger:
                    # 添加部门负责人
                    dept.charger = charger
                    dept.save()

                result['id'] = dept.id
                result['status'] = SUCCESS
                result['msg'] ='已完成'
        else:
            result['status'] = ERROR
            result['msg'] ='Need name in POST'
   
        return HttpResponse(json.dumps(result), content_type="application/json")


    def put(self, request, community):
        """
        修改
        """
        result = {}
        user = request.user  
        data = request.POST
        
        if 'id' in data:
            deptid = data['id']
            try:
                dept = Dept.objects.get(id=deptid, community = community)
                logger.debug("user:{0} start to modify dept:{1}:ID:{2}".format(user.username, dept.name, dept.id))
                if 'name' in data: 
                    # 修改部门名称
                    name = data['name'].strip()
                    logger.debug("user:{0} start to modify dept old name:{1}: new name:{2}".\
                                           format(user.username, dept.name, name))
                    if len(name) > 1024 :
                        result['status'] = ERROR
                        result['msg'] = "部门名字太长，不能超过512个字"
                        return HttpResponse(json.dumps(result), content_type="application/json") 
                    elif len(name) == 0:
                        result['status'] = ERROR
                        result['msg'] ='部门名字不能为空'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    elif check_name_exist(name, community=community, excludeid = dept.id):
                        # 部门名称已经存在
                        result['status'] = ERROR
                        result['msg'] = '部门名字已存在'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    dept.name = name

                if 'alias' in data:
                    # 修改部门别名
                    alias = data['alias'].strip()
                    logger.debug("user:{0} start to modify dept old alias:{1}: new alias:{2}".\
                                           format(user.username, dept.alias, alias))
                    result = check_alias(alias,dept.id)
                    if result['status'] != SUCCESS:
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    dept.alias = alias
                
                if 'chargerid' in data:
                    # 修改部门负责人
                    chargerid = data['chargerid']
                    if chargerid:
                        # 部门负责人
                        # 为当前用户添加部门负责人角色
                        try:
                            charger = User.objects.get(id = chargerid) 
                            dept.charger = charger 
                        except User.DoesNotExist:
                            result['status'] = ERROR
                            result['msg'] = '未找到相关负责人'
                            return HttpResponse(json.dumps(result), content_type="application/json")
                # 添加部门/组中的成员： 
                if 'add_user_ids' in data:
                    add_user_ids = data['add_user_ids'].strip()
                    add_user_ids = add_user_ids.split(',')
                    logger.debug("user:{0} start to add user to dept: dept:{1}:ID:{2}, add_list={3}".\
                                        format(user.username, dept.name, dept.id, str(add_user_ids)))
                    users = User.objects.filter(id__in = add_user_ids) 
                    for user in users: 
                        dept.users.add(user)
                      
                # 移除部门/组中的成员：
                if 'del_user_ids' in data:
                    # 将用户移除到未分类或者指定组
                    del_user_ids = data['del_user_ids'].strip()
                    del_user_ids = del_user_ids.split(',')
                    logger.debug("user:{0} start to del user to dept: dept:{1}:ID:{2}, del_list={3}".\
                                        format(user.username, dept.name, dept.id, str(del_user_ids)))
                    users = User.objects.filter(id__in = del_user_ids) 
                    for user in users:
                        dept.users.remove(user) 
                             
                dept.save()
                result['status'] = SUCCESS
                result['msg'] ='已完成'
            except Dept.DoesNotExist:
                result['status'] = DEPT_NOTFOUND
                result['msg'] ='404 Not found the id' 
        else:
            result['status'] = DEPT_ARGUMENT_ERROR_NEED_ID
            result['msg'] ='Need id  in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")


    def delete(self, request):
        """
        删除
        """
        result = {}
        user = request.user 
        data = request.POST
        if 'id' in data:
            deptid = data['id'] 
            try:
                dept = Dept.objects.get(id=deptid) 
                logger.warning("user:{0} has deleted dept(id:{1}, name:{2}".format(user.username, dept.id, dept.name))
                dept.delete() 
                result['status'] =SUCCESS
                result['msg'] ='已完成'
            except Dept.DoesNotExist:
                result['status'] = ERROR
                result['msg'] ='404 Not found the id' 
        else:
            result['status'] = ERROR
            result['msg'] ='Need id in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")


class DeptUserView(APIView):
    '''部门员工'''
    def get(self,request):
        """
        查询部门的员工
        """
        result ={}
        if 'dept_id' in request.GET:
            dept_id =request.GET['dept_id']
            dept_id = dept_id.split(',')
            members = list(User.objects.filter(depts__in = dept_id)\
                .values_list('username',flat=True))
            result['status'] = SUCCESS
            result['msg'] = members
            return HttpResponse(json.dumps(result),content_type='application/json')
        else:
            result['status'] = ERROR
            result['msg'] = '请提供要查询的工种的id,如果要查询多个部门成员，请用英文逗号隔开'
            return HttpResponse(json.dumps(result),content_type='application/json')