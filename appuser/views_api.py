# -*- coding: utf-8 -*- 
from common.logutils import getLogger
import time
import traceback
import requests
import uuid
from datetime import datetime
import configparser
from django.shortcuts import render
from django.http import HttpResponse 
from django.conf import settings 
import pdb
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import Group
import os
from django.views import View
from appuser.models import AdaptorUser as User
from appuser.models import VerifyCode
from django.utils.translation import ugettext as _
import json
import random
import string
from django.utils import timezone
from common.fileupload import FileUpload
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, HttpResponseForbidden 
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import  permission_classes
from rest_framework.decorators import api_view

from appuser.verify import check_email_exist, check_name_exist,  check_name, check_email, \
     check_number, check_bool, check_sex, check_phone_exist
from common.utils import verify_phone, verify_email
from dept.views import get_dept_dict
from .form import UploadPortrainForm, GroupForm, UserForm

from django.contrib import auth
from django.contrib.auth.decorators import login_required
from community.models import Staff, Community
# from socialoauth import SocialSites,SocialAPIError
from appuser.comm import get_user_info, get_user_detail_info, get_simple_user_info
from dept.models import Dept
from basedatas.bd_comm import Common
from mobile.detectmobilebrowsermiddleware import DetectMobileBrowser
from appuser.models import InvalidUsername 


from role.models import Role
from property.code import *

dmb = DetectMobileBrowser()
comm = Common()

logger = getLogger(True, 'users', False)
 
