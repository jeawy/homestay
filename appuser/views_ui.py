# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from django.conf import settings
from django.shortcuts import redirect 
from django.utils.translation import ugettext as _
import pdb
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import  Group
import os
from appuser.models import AdaptorUser as User
from appuser.models import VerifyCode
from rest_framework.views import APIView
from appuser.comm import set_login_info
from django.http import HttpResponseForbidden
from common.fileupload import FileUpload
import json
import random
import datetime
import string
from django.utils import timezone
from django.db.utils import IntegrityError
import uuid
from common.utils import verify_phone 
from django.contrib import auth
from appuser.models import InvalidUsername
from appfile.comm import AppFileMgr
from appfile.models import Attachment
from rest_framework_jwt.views import obtain_jwt_token
from property.code import * 
from common.utils import verify_email
#from socialoauth import SocialSites,SocialAPIError  
from appuser.i18 import *
from basedatas.bd_comm import Common
from mobile.detectmobilebrowsermiddleware import DetectMobileBrowser
 

dmb     = DetectMobileBrowser()
comm    = Common()

@csrf_exempt
def login(request):  
    context ={}  
    if len(request.POST) == 0 and request.method == "POST": 
        request.POST = request.data
    next_url = request.GET.get('next')
    context = {'next': next_url}
    if 'phone' in  request.POST and 'password' in request.POST: 
         
        phone = request.POST['phone']
        password = request.POST['password']
        user = auth.authenticate(phone = phone, password = password) 
        if user: 
                auth.logout(request)
                isMble = dmb.process_request(request)
                if not isMble:
                    # 来自PC端的登录，必须有物业、或者超级管理员的角色
                    if not user.is_superuser:
                       # 无权限登录pc端
                       context['status'] = ERROR
                       context['msg'] = "无权限登录pc端"
                       return  HttpResponse(json.dumps(context),  content_type='application/json')
                

                # User is valid.  Set request.user and persist user in the session
                # by logging the user in.
                request.user = user
                auth.login(request, user)  
                context['status'] = SUCCESS
                if isMble:
                    context['msg'] = set_login_info(user, request ) 
                else:
                    # 从PC端登录用户
                    context['msg'] = set_login_info(user, request, way="pc")
                     
                response = HttpResponse(json.dumps(context),  
                    content_type='application/json')
                dt = datetime.datetime.now() + datetime.timedelta(hours = int(1))
                request.session['sessionid'] = user.get_session_auth_hash()
                request.session.set_expiry(60 * 60 )

                response.set_cookie('sessionid', user.get_session_auth_hash(), expires = dt)
                return response 
        else:
            try: 
                user = User.objects.get(phone = phone)
                if user.is_active:
                    msg =  '密码错误' 
                else:
                    msg =  '用户已注销' 
            except User.DoesNotExist:
                msg =  "用户未注册" #'登录失败，用户{0}未注册...'
            status =  USER_NOT_REGISTERED
            context = {
                        'status':status,
                        'msg':msg,
                        'phone':phone}
        
                
            return  HttpResponse(json.dumps(context), content_type='application/json') 
    else: 
        return  HttpResponse(json.dumps(context), content_type='application/json')
        

def logout(request):
    auth.logout(request)
    return redirect('/')
   
