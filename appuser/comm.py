#! -*- coding: utf-8 -*-
import pdb 
from appuser.models import AdaptorUser as User 
from dept.models import Dept
from property.code import ERROR, SUCCESS
from role.models import Role
import uuid
import json
from rest_framework_jwt.views import obtain_jwt_token
from django.http import HttpResponse 
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.views import ObtainJSONWebToken

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER


class WxLoginView(ObtainJSONWebToken):
    """
    仅需要手机号码的授权登录，用于微信、短信验证码等登录
    """
    def post(self, request, *args, **kwargs):
        
        # by default attempts username / passsword combination
        response = super(WxLoginView, self).post(request, *args, **kwargs)
        # token = response.data['token']  # don't use this to prevent errors
        # below will return null, but not an error, if not found :)
         
        content = {}
        # token ok, get user 
        phone = kwargs['kwargs']['phone']
            
        # phone exists in request, try to find user
        try: 
            user = User.objects.get(phone=phone)
            # make token from user found by email
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            content['status'] = SUCCESS
            content['token'] = token
        except :
            content['status'] = ERROR
            content['msg'] = 'User not found'
                   
        return  HttpResponse(json.dumps(content), content_type='application/json')   
       
        
obtain_wx_jwt_token = WxLoginView.as_view()



def set_login_info(user, request, way="app"): 
    jwt_token = ""
    if way == 'wx':
        jwt_token = obtain_wx_jwt_token(request, kwargs={"phone":user.phone}).content.decode('utf-8')
    else:
        jwt_token = obtain_jwt_token(request).render().content.decode('utf-8') 
    jwt_token = json.loads(jwt_token)
    user_dict = {}
    if Role.objects.filter(users=user).exists():
        i = 0
        roles_name = Role.objects.filter(users=user).values('name')
        user_dict['role'] = roles_name[0]['name']
        if len(roles_name) > 1:
            for role_name in roles_name:
                if i < len(roles_name) - 1:
                    i += 1
                    user_dict['role'] = user_dict['role'] + ',' + roles_name[i]['name']
    else:
        user_dict['role'] = []
        
    depts = user.user_depts.all() 
    dept = []
    for dept_item in depts:
        dept_dict = {}
        dept_dict['id'] = dept_item.id
        dept_dict['name'] = dept_item.name
        dept.append(dept_dict)
      
    if user.thumbnail_portait:
        thumbnail_portait = user.thumbnail_portait
    else:
        thumbnail_portait = None


    userauth = {}
    if way == 'pc':
        # 目前只有PC端需要这些权限
        userauth['manage_project'] = user.has_role_perm('projects.projects.can_manage_projects')   
        userauth['manage_role'] =  user.has_role_perm('role.role.can_manage_role')
        userauth['manage_approve'] = user.has_role_perm('task.task.can_approve_task')  
        userauth['dept_manager'] = user.has_role_perm('appuser.baseuser.dept_manager')
        userauth['manage_attendance'] = user.has_role_perm('attendance.attendance.can_manage_attendance')
        userauth['manage_overtime_template'] = user.has_role_perm('wktemplate.extraworkrule.can_manage_extrawork')
        userauth['can_manage_asset_history'] = user.has_role_perm('assets.historyversion.can_manage_asset_history')
        # 属性绑定的权限
        userauth['can_manage_attrsbind'] = user.has_role_perm('attrs.attrsbind.can_manage_attrsbind')
        
        userauth['manage_overtime_approve'] = user.has_role_perm('overtime.overtimeapprove.can_manage_overtime_approve')
        userauth['admin_management'] = user.has_role_perm('appuser.baseuser.admin_management')  
        userauth['is_superuser'] =  user.is_superuser
    context = { 
            'phone':user.phone,
            'openid':user.openid,
            'thumbnail_portait':  thumbnail_portait,
            'uuid': user.uuid,
            'username': user.username,  
            'cid': user.cid,  
            'sex': user.sex,
            'dept': dept,
            'auth': userauth,
            'role': user_dict
        } 
    context = dict(context, **jwt_token)
    return context


def get_user_detail_info(user_item):
    """
    返回前端需要的用户信息列表 
    """
     
    user_dict = {}
    user_dict['uuid'] = user_item.uuid
    user_dict['username'] = user_item.username
    user_dict['email'] = user_item.email
    user_dict['phone'] = user_item.phone
     
    user_dict['sex'] = user_item.sex
    user_dict['thumbnail_portait'] = user_item.thumbnail_portait
    
    user_dict['is_active'] = user_item.is_active
    user_dict['cid'] = user_item.cid 
    return user_dict

def get_simple_user_info(users):
    """
    返回前端需要的用户信息列表:只返回id、uuid、username、phone 
    """
    user_list = []
    for user_item in users:
        user_dict = {}
        user_dict['id'] = user_item.id
        user_dict['username'] =  user_item.username if user_item.username is not None   else ""
        user_dict['uuid'] = user_item.uuid
        user_dict['phone'] = user_item.phone 
        user_list.append(user_dict) 
    return user_list


def get_user_info(users):
    """
    返回前端需要的用户信息列表 
    """
    user_list = []
    for user_item in users:
        user_dict = {}
        user_dict['id'] = user_item.id
        user_dict['username'] = user_item.username
        user_dict['email'] = user_item.email
        user_dict['phone'] = user_item.phone
        depts = user_item.user_depts.all() 
        dept = []
        for dept_item in depts:
            dept_dict = {}
            dept_dict['id'] = dept_item.id
            dept_dict['name'] = dept_item.name
            dept.append(dept_dict)
       
        user_dict['dept'] = dept
       

        if Role.objects.filter(users=user_item).exists():
            i = 0
            roles_name = Role.objects.filter(users=user_item).values('name')
            user_dict['role'] = roles_name[0]['name']
            if len(roles_name) > 1:
                for role_name in roles_name:
                    if i < len(roles_name)-1:
                        i += 1
                        user_dict['role'] = user_dict['role'] + ',' + roles_name[i]['name']
        else:
            user_dict['role'] = None
        user_dict['sex'] = user_item.sex
        
        
        user_dict['is_active'] = user_item.is_active
        user_list.append(user_dict) 
    return user_list

def get_depts_users_ids(depts):
    """
    获取某部门所有的用户id列表
    """
    users = User.objects.filter(depts__id__in = depts)
    userids = [user.id for user in users] 
    return userids