class UserView(APIView):
 
    def get(self, request):
        content = {}
        user = request.user
        kwargs = {} 
        if 'auth' in request.GET:
            # 如果参数中有社区的信息，并且不是超级用户，
            # 则认为是物业管理人员，那么只有IT manager有权限，另外在该小区中分配了当前权限的用户也有
            # 获取当前用户是否有用户管理权限
             
            perm = user.has_role_perm('appuser.baseuser.admin_management')
            content['status'] = SUCCESS
            content['msg'] = {
                "admin_management":perm
            }
            return HttpResponse(json.dumps(content), content_type='application/json')
        
        community_kwargs = {}

        if 'username' in request.GET:
            username = request.GET['username'].strip()
            kwargs['username__icontains'] = username
            community_kwargs['user__username__icontains'] = username
 
        if 'mine' in request.GET: 
            content['status'] = SUCCESS
            content['msg'] = get_user_detail_info(user)
            return HttpResponse(json.dumps(content), content_type='application/json')
        if 'deptid' in request.GET:
            deptid = request.GET['deptid']
            try:
                deptid = int(deptid)
                kwargs['depts__id'] = deptid
            except ValueError:
                pass

        if 'virtual' in request.GET:
            virtual = request.GET['virtual'].strip()
            kwargs['virtual'] = virtual

        if 'permissions' in request.GET:

            role_list = Role.objects.filter(users=user)
            if role_list:
                perms_list = []
                for role in role_list:
                    perms = role.permissions.all()
                    for perm in perms:
                        perm_dict = {}
                        perm_dict['id'] = perm.id
                        perm_dict['name'] = perm.name
                        perm_dict['codename'] = perm.codename
                        perms_list.append(perm_dict)
                perms_result = []
                for i in perms_list:
                    if not i in perms_result:
                        perms_result.append(i)
                print(perms_result)

                return HttpResponse(json.dumps(perms_result), content_type='application/json')

            else:
                content['msg'] = '用户未分配权限'
                return HttpResponse(json.dumps(content), content_type='application/json')
        else:
            users = User.objects.filter(**kwargs)
        user_list = []
        if 'simple' in request.GET:
            user_list = get_simple_user_info(users)
        else:
            user_list = get_user_info(users)

        return HttpResponse(json.dumps(user_list), content_type='application/json')
 
    def post(self, request):
        """
        新建用户
        """
        content = {
            'status': ERROR
        }
        user = request.user

        data = request.POST

        if 'method' in data:
            method = data['method'].lower().strip()
            if method == 'put':  # 修改
                return self.put(request)
            if method == 'delete':  # 删除
                return self.delete(request)

        # 判断是否有管理权限
        if not user.has_role_perm('appuser.baseuser.admin_management'):
            return HttpResponse('Forbidden', status=403)
        else:
            if 'username' in data :
                # 创建用户
                newuser = User()
                username = data['username'].strip()
                 
                result = check_name(username)
                if not result:
                    if check_name_exist(username):
                        content['msg'] = "用户名重复不可使用"
                        return HttpResponse(json.dumps(content), content_type="application/json")
                    else:
                        newuser.username = username
                else:
                    content['msg'] = "用户名长度需要在0与128之间"
                    return HttpResponse(json.dumps(content), content_type="application/json")

                
                if 'phone' in data:
                    phone = data['phone'].strip()
                     
                    if len(phone) :    
                        # 检查phone格式是否正确
                        result = verify_phone(phone)
                        if result:
                            # 检查phone是否重复
                            if check_phone_exist(phone):
                                content['msg'] = '手机号码已被注册不可使用'
                                return HttpResponse(json.dumps(content), content_type="application/json")
                            else:
                                newuser.phone = phone
                        else:
                            content['msg'] = '手机号码格式错误'
                            return HttpResponse(json.dumps(content), content_type="application/json")
 
                if 'virtual' in data:
                    virtual = data['virtual'].strip()
                    newuser.virtual = virtual


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
                    
                    
                if 'password' in data:
                    pwd = data['password'].strip()
                    # 判断用户输入密码是否为空，若为空则返回提示
                    if pwd:
                        newuser.set_password(pwd)
                    else:
                        content['msg'] = '未输入密码'
                        return HttpResponse(json.dumps(content), content_type="application/json")
                    
                newuser.uuid = uuid.uuid4() 
                newuser.save()
                if 'img' in request.FILES:
                    # 获取主图
                    imagefile = request.FILES['img']
                    pre = datetime.now().strftime("%Y%m%d%H%M%S%f")
                    file_name, file_extension = os.path.splitext(
                        imagefile.name)
                    filename = pre+file_extension
                    FileUpload.upload(imagefile,
                                        os.path.join('portrait', str(user.id)),
                                        filename)
                    filepath = os.path.join('portrait', str(user.id), filename  )
                    
                    newuser.thumbnail_portait = filepath
                    newuser.save()

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
        data = request.POST
 
        # 管理员修改用户信息
        
        user = request.user # 默认修改自己的

        if 'uuid' in data and user.has_role_perm('appuser.baseuser.admin_management'):
            useruuid = data['uuid'] 
            try:
                user = User.objects.get(uuid=useruuid)
            except User.DoesNotExist:
                content['msg'] = '找不到用户id'
                return HttpResponse(json.dumps(content), content_type="application/json")


        if 'username' in data :  
            username = data['username'].strip()
                
            result = check_name(username)
            if not result:
                if check_name_exist(username, user.id):
                    content['msg'] = "用户名重复不可使用"
                    return HttpResponse(json.dumps(content), content_type="application/json")
                else:
                    user.username = username
            else:
                content['msg'] = "用户名长度需要在0与128之间"
                return HttpResponse(json.dumps(content), content_type="application/json")



        # 获取name字段 
        # 获取email字段
        if 'email' in data:
            email = data['email'].strip()
            # 检查email格式是否正确
            result = verify_email(email)
            if result:
                # 验证email是否重复
                if check_email_exist(email, user.id):
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
                    if check_phone_exist(phone, user.id):
                        content['msg'] = '手机号码已被注册不可使用'
                        return HttpResponse(json.dumps(content), content_type="application/json")
                    else:
                        user.phone = phone
                else:
                    content['msg'] = '手机号码格式错误'
                    return HttpResponse(json.dumps(content), content_type="application/json")
            else:
                user.phone = phone # 设置手机号码为空

        
        if 'virtual' in data:
            virtual = data['virtual'].strip()
            user.virtual = virtual


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
         
             
        if 'cid' in data:
            cid = data['cid'].strip()
            # cid
            if cid:
                user.cid = cid

        if 'wxusername' in data:
            # 微信用户名，如果将来有真实姓名，会被替换
            if user.username == ""  or user.username is None:
                user.username = data['wxusername'] 

        if 'wximage' in data:
            # 微信的用户头像
            wximage = data['wximage']
            r = requests.get(wximage)
            try:
                os.remove(os.path.join(settings.FILEPATH,user.thumbnail_portait) )
            except IOError:
                pass
            pre = datetime.now().strftime("%Y%m%d%H%M%S%f")
             
            user.thumbnail_portait = os.path.join('portrait', str( user.id), pre+".png") 
            filepath = os.path.join(settings.FILEPATH, user.thumbnail_portait)
            print(filepath)
            with open(filepath,'wb') as f: 
                f.write(r.content) 
                f.close()
        
        if 'img' in request.FILES:
            # 获取主图
            imagefile = request.FILES['img']
            pre = datetime.now().strftime("%Y%m%d%H%M%S%f")
            file_name, file_extension = os.path.splitext(
                imagefile.name)
            filename = pre+file_extension
            FileUpload.upload(imagefile,
                                os.path.join('portrait', str(user.id)),
                                filename)
            filepath = os.path.join('portrait', str(user.id), filename  )
            if user.thumbnail_portait:
                # 删除旧的缩略图
                imgpath = os.path.join(settings.FILEPATH, user.thumbnail_portait )
                if os.path.isfile(imgpath): 
                    os.remove(imgpath)
            user.thumbnail_portait = filepath

            
        user.save()
        content['status'] = SUCCESS
        content['msg'] = '修改成功' 
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
        data = request.POST

        user = request.user
        # 判断用户是否具有管理员权限
        if user.has_role_perm('appuser.baseuser.admin_management'):
            # 管理员修改用户信息
            if 'ids' in data:
                userids = data['ids'].split(",")
                users = User.objects.filter(id__in=userids)
                users.delete()
                content['status'] = SUCCESS
                content['msg'] = '删除成功'
                return HttpResponse(json.dumps(content), content_type="application/json")
            else:
                content['msg'] = '缺少ids参数'
                return HttpResponse(json.dumps(content), content_type="application/json")
        else:
            return HttpResponse('Forbidden', status=403)

 