@csrf_exempt
def register(request):
    content = {} 

    if request.method == "POST":
        
        phone = request.POST['phone'].strip()
        if not verify_phone(phone):
            # 手机格式错误
            content={
            'status':ERROR ,  
            'msg': APPUSER_PHONE_ERROR # {0}格式错误
            }
            return  HttpResponse(json.dumps(content), content_type='application/json') 
        else:
            # 验证是否被注册
            if User.objects.filter(phone = phone, is_active = True).exists():
                content={
                        'status':ERROR , 
                        'msg': "手机号已注册"
                }
                return  HttpResponse(json.dumps(content), content_type='application/json') 
        password = request.POST['password'].strip()
        code = request.POST['code'].strip()
        if VerifyCode.objects.veirfy_code_phone(code, phone):
            if User.objects.filter(phone = phone).exists():
                # 用户之前注销了，重新启用
                user = User.objects.get(phone = phone)
                user.set_password(password)
                user.is_active = True
            else:
                useruuid = uuid.uuid4()
                user = User.objects.create_user(phone, useruuid,  password) 
            if 'username' in request.POST:
                username =  request.POST['username']
                user.username = username
            user.save()
            content={
                    'status': SUCCESS,
                    'msg' :  APPUSER_REGISTER_SUCCESS  # 注册成功
            }  
        else:
            content={
                'status': ERROR,
                'phone':phone, 
                'msg':  APPUSER_CODE_ERROR 
            }
    else:
        content['status'] =  ERROR
        content['msg'] = '方法错误，请使用post'
     
    return  HttpResponse(json.dumps(content), content_type='application/json') 

      
def register_success(request):
    content = {}

    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        msg = User.objects.uniqueUsername(username) 
        if msg:
            invalidnames = InvalidUsername.objects.filter(username = username ) 
            if len(invalidnames) > 0:
                msg = False
        if msg == False:
            content={
                'status':ERROR ,
                'msg': [username] # username + _(' has been registered') # 已被注册
            }
        else:       
            phone = request.POST['phone'].strip()
            password = request.POST['password'].strip()
            phonecode = request.POST['phonecode'].strip()
            if VerifyCode.objects.veirfy_code_phone(phonecode, phone):
                user = User.objects.create_user(phone, username,  password)
        
                user = auth.authenticate(phone=phone, password=password)
                auth.login(request, user)
                token = uuid.uuid4()

                return redirect(redirect_url+"?token=" , **content)
            else:
                content={
                    'status': ERROR,
                    'username':username,
                    'phone':phone, 
                    'msg': _('验证码错误') # 验证码错误
                }
 
    return render(request, 'user/regsiter.html', content)

@csrf_exempt
def find_password(request): 
    content={} 
    if request.method == 'POST': 
        phone = request.POST['phone'].strip()
        password = request.POST['password'].strip()
        phonecode = request.POST['phonecode'].strip()
        if VerifyCode.objects.veirfy_code_phone(phonecode, phone, codetype='1'):
            user = User.objects.get(phone = phone )
            user.set_password(password) 
            user.save()
            content={
                'status':SUCCESS, 
                'msg': _('密码已修改.')  
            }
        else:
            content={
                'status': ERROR,  
                'msg':  _('验证码错误') # 验证码错误
            }
        return HttpResponse(json.dumps(content), content_type='application/json')
    else:
        content['status'] =  ERROR
        content['msg'] = '方法错误，请使用post'

    return  HttpResponse(json.dumps(content), content_type='application/json') 



class UserPortrait(APIView):
    """
    用户头像管理
    """ 
    def post(self, request):
        result = {}
         
        user = request.user  
        
        # 修改用户头像
        if len(request.FILES) : 
            for image in request.FILES:
                # 获取附件对象 
                imagefile = request.FILES[image]
                pre = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
                file_name, file_extension = os.path.splitext(imagefile.name)
                filename = pre+file_extension
                FileUpload.upload(imagefile, 
                                os.path.join('portrait', str(user.id)), 
                                filename )
                    
                filepath= os.path.join('portrait', str( user.id), filename) 

            
                if user.thumbnail_portait:
                    # 删除磁盘旧文件
                    try:
                        os.remove(os.path.join(settings.FILEPATH,user.thumbnail_portait) )
                    except IOError:
                        pass
            
            user.thumbnail_portait = filepath
            user.save()
            result['status'] = SUCCESS
            result['msg'] = user.thumbnail_portait
        else:
            result['status'] = ERROR
            result['msg'] = 'no files'
             
        return HttpResponse(json.dumps(result), content_type="application/json")