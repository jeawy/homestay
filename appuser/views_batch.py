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
  
from appuser.models import AdaptorUser as User 
import json
import random
import string
import uuid
from django.utils import timezone
from django.contrib.auth.models import Permission 
from rest_framework.views import APIView 
from appuser.verify import check_email_exist, check_name_exist,  check_name, check_email, \
     check_number, check_bool, check_sex, check_phone_exist
from common.utils import verify_phone, verify_email
from dept.views import get_dept_dict
from .form import UploadPortrainForm, GroupForm, UserForm

from django.contrib import auth 

# from socialoauth import SocialSites,SocialAPIError 
from dept.models import Dept
from basedatas.bd_comm import Common 
from appuser.models import InvalidUsername
from community.models import Community, Staff
from role.models import Role
from property.code import *
 

logger = getLogger(True, 'users', False)
 
class UserBatchView(APIView):
    """
    用户批量添加
    """ 
    def post(self, request):
        # 用户批量添加
        user = request.user
        community = None
        user_json = request.data
        if 'communityuuid' in user_json:
            communityuuid = user_json['communityuuid'].strip()
            try:
                community = Community.objects.get(uuid = communityuuid )
            except Community.DoesNotExist:
                pass
        perm =  user.has_role_perm('appuser.baseuser.admin_management')
        if community is not None: 
            # 物业IT支持或者物业有权限的员工导入物业员工数据
            if not perm and community.IT_MANAGER != user:
                return HttpResponse('Forbidden', status=403)
        elif not perm:
            # 
            return HttpResponse('Forbidden', status=403) 

        result = {}
        content = {}
        # 创建消息列表
        msg_list = []
        # 创建批量添加失败,成功数
        fail_num = 0
        success_num = 0
        # 迭代次数与数据索引
        i = 0
        # 获取请求数据并以json格式进行解析
        
         
        # 获取数据中的keys-values
        keys_data = user_json["keys"]
        values_data = user_json["values"]

        for value_data in values_data:
            i += 1
             
            phone_index = keys_data.index('phone') 
            phone = value_data[phone_index]
            if phone:
                phone = phone.strip()
                if verify_phone(phone):
                    try:
                        user = User.objects.get(phone = phone)
                    except User.DoesNotExist: 
                        user = User.objects.create(phone = phone, uuid= uuid.uuid4())
                    
                    # 添加到物业员工部门
                    if community is not None:
                        staff = Staff()
                        staff.user = user
                        staff.community = community
                        try:
                            staff.save()
                        except Exception:
                            pass

                    try:
                        name_index = keys_data.index('name')
                        name = value_data[name_index]
                        if name:
                            name = name.strip()
                            if not check_name(name): 
                                user.username = name 
                            else:
                                fail_num += 1
                                content['msg'] = '用户名长度需要在0与128之间'
                                logger.info("第{0}条数据name字段不合规定".format(i))
                                msg_list.append("第{0}条的错误信息是{1}".format(i, content['msg']))
                                del content['msg']
                                continue 
                    except Exception:
                        pass
                    
                    try:
                        email_index = keys_data.index('email')
                        email = value_data[email_index].strip()
                        if verify_email(email):
                            if not check_email_exist(email):
                                user.email = email
                            else:
                                fail_num += 1
                                content['msg'] = '邮箱重复不可使用'
                                logger.info("第{0}条数据email字段不合规定".format(i))
                                msg_list.append("第{0}条的错误信息是{1}".format(i, content['msg']))
                                del content['msg']
                                continue
                        else:
                            fail_num += 1
                            content['msg'] = "邮箱格式错误"
                            logger.info("第{0}条数据email格式错误".format(i))
                            msg_list.append("第{0}条的错误信息是{1}".format(i, content['msg']))
                            del content['msg']
                            continue
                    except Exception:
                        pass
    
                    try:
                        isactive_index = keys_data.index('isactive')
                        isactive = value_data[isactive_index].strip()
                        if isactive:
                            if check_bool(isactive, content):
                                fail_num += 1
                                logger.info("第{0}条数据isactive字段不合规定".format(i))
                                msg_list.append("第{0}条的错误信息是{1}".format(i, content['msg']))
                                del content['msg']
                                continue
                            else:
                                user.is_active = isactive
                    except Exception:
                        pass
                    try:
                        sex_index = keys_data.index('sex')
                        sex = value_data[sex_index].strip()
                        if sex:
                            if not check_sex(sex, content):
                                fail_num += 1
                                logger.info("第{0}条数据sex字段不合规定".format(i))
                                msg_list.append("第{0}条的错误信息是{1}".format(i, content['msg']))
                                del content['msg']
                                continue
                            else:
                                user.sex = sex
                    except Exception:
                        pass
                    user.save()
                    try:
                        dept_index = keys_data.index('dept')
                        dept = value_data[dept_index].strip()
                        if dept:
                            try:
                                dept = dept.format()
                                dept = Dept.objects.get(name=dept)
                                user.depts.add(dept)
                            except Dept.DoesNotExist:
                                fail_num += 1
                                content['msg'] = '未能找到该对应工种'
                                msg_list.append(
                                    "第{0}条的错误信息是{1}".format(i, content['msg']))
                                del content['msg']
                                continue
                    except Exception:
                        pass

                    
                else:
                    fail_num += 1
                    content['msg'] = "手机号码格式错误"
                    logger.info("第{0}条数据phone格式错误".format(i))
                    msg_list.append("第{0}条的错误信息是{1}".format(i, content['msg']))
                    del content['msg']
                    continue
             
                success_num += 1
                logger.info("导入成功:{0}".format(i))
            else:
                fail_num += 1
                content['msg'] = "手机号码空白数据"
                logger.info("第{0}条数据phone空白".format(i))
                msg_list.append("第{0}条的错误信息是{1}".format(i, content['msg']))

        result['status'] = SUCCESS if success_num + fail_num == i else ERROR
        result['msg'] = msg_list
        result['success_num'] = success_num
        result['fail_num'] = fail_num
        logger.info("success_num:{0},fail_num:{1}".format(
            success_num, fail_num))
        return HttpResponse(json.dumps(result), content_type="application/json")
 