class UserRoleView(APIView):
    """
    用户角色管理
    """ 
    def get(self, request):
        content = {}  
        user = request.user
        if 'userid' in request.GET:
            userid = request.GET['userid'].strip()
            user = User.objects.get(id=userid)
        
        user_dict = {}
        user_dict['id'] = user.id
        user_dict['username'] = user.username
        user_dict['roles'] = []
        role_list = Role.objects.filter(users=user)
        for role in role_list:
            role_dict = {}
            role_dict['id'] = role.id
            role_dict['name'] = role.name
            user_dict['roles'].append(role_dict)
        return HttpResponse(json.dumps(user_dict), content_type='application/json')
 
    def post(self, request):
        """
        为用户添加角色
        """
        result = {}
        user = request.user
        # 判断是否有role角色管理权限
        if not user.has_perm('dept.can_manage_role'):
            return HttpResponseForbidden()
        # 新建
        if len(request.POST) == 0:
            request.POST = request.data
        if 'method' in request.POST:
            method = request.POST['method'].lower()
            if method == 'put':  # 修改
                return self.put(request)
            elif method == 'delete':  # 删除
                return self.delete(request)

        # 用户id和角色id列表
        if 'userid' in request.POST and 'roleids' in request.POST:
            userid = request.POST['userid'].strip()
            roleids = request.POST['roleids'].strip()
            logger.debug("userid:{0}, roleids:{1}".format(userid, roleids))

            # 数据验证开始
            try:
                userid = int(userid)
            except ValueError:
                result['status'] = VALUEERROR_INT
                result['msg'] = 'Need int for userid.'
                return HttpResponse(json.dumps(result), content_type="application/json")
            roleids = list(set(roleids.split(',')))
            if not roleids:
                result['status'] = USER_ROLEID_EMPTY
                result['msg'] = 'role id list cannot be null.'
                return HttpResponse(json.dumps(result), content_type="application/json")
            else:
                try:
                    roleids = [int(roleid) for roleid in roleids]
                except ValueError:
                    result['status'] = USER_ROLE_ID_VALUE_ERROR
                    result['msg'] = 'role id is valid string.'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                    # 数据验证结束

            try:
                asigner = User.objects.get(id=userid)
                roles = Role.objects.filter(id__in=roleids)
                logger.debug("get {0} roles".format(len(roles)))
                for role in roles:
                    asigner.role.add(role)
                logger.warning("add user :{0} asign user:{1} with roles:{2}".
                               format(user.username, asigner.username, str(roleids)))
                result['status'] = SUCCESS
                result['msg'] = '已完成'
            except User.DoesNotExist:
                result['status'] = USER_NOT_FOUND
                result['msg'] = 'user not found.'
                return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = USER_ARGUMENT_ERROR_NEED_USERID_ROLEIDS
            result['msg'] = 'Need userid and roleids in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")
 
    def delete(self, request):
        """
        移除用户角色
        """
        result = {}
        user = request.user
        # 用户id和角色id列表
        if 'userid' in request.POST and 'roleids' in request.POST:
            userid = request.POST['userid'].strip()
            roleids = request.POST['roleids'].strip()
            logger.debug(
                "delete userid:{0}, roleids:{1}".format(userid, roleids))

            # 数据验证开始
            try:
                userid = int(userid)
            except ValueError:
                result['status'] = VALUEERROR_INT
                result['msg'] = 'Need int for userid.'
                return HttpResponse(json.dumps(result), content_type="application/json")
            roleids = list(set(roleids.split(',')))
            if not roleids:
                result['status'] = USER_ROLEID_EMPTY
                result['msg'] = 'role id list cannot be null.'
                return HttpResponse(json.dumps(result), content_type="application/json")
            else:
                try:
                    print(roleids)
                    roleids = [int(roleid) for roleid in roleids]
                except ValueError:
                    result['status'] = USER_ROLE_ID_VALUE_ERROR
                    result['msg'] = 'role id is valid string.'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                    # 数据验证结束

            try:
                asigner = User.objects.get(id=userid)
                roles = Role.objects.filter(id__in=roleids)
                logger.debug("remove: get {0} roles".format(len(roles)))
                for role in roles:
                    asigner.role.remove(role)
                logger.warning("user :{0} asign user:{1} with roles:{2}".
                               format(user.username, asigner.username, str(roleids)))
                result['status'] = SUCCESS
                result['msg'] = '已完成'
            except User.DoesNotExist:
                result['status'] = USER_NOT_FOUND
                result['msg'] = 'user not found.'
                return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = USER_ARGUMENT_ERROR_NEED_USERID_ROLEIDS
            result['msg'] = 'Need userid and roleids in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")


