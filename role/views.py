#! -*- coding:utf-8 -*-
import json
import pdb  
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.translation import ugettext as _
from role.models import Role  
from django.db.models import Q
from appuser.models import AdaptorUser as User  
from django.utils import timezone 
from community.models import Community
from community.comm import getUserCommunities
from rest_framework.views import APIView
from role.comm import RoleMgr
from django.views import View
from django.contrib.auth.models import Permission
from property.code import *
from appuser.comm import get_user_info
from common.logutils import getLogger 
logger = getLogger(True, 'role', False)


def get_role_dict(role):
    """
    返回role的字典实例
    字典格式：
     {
                    "id":role.id
                    "name":role.name
                    }
    """

    role_dict = {
        "id":role.id,
        "name":role.name,
        "sort":role.role_sort,
        'role_type':role.role_type
    }
    return role_dict


def check_name_exist(name, community, roleid=None):
    """检查名称是否已经存在，如果存在返回True，否则返回False"""
    if roleid: 
        return Role.objects.filter(name=name, community=community).exclude(id=roleid).exists()
    else:
        return Role.objects.filter(name=name, community=community).exists()

class RoleInitView(View):
    def post(self, request):
        # 内置角色初始化
        """
            role_json =[
            ["物业", 2, None, None, "wuye",  0],
            ["业主", 2, None, None, "yezhu",  0],
            ["租户", 2, None, None, "zuhu",  0],
        ]
        """ 
        role_json_ls = request.POST['role'] 
        for role_item in json.loads(role_json_ls):
            role, created = Role.objects.get_or_create(code = role_item[2] )
            role.name = role_item[0]
            role.role_type = role_item[1]
            role.role_sort = role.INTERNAL # 都是内置角色 
            role.save()

        result = {
            'status':SUCCESS,
            "msg" : "角色初始化成功"
        }
        return HttpResponse(json.dumps(result), content_type="application/json")


class PermsView(APIView): 
    def get(self, request):
        content = {}
        user = request.user 
        content['status'] = SUCCESS
        kwargs = {}
        if 'roleid' in request.GET:
            kwargs['id'] = request.GET['roleid']
            try:
                role = Role.objects.get( ** kwargs)
                perms = role.permissions.all()
            except Role.DoesNotExist:
                content['status'] = ERROR
                content['msg'] = "角色未找到"
                return HttpResponse(json.dumps(content), content_type="application/json")
        elif 'codename' in request.GET:
            codename = request.GET['codename'].strip()
            perms = Permission.objects.filter( name__icontains = codename,content_type__id__gte = 10 )
        else :
            perms = Permission.objects.filter(content_type__id__gte = 10)
        perms_list = []
        for perm in perms:
            perm_dict = {}
            perm_dict['id'] = perm.id
            perm_dict['name'] = perm.name
            perm_dict['codename'] = perm.codename
            perms_list.append(perm_dict)
        
        content['msg'] = perms_list
        return HttpResponse(json.dumps(content), content_type="application/json")


