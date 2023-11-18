# -*- coding: utf-8 -*- 
from common.logutils import getLogger
import time
import traceback
import configparser
from django.shortcuts import render
from django.http import HttpResponse 
from django.conf import settings 
import pdb
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import Group
import os
from django.contrib import auth
import requests
from appuser.models import AdaptorUser as User
from appuser.models import VerifyCode
from django.utils.translation import ugettext as _
import json
import random
import string
import uuid
from django.views import View
from common.WXBizDataCrypt import WXBizDataCrypt
from dept.models import Dept
from property.code import ERROR, SUCCESS
from appuser.comm import set_login_info


logger = getLogger(True, 'users', False)



class WeixinView(View):
 
    def get(self, request):
        content = {}   
        return  HttpResponse(json.dumps(content), content_type='application/json')
    
    def post(self, request):
        content = {}  
        weixinurl = settings.WEIXINPAY['xiaochengxu']['WEIXINURL']
        appId = settings.WEIXINPAY['xiaochengxu']['app_id']
        secret = settings.WEIXINPAY['xiaochengxu']['app_seckey']
        js_code = request.POST['js_code']
        encryptedData = request.POST['encryptedData']
        bindphone = None
        if 'bindphone'  in request.POST:
            # 微信小程序端使用手机号码登录之后，需要绑定openid进行支付时，传递这个参数
            bindphone = request.POST['bindphone']
        iv = request.POST['iv']
        print(request.POST)
        grantType = request.POST['grantType']
        params  = {
            "appId":appId,
            "secret":secret,
            "js_code":js_code,
            "grantType":grantType
        }
        req = requests.get(weixinurl, params)
        if req.status_code == 200: 
            wx_content = json.loads(req.content)
            logger.debug("wxlogin:"+ req.content.decode("utf-8") )
             
                        
            if 'session_key' in wx_content: 
                openid = wx_content['openid']
                if bindphone is not None:
                    # 只绑定并返回用户的openid 
                    try:
                        user = User.objects.get(phone = bindphone)
                        if user.openid is None:
                            user.openid = openid
                            user.save()
                    except User.DoesNotExist: 
                        content['status'] = ERROR
                        content['msg'] = "用户未注册" 
                        return  HttpResponse(json.dumps(content), content_type='application/json') 
                else:
                    session_key = wx_content["session_key"]
                    try:
                        pc = WXBizDataCrypt(appId, session_key) 
                        wx_result = pc.decrypt(encryptedData, iv) 
                        phone = wx_result['purePhoneNumber']
                        # 如果用户未注册：1、自动注册，2 自动登录 
                        try:
                            user = User.objects.get(phone = phone)
                        except User.DoesNotExist: 
                            logger.debug("新用户:"+ str(phone) )
                            user = User.objects.create(phone = phone, uuid= str(uuid.uuid4()))
                        if user.openid is None:
                            user.openid = openid
                            user.save()

                        auth.logout(request)
                        request.user = user 
                        auth.login(request, user)
                        content['status'] = SUCCESS
                        content['openid'] = openid
                        content['msg'] = set_login_info(user, request, "wx")
                    except : 
                        content['status'] = ERROR
                        content['msg'] = "再试一次" 
            else:
                content['status'] = ERROR
                content['msg'] = wx_content  
        return  HttpResponse(json.dumps(content), content_type='application/json')

        