# list all user portraits in a page
def list_users(request):
    if not request.user.is_superuser:
        return HttpResponse("没有权限...")
    isMble = dmb.process_request(request)

    context = {}

    # get user list
    user_list = User.objects.all().order_by('-date')

    context = {'user_list': user_list}
    if isMble:
        return render(request, 'users.html', context)
    else:
        return render(request, 'users.html', context)


# list all user for administrator to manage
def admin_list_users(request):
    isMble = dmb.process_request(request)

    context = {}

    # get user list
    user_list = User.objects.all().order_by('-date')

    context = {'user_list': user_list}
    if isMble:
        return render(request, 'user/m_userslist.html', context)
    else:
        return render(request, 'user/userslist.html', context)


def admin(request, userid, super):
    if not request.user.is_superuser:
        return HttpResponse("没有权限...")
    result = {}
    try:
        user = User.objects.get(id=userid)
        user.is_superuser = int(super)
        user.save()
        result['status'] = 'OK'
        result['msg'] = '设置成功...'
    except User.DoesNotExist:
        result['status'] = ERROR
        result['msg'] = 'Not found...'

    return HttpResponse(json.dumps(result), content_type='application/json')


def staff(request, userid, staff):
    if not request.user.is_superuser:
        return HttpResponse("没有权限...")
    result = {}
    try:
        user = User.objects.get(id=userid)

        user.is_staff = int(staff)
        user.save()
        result['status'] = 'OK'
        result['msg'] = '设置成功...'
    except User.DoesNotExist:
        result['status'] = ERROR
        result['msg'] = 'Not found...'

    return HttpResponse(json.dumps(result), content_type='application/json')