class RoleView(APIView):
 
    def get(self, request):
        result = {}  
        user = request.user
        community = None
        # 小区uuid是必须参数
        if 'communityuuid' in request.GET:
            #  物业获取自己的员工列表
            communityuuid = request.GET['communityuuid'].strip() 
            try:
                community = Community.objects.get(uuid = communityuuid)
                perm = user.has_community_perm('role.role.can_manage_role', community)
                result['auth'] = {
                    "manage_role":perm 
                }
                if 'minerole' in request.GET:
                    # 获取当前用户的角色列表 
                    result['msg'] = list(Role.objects.filter(users=user).values("name","code"))
                    communityuuids = getUserCommunities(user)
                    if communityuuid in communityuuids:
                        result['is_staff'] = 1
                    else:
                        result['is_staff'] = 0
                    result['status'] = SUCCESS
                    return HttpResponse(json.dumps(result), content_type="application/json")
                if not perm:
                    return HttpResponse('Forbidden', status=403)
            except Community.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = "未找到相关小区" 
                result['auth'] = {
                    "manage_role":False
                }
        else:
            # 超级用户可以不带communityuuid
            if not user.is_superuser:
                result['status'] = ERROR
                result['msg'] = "缺少小区uuid" 
                result['auth'] = {
                    "manage_role":False
                }
                return HttpResponse(json.dumps(result), content_type="application/json")
        result['auth']['is_superuser'] = user.is_superuser
        if 'id' in request.GET:
            role_id = request.GET['id']
            try:
                role_id = int(role_id)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = 'id not int'
                return HttpResponse(json.dumps(result), 
                       content_type="application/json") 
            try: 
                role = Role.objects.get(id=role_id)
                result['status'] = SUCCESS
                result['msg'] = get_role_dict(role)
                result['users'] = get_user_info(role.users.all())

            except Role.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '404 Not found the id'
        
        else:
            if user.is_superuser:
                # 超级用户获取所有角色
                roles = Role.objects.all()
            else:
                roles = Role.objects.filter(community = community)
            roles_list = []
            for role in roles:
                roles_list.append(get_role_dict(role))
            result['msg'] = roles_list
            result['status'] = SUCCESS

        return HttpResponse(json.dumps(result), content_type="application/json")

    
    def post(self, request):
        """
        新建角色
        """
        result = {}
        user = request.user 
        # 验证权限：是否有管理权限  
        # 小区uuid是必须参数
        community = None
        if 'communityuuid' in request.POST:
            #  物业获取自己的员工列表
            communityuuid = request.POST['communityuuid'].strip() 
            try:
                community = Community.objects.get(uuid = communityuuid)
                perm = user.has_community_perm('role.role.can_manage_role', community)
                result['auth'] = {
                    "manage_role":perm 
                }
                if not perm:
                    return HttpResponse('Forbidden', status=403)
            except Community.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = "未找到相关小区" 
                result['auth'] = {
                    "manage_role":False
                }
        else:
            # 超级用户可以不带communityuuid
            if not user.is_superuser:
                result['status'] = ERROR
                result['msg'] = "缺少小区uuid" 
                result['auth'] = {
                    "manage_role":False
                }
                return HttpResponse(json.dumps(result), content_type="application/json")
        result['auth']['is_superuser'] = user.is_superuser
       
        # 新建
        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST
        if 'method' in data:
            method = data['method'].lower()
            if method == 'put':  # 修改
                return self.put(request, community)
            elif method == 'delete':  # 删除
                return self.delete(request)

        # 新建角色
        # name字段是必须的 
        if 'name' in data:
            name = data['name'].strip()
            if len(name) > 200:
                result['status'] = ERROR
                result['msg'] = '角色名称太长'
                return HttpResponse(json.dumps(result), content_type="application/json")
            elif len(name) == 0:
                result['status'] = ERROR
                result['msg'] = '角色名称为空'
                return HttpResponse(json.dumps(result), content_type="application/json")
            elif check_name_exist(name, community):
                # 角色名称已经存在
                result['status'] = ERROR
                result['msg'] = '角色名称重复'
                return HttpResponse(json.dumps(result), content_type="application/json")
        #没有name
        else:
            result['status'] = ERROR
            result['msg'] = 'post里没有角色名称'
            return HttpResponse(json.dumps(result),content_type="application/json")
        #创建角色
        role = Role.objects.create(name = name, community = community)
        if 'role_sort' in data:
            role_sort = data['role_sort']
            try:
                role_sort = int(role_sort)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = '角色分类不是int'
                role.delete()
                return HttpResponse(json.dumps(result), content_type="application/json")
            if role_sort not in role.get_role_sort_list():
                result['status'] = ERROR
                result['msg'] = '角色分类不被允许'
                role.delete()
                return HttpResponse(json.dumps(result), content_type="application/json")
            else:
                role.role_sort = role_sort
        if 'role_type' in data:
            role_type = data['role_type']
            try:
                role_type = int(role_type)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = '角色id不是int'
                role.delete()
                return HttpResponse(json.dumps(result), content_type="application/json")
            if role_type not in role.get_role_type_list():
                result['status'] = ERROR
                result['msg'] = '角色类型不被允许'
                role.delete()
                return HttpResponse(json.dumps(result), content_type="application/json")
            else:
                role.role_type = role_type 
                role.save()
        if 'perm_ids' in data:
            # 添加权限
            perm_ids = data['perm_ids']
            if isinstance(perm_ids, str):
                perm_ids = perm_ids.split(",")
            perms = Permission.objects.filter(id__in = perm_ids) 
            for perm in perms:
                role.permissions.add(perm) 
            
        result['status'] = SUCCESS
        result['msg'] = '创建成功'
        return HttpResponse(json.dumps(result), content_type="application/json")

    def put(self, request, community):
        """
        修改：为角色绑定或者解绑用户
        内置角色，不能删除，不能修改
        自定义角色，支持删除和修改
        """
        result = {}
        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST
        if 'id' in data:
            roleid = data['id']
            try:
                roleid = int(roleid)
                role = Role.objects.get(id=roleid)
                # 角色是自定义角色，可以修改
                if 'name' in data:
                    if role.role_sort == role.DEFINE:
                        name = data['name']
                        if len(name) > 200:
                            result['status'] = ERROR
                            result['msg'] = '角色名称太长'
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        elif len(name) == 0:
                            result['status'] = ERROR
                            result['msg'] = '角色名称为空'
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        elif check_name_exist(name,community, roleid):
                            # 名称已经存在
                            result['status'] = ERROR
                            result['msg'] = '角色名称重复'
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        #修改角色
                        role.name = name
                    # 内置角色不允许修改角色名称
                    else:
                        result['status'] = ERROR
                        result['msg'] = '内置角色不允许修改角色名称'
                        return HttpResponse(json.dumps(result), content_type="application/json")

                if 'add_userids' in data:
                    # 添加用户角色
                    add_userids = data['add_userids']
                    add_userids_list = add_userids.split(',')
                    if role.role_type == Role.UNIQUE:
                        if len(add_userids_list) > 1:
                            result['status'] = ERROR
                            result['msg'] = u'唯一性角色最多绑定一个用户'
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        elif len(role.users.all()) > 0:
                            result['status'] = ERROR
                            result['msg'] = u'唯一性角色已经绑定了一个用户'
                            return HttpResponse(json.dumps(result), content_type="application/json")
                    add_users = User.objects.filter(id__in=add_userids_list)
                    for add_user in add_users:
                        role.users.add(add_user)
                if 'del_userids' in data:
                    # 删除用户角色
                    del_userids = data['del_userids']
                    del_userids_list = del_userids.split(',')
                    del_users = User.objects.filter(id__in = del_userids_list)
                    for del_user in del_users:
                        role.users.remove(del_user)
                if 'role_type' in data:
                    role_type = data['role_type']
                    try:
                        role_type = int(role_type)
                    except ValueError:
                        result['status'] = ERROR
                        result['msg'] = 'role id value is not int'
                        role.delete()
                        return HttpResponse(json.dumps(result), content_type="application/json")

                    if role_type not in role.get_role_type_list():
                            result['status'] = ERROR
                            result['msg'] = 'role type not allowed'
                            return HttpResponse(json.dumps(result), content_type="application/json")
                    else:
                        if role_type == Role.UNIQUE:
                            if role.role_type == Role.UNIQUE:
                                # 角色原来就是唯一性角色，不需要做处理
                                pass
                            else:
                                # 角色原来就是多用户角色，删除原来绑定的用户
                                for del_user in role.users.all():
                                    role.users.remove(del_user)
                        role.role_type = role_type

                if 'add_perm_ids' in data:
                    # 添加权限
                    add_perm_ids = data['add_perm_ids']
                    if isinstance(add_perm_ids, str):
                        add_perm_ids = add_perm_ids.split(",")
                    perms = Permission.objects.filter(id__in = add_perm_ids)
                    for perm in perms:
                        role.permissions.add(perm)
                if 'del_perm_ids' in data:
                    # 删除权限
                    del_perm_ids = data['del_perm_ids']
                    if isinstance(del_perm_ids, str):
                        del_perm_ids = del_perm_ids.split(",")
                    perms = Permission.objects.filter(id__in = del_perm_ids)
                    for perm in perms:
                        role.permissions.remove(perm)

                role.save()
                result['status'] = SUCCESS
                result['msg'] = '已完成'

                return HttpResponse(json.dumps(result), content_type="application/json")

            except Role.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '404 Not found the id'
        #没有传id
        else:
            result['status'] = ERROR
            result['msg'] = 'Need id in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self, request):
        """
        删除
        """
        result = {}
        user = request.user
        data = request.POST
        if 'id' in data:
            role_id = data['id']
            try: 
                role = Role.objects.get(id=role_id)
                # 角色是自定义角色，可以删除；若是内置角色报错
                if role.role_sort == role.DEFINE:
                    logger.warning("user:{0} has deleted role(id:{1}, name:{2}". \
                                   format(user.username, role.id, role.name))
                    role.delete()
                    result['status'] = SUCCESS
                    result['msg'] = '已完成'
                else:
                    result['status'] = ERROR
                    result['msg'] = '角色为内置角色，不能删除'
                    return HttpResponse(json.dumps(result), content_type="application/json")
            except Role.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '404 Not found the id'
        else:
            result['status'] = ERROR
            result['msg'] = 'Need id in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")