@csrf_exempt
@login_required
def portrait(request):
    # response for the social site user login
    '''
    socialsites = SocialSites(settings.SOCIALOAUTH_SITES)

    if request.GET.get('state',None)=='socialoauth':

        auth.logout(request) #logout first

        access_code = request.GET.get('code')

        qq_object = socialsites.get_site_object_by_name('qq')
        try:
            qq_object.get_access_token(access_code)
            fake_email = qq_object.uid+"@qq.com"
            try:
                #user exist
                User.objects.get(email=fake_email)
            except User.DoesNotExist:
                #user doesn't exist, need add it first
                social_user = User(name=qq_object.name,email=fake_email,head_portrait=qq_object.avatar,social_user_status=1,social_site_name=1,social_user_id=qq_object.uid)
                social_user.set_password(qq_object.uid)
                social_user.date = timezone.now()
                social_user.save()

            user = auth.authenticate(email=fake_email, password=qq_object.uid)    
            request.user = user
            auth.login(request, user)
            return HttpResponseRedirect("/")
        except SocialAPIError as e:
            print (e )
    '''
    isMobile = dmb.process_request(request)

    result = {}
    if request.method == 'POST':
        user = request.user

        # remove the old portraint

        if 'media' in user.head_portrait.name[1:]:
            oldportraint = os.path.join(
                settings.MEDIA_ROOT, user.head_portrait.name[7:])
        else:
            oldportraint = os.path.join(
                settings.MEDIA_ROOT, user.head_portrait.name[1:])

        if os.path.isfile(oldportraint):
            os.remove(oldportraint)
            # rename the fake portrait
            if 'media' in user.fake_head_portrait.name[1:]:
                os.rename(os.path.join(settings.MEDIA_ROOT,
                                       user.fake_head_portrait.name[7:]), oldportraint)
            else:
                os.rename(os.path.join(settings.MEDIA_ROOT,
                                       user.fake_head_portrait.name[1:]), oldportraint)
        user.head_portrait = user.fake_head_portrait
        user.is_head_portrait = True
        user.save()

        result['status'] = 'OK'
        result['msg'] = '头像上传成功...'
        return HttpResponse(json.dumps(result), content_type='application/json')
    else:
        form = UploadPortrainForm()
        form.fields['portrain'].label = '点击上传头像'
        admin_granted = has_admin_perm(request.user)

        context = {
            'form': form.as_ul(),
            'admin_granted': admin_granted,
        }
        if isMobile:
            return render(request, 'user/m_change_portrait.html', context)
        else:
            return render(request, 'user/change_portrait.html', context)


@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def upload_fake_portrait(request):
    isMobile = dmb.process_request(request)

    result = {}
    if request.method == 'POST':

        form = UploadPortrainForm(request.POST, request.FILES)
        if form.is_valid():
            usesr = request.user

            # remove the old portraint
            if 'media' in usesr.head_portrait.name[1:]:
                oldportraint = os.path.join(
                    settings.MEDIA_ROOT, usesr.head_portrait.name[7:])
            else:
                oldportraint = os.path.join(
                    settings.MEDIA_ROOT, usesr.head_portrait.name[1:])

            if os.path.isfile(oldportraint):
                os.remove(oldportraint)

            code = ''.join(random.choice(
                string.ascii_lowercase + string.digits) for i in range(4))
            filename = handle_uploaded_file(
                request.FILES['portrain'], str(usesr.id) + '_' + code)

            # usesr.is_head_portrait = False
            usesr.head_portrait = filename.replace('\\', '/')
            usesr.is_head_portrait = True
            usesr.save()
            result['status'] = 'OK'
            result['msg'] = _('Saved')  # '头像上传成功...'
            result['file'] = filename
        else:
            result['status'] = ERROR
            result['msg'] = _('Please select a picture first')  # '请先选择图片..'

    else:
        result['status'] = ERROR
        result['msg'] = _('Please select a picture first')  # '请先选择图片..'

    return HttpResponse(json.dumps(result), content_type='application/json')


def handle_uploaded_file(f, userid):
    # with open(os.path.join(settings.MEDIA_ROOT, 'portrait'), 'wb+') as destination:

    filename = str(userid) + '.png'

    with open(os.path.join(settings.MEDIA_ROOT, 'portrait', filename), 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return os.path.join(settings.MEDIA_URL, 'portrait', filename)


def grouplist(request):
    isMobile = dmb.process_request(request)
    if request.user.is_anonymous():
        return comm.redirect_login_path(isMobile, request)

    # get group list
    group_list = Group.objects.all()

    context = {'group_list': group_list}
    if isMobile:
        return render(request, 'user/m_grouplist.html', context)
    else:
        return render(request, 'user/grouplist.html', context)


def newgroup(request):
    isMobile = dmb.process_request(request)
    if request.user.is_anonymous():
        return comm.redirect_login_path(isMobile, request)

    if not has_admin_perm(request.user):
        context = {
            'not_granted': True,
        }
    else:
        if request.method == 'POST':
            form = GroupForm(request.POST)

            if form.is_valid():
                new_group = form.save()
                form = GroupForm()
                context = {
                    'form': form,
                    'saved': True,
                    'validate': True,
                }
            else:
                # invalide form
                form = GroupForm()
                context = {
                    'form': form,
                    'validate': False,
                }
        else:
            form = GroupForm()
            context = {
                'form': form,
                'validate': True,
            }
    if isMobile:
        return render(request, 'user/m_group.html', context)
    else:
        return render(request, 'user/m_group.html', context)


def modify_group(request, groupid):
    isMobile = dmb.process_request(request)
    if request.user.is_anonymous():
        return comm.redirect_login_path(isMobile, request)

    if not has_admin_perm(request.user):
        context = {
            'not_granted': True,
        }
    else:
        try:
            group = Group.objects.get(pk=groupid)
            if request.method == 'POST':
                form = GroupForm(request.POST, instance=group)
                if form.is_valid():
                    form.save()
                    context = {
                        'form': form,
                        'saved': True,
                        'validate': True,
                    }
                else:
                    # invalide form
                    form = GroupForm()
                    context = {
                        'form': form,
                        'validate': False,
                    }
            else:
                form = GroupForm(instance=group)
                context = {
                    'form': form,
                    'validate': True,
                }
        except Group.DoesNotExist:
            context = {
                'usernotexist': True,
            }

    if isMobile:
        return render(request, 'user/m_group.html', context)
    else:
        return render(request, 'user/m_group.html', context)


def has_admin_perm(user):
    '''
       if a user has permission to manage user, group and permission
       if has, return True, else return False
    '''
    if user.is_superuser:
        return True
    else:
        return user.has_perm('appuser.admin_management')


def modify_user(request, userid):
    isMobile = dmb.process_request(request)
    if request.user.is_anonymous():
        return comm.redirect_login_path(isMobile, request)

    if not has_admin_perm(request.user):
        context = {
            'not_granted': True,
        }
    else:
        try:
            user = User.objects.get(pk=userid)
            if request.method == 'POST':
                form = UserForm(request.POST, instance=user)
                if form.is_valid():
                    form.save()
                    context = {
                        'form': form,
                        'saved': True,
                        'validate': True,
                    }
                else:
                    # invalide form
                    form = UserForm()
                    context = {
                        'form': form,
                        'validate': False,
                    }
            else:
                form = UserForm(instance=user)
                context = {
                    'form': form,
                    'validate': True,
                }
        except User.DoesNotExist:
            context = {
                'usernotexist': True,
            }

    if isMobile:
        return render(request, 'user/m_change_user.html', context)
    else:
        return render(request, 'user/change_user.html', context)


'''
new frame start
'''


def usernames(request, username):
    # 验证用户名是否唯一
    if request.method == 'GET':
        msg = User.objects.uniqueUsername(username)
        if msg:
            invalidnames = InvalidUsername.objects.filter(username=username)
            if len(invalidnames) > 0:
                msg = False

        status = {
            'result': 'ok',
            'msg': msg
        }

    return HttpResponse(json.dumps(status), content_type="application/json")


def email(request, email):
    if request.method == 'GET':
        msg = User.objects.uniqueEmail(email)
        status = {'result': 'ok',
                  'msg': msg}
    return HttpResponse(json.dumps(status), content_type="application/json")


def emailscode(request, email):
    # 发送邮箱验证码
    result = {}
    returnjson = False
    if 'json' in request.GET:
        returnjson = True

    if request.method == 'GET':
        codetype = request.GET.get('codetype', '0')
        if codetype == '0':  # 注册
            pass
        else:
            # 密码找回
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                result['status'] = USER_NOT_FOUND
                result['msg'] = _('用户不存在')  # '用户不存在...'
                return HttpResponse(json.dumps(result), content_type="application/json")
        result = VerifyCode.objects.send_code(email, codetype=codetype)
    else:
        result['status'] = ERROR
        result['msg'] = _('Need Get')
    return HttpResponse(json.dumps(result), content_type="application/json")


def verify(request, email, code):
    # 验证邮箱验证码
    result = {}
    if request.method == 'GET':
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            result['status'] = ERROR
            result['msg'] = _('用户不存在')  # '用户不存在...'
            return HttpResponse(json.dumps(result), content_type="application/json")

        result = VerifyCode.objects.veirfy_code(code, email)
        result['status'] = 'ok'
        result['msg'] = _('Verified')
        result['email'] = email
    else:
        result['status'] = ERROR
        result['msg'] = _('Need Get')
    return HttpResponse(json.dumps(result), content_type="application/json")

class PhoneCodeView(View): 
    def get(self, request): 
        # 发送手机验证码
        msg = {} 
        int_time = int(time.time())
        if 'phone' in request.GET and 'codetype' in request.GET:
            # 发送验证码 
            codetype = request.GET['codetype']
            phone = request.GET['phone']
            if codetype == '1':
                try:
                    user = User.objects.get(phone=phone)
                except User.DoesNotExist:
                    msg['status'] = ERROR
                    msg['msg'] = '用户未注册'  
                    return HttpResponse(json.dumps(msg), content_type="application/json")
            else:
                try:
                    user = User.objects.get(phone=phone) 
                    # u'该手机号已注册，请重新登录或找回密码'
                    if user.is_active:
                        msg['status'] = 2 # 已注册，导航到登录页
                        msg['msg'] = "手机号已注册"
                        return HttpResponse(json.dumps(msg), content_type="application/json")
                except User.DoesNotExist:
                    pass

            if 'time' in request.session:
                old_int_time = request.session['time']
                request.session['time'] = int_time
                if int_time - old_int_time < 60:  # 60秒，频率太高
                    msg['status'] = ERROR
                    msg['msg'] = "勿频繁操作"  # u'操作频率太快...'
                else:
                    # 发送验证码
                    msg = VerifyCode.objects.send_code_phone(phone, codetype)
            else:
                old_int_time = 0
                msg = VerifyCode.objects.send_code_phone(phone, codetype)
                request.session['time'] = int_time
            print(int_time, old_int_time, int_time - old_int_time)
        else:
            msg={"status":ERROR,"msg":"参数错误"}
        return HttpResponse(json.dumps(msg), content_type="application/json")


# @login_required
@api_view(['GET', 'POST']) 
@permission_classes((IsAuthenticated,))
def alter_usertype(request, phone, usertype):
    # 修改用户类型：
    # phone电话号码
    # usertype为新用户类型，可选值为【1,0】
    msg = {}
    if usertype in [0, 1]:  # User.get_usertypes():
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            msg['status'] = ERROR
            msg['msg'] = _('用户不存在')  # '用户不存在...'
    else:
        msg['status'] = ERROR
        msg['msg'] = _('usertype error, must be in [1, 0]...')

    return HttpResponse(json.dumps(msg), content_type="application/json")


@csrf_exempt
def phoneverify(request, phone, code):
    # 验证手机号码
    result = {}
    if request.method == 'GET':
        status = VerifyCode.objects.veirfy_code_phone(code, phone)
        if status:
            result['status'] = 'ok'
            result['msg'] = _('ok')
        else:
            result['status'] = ERROR
            result['msg'] = _('Verification code error')  # 验证码错误
    return HttpResponse(json.dumps(result), content_type="application/json")


@csrf_exempt
def authorize(request):
    """
    第三方通过token获取用户信息
    需要：token, appid and secret in post
    """
    result = {}
    if request.method == 'POST':
        if 'token' in request.POST and 'appid' in request.POST and 'secret' in request.POST:
            token = request.POST['token']
            appid = request.POST['appid']
            secret = request.POST['secret']
            try:
                authtoken = AuthToken.objects.get(
                    app__uuid=appid, app__secret=secret, token=token)
                user = authtoken.user

                result['status'] = 'ok'
                user_json = {
                    'username': user.username,
                    'email': user.email,
                    'phone': user.phone
                }
                result['result'] = user_json
                # authtoken.delete()
            except AuthToken.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = _('404 Not found')
        else:
            result['status'] = ERROR
            result['msg'] = _('Parameter error')
    else:
        result['status'] = ERROR
        result['msg'] = _('Method error')

    return HttpResponse(json.dumps(result), content_type="application/json")

 