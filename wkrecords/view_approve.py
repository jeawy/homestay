#! -*- coding:utf-8 -*-
import json
import pdb
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.translation import ugettext as _
from dept.models import Dept
from django.http import QueryDict
from django.core import serializers
from appuser.models import AdaptorUser as User
from common.customjson import LazyEncoder
from notice.comm import NoticeMgr
from common.request import Code
from django import forms
from django.utils import timezone
from django.shortcuts import redirect


from rest_framework.views import APIView
from property.code import *
from common.logutils import getLogger

from wkrecords.models import WkRecords, Approve, Associate
from category.models import Category
from wktemplate.models import WkTemplate

logger = getLogger(True, 'wkrecords', False)


def get_approve_dict_one(approve):
    """
    返回审批记录的字典实例
    字典格式：
     {
                    "approve_time":approve_time,
                    "approve_opinion":approve_opinion,
                    "approve_level":approve.level,
                    "approve_status": approve.status,
                    "approve_and_or":approve.and_or,
                    "approve_touser":approve_touser,
                    }
    """

    approve_time = ''
    if approve.time:
        over_time =approve.time.strftime('%Y-%m-%d %H:%M:%S')
    approve_opinion = ''
    if approve.opinion:
        approve_opinion = approve.opinion
    approve_touser = ''
    if approve.touser:
        approve_touser = approve.touser_id

    record_dict = {
        "approve_time":approve_time,
        "approve_opinion":approve_opinion,
        "approve_level":approve.level,
        "approve_status": approve.status,
        "approve_and_or":approve.and_or,
        "approve_touser":approve_touser,
    }

    return record_dict

def get_approve_dict_all(approve):
    """
    返回审批记录的字典实例
    字典格式：
     {
                    "flow_Id":record.id
                    "creator_name":creator_name,
                    "creator_id":creator_id,
                    "category_name":category_name,
                    "category_level": category_level ,
                    "name":record.name,
                    "status":record.status,
                    "create_time":record.create_time,
                    "over_time":record.over_time,
                    "template_name":template_name,
                    "template_id":template_id,
                    }
    """

    record = approve.flow
    creator_name = approve.flow.user.username
    creator_id = approve.flow.user.id
    category_name = ''
    category_level = ''
    if approve.flow.category_id:
        category_name = record.category.name
        category_level = record.category.level
    create_time = record.date.strftime('%Y-%m-%d %H:%M:%S') #setting里面设置USE_TZ和TIME_ZONE以后才可以显示北京时间
    over_time = ''
    if record.over_time:
        over_time =record.over_time.strftime('%Y-%m-%d %H:%M:%S')
    template_name = ''
    template_id= ''
    if record.template_id:
        template_name = record.template.name
        template_id = record.template.id

    record_dict = {
        "flow_id":record.id,
        "creator_name": creator_name,
        "creator_id": creator_id,
        "category_name": category_name,
        "category_level": category_level,
        "name": record.name,
        "status": record.status,
        "create_time": create_time,
        "over_time": over_time,
        "template_name": template_name,
        "template_id": template_id,
    }

    return record_dict


class WkApproveView(APIView):
    """查看审批记录和进行审批"""

    
    def get(self, request):

        content = {}
        returnjson = False
        if 'json' in request.GET:
            returnjson = True
        user = request.user

        if 'id' in request.GET:
            id = request.GET['id']
            try:
                flow_id = int(id)
            except ValueError:
                content['status'] = WKRECORDS_RECORD_ARGUMENT_ERROR_ID_NOT_INT
                content['msg'] = 'Record id not int'
                return HttpResponse(json.dumps(content), content_type="application/json")
            #查找具体的审批记录
            try:
                approve = Approve.objects.get(flow_id=flow_id, approver_id=user.id)
                content['status'] = SUCCESS
                content['msg'] = get_approve_dict_one(approve)
            except Approve.DoesNotExist:
                content['status'] = WKRECORDS_RECORD_NOT_FOUND
                content['msg'] = '404 Not found the id'
                return HttpResponse(json.dumps(content), content_type="application/json")
        #查找当前审批人所有的审批记录
        else:
            approvers = Approve.objects.filter(approver_id=user.id)
            approve_list = []
            for approve in approvers:
                approve_list.append(get_approve_dict_all(approve))
            content['msg'] = approve_list
            content['status'] = SUCCESS

        return HttpResponse(json.dumps(content), content_type="application/json")

    
    def post(self, request):
        """
        审批流程
        """
        result = {}
        user = request.user
        # 新建流程
        if len(request.POST) == 0:
            request.POST = request.data

       #审批流程程模块
       #验证数据是否合法
        record = WkRecords()
        approver = Approve()
        #record.user_id = user.id
        # 外键，验证流程是否存在，审批人是否合法
        # 
        if 'id' in request.POST:
            id = request.POST['id'].strip()
            try:
                flow_id = int(id)
                record = WkRecords.objects.get(id=flow_id)
            except ValueError:
                result['status'] = WKRECORDS_RECORD_ARGUMENT_ERROR_ID_NOT_INT
                result['msg'] = 'The id not int'
                return HttpResponse(json.dumps(result), content_type="application/json")
            except WkRecords.DoesNotExist:
                result['status'] = WKRECORDS_NOT_FOUND
                result['msg'] = '404 Not found the id'
                return HttpResponse(json.dumps(result), content_type="application/json")
            try:
                # 
                approver = Approve.objects.get(flow_id=flow_id, approver_id=user.id)
            except Approve.DoesNotExist:
                result['status'] = WKRECORDS_APPROVER_NOT_FOUND
                result['msg'] = '404 Not found the approver'
                return HttpResponse(json.dumps(result), content_type="application/json")
            #查看当前流程审批状态和审批人员审批状态是否可以进行审批
            if (record.status != WkRecords.SUBMITTED or record.status != WkRecords.APPROVE) \
                    and approver.status != Approve.SUBMITTED and approver.level != 0:
                result['status'] = WKRECORDS_APPROVER_CAN_NOT_APPROVE
                result['msg'] = 'Approver can not to approve'
                return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = WKRECORDS_ARGUMENT_ERROR_NEED_ID
            result['msg'] = 'Need id in POST'
            return HttpResponse(json.dumps(result), content_type="application/json")

        #验证审批状态
        #
        if 'status' in request.POST:
            try:
                status = int(request.POST['status'].strip())
            except ValueError:
                result['status'] = WKRECORDS_APPROVER_STATUS_NOT_INT
                result['msg'] = 'Approver status not int'
                return HttpResponse(json.dumps(result), content_type="application/json")
            # 验证审批状态是否在合法的列表中
            approve_enum = [Approve.PASS, Approve.REFUSE, Approve.OTHER]
            if status in approve_enum:
                approver.status = status
            else:
                result['status'] = WKRECORDS_APPROVER_STATUS_NOT_LEGAL
                result['msg'] = 'Approver status not legal'
                return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = WKRECORDS_APPROVER_STATUS_NOT_FOUND
            result['msg'] = 'Approver status not found'
            return HttpResponse(json.dumps(result), content_type="application/json")

        #验证审批意见
        # 
        if 'opinion' in request.POST:
            opinion = request.POST['opinion'].strip()
            if opinion:
                approver.opinion = opinion
            else:
                result['status'] = WKRECORDS_APPROVER_OPINION_IS_EMPTY
                result['msg'] = 'Approver opinion is empty'
                return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = WKRECORDS_APPROVER_OPINION_NOT_FOUND
            result['msg'] = 'Need opinion id POST'
            return HttpResponse(json.dumps(result), content_type="application/json")
        #验证结束

        #保存审批意见
        approver.time = timezone.now()  #保存审批时间
        #当前审批状态通过
        if approver.status == Approve.PASS:
            approver_list = Approve.objects.filter(flow_id=record.id, level=approver.level).exclude(approver_id=user.id)
            #当前级别并行审批
            if approver.and_or == Approve.AND:
                flag =1
                for appr in approver_list:
                    if appr.status == 0:
                        flag = 0
                        break
                if flag == 0:
                    approver.save()
                #当前审批级别审批结束，进入下一级审批
                else:
                    level = approver.level + 1
                    next_approver = Approve.objects.filter(flow_id=record.id, level=level)
                    if next_approver:
                        next_approver.update(status=Approve.SUBMITTED)
                    else:
                        record.status = WkRecords.PASS
                        record.save()
                        approver.save()
            #当前级别串行审批
            elif approver.and_or == Approve.OR:
                #当前级别的其他审批人员不用进行审批
                if approver_list:
                    approver_list.update(status=Approve.OTHER_PASS)
                #下级审批人员设置
                level = approver.level + 1
                next_approver = Approve.objects.filter(flow_id=record.id, level=level)
                if next_approver:
                    next_approver.update(status=Approve.SUBMITTED)
                else:
                    record.status = WkRecords.PASS
                    record.save()
                approver.save()
        #当前审批状态拒绝
        elif approver.status == Approve.REFUSE:
            record.status = WkRecords.REFUSE
            record.save()
            approver.save()
        #当前审批状态为转批
        elif approver.status == Approve.OTHER:
            if 'touser' in request.POST:
                try:
                    touser = User.objects.get(id=request.POST['touser'].strip())
                except ValueError:
                    result['status'] = WKRECORDS_APPROVER_TOUSER_ERROR
                    result['msg'] = 'Touser error'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except User.DoesNotExist:
                    result['status'] = WKRECORDS_APPROVER_NOT_FOUND
                    result['msg'] = '404 Not found the touser'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                #查看转批人是否流程创建人和自己
                if touser.id == record.user_id or touser.id == approver.approver_id:
                    result['status'] = WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_CAN_NOT_SELF
                    result['msg'] = 'Touser can not flow creator or self'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                #查看当前转批人员是否已经是审批人员
                temp_appr = Approve.objects.filter(flow_id=record.id, approver_id=user.id)
                if temp_appr:
                    approver.touser_id = touser.id
                    approver.opinion  = approver.opinion + "(审批用户已经存在)"
                    approver.save()

                    approver_list = Approve.objects.filter(flow_id=record.id, level=approver.level).exclude(
                        approver_id=user.id)
                    flag = 1
                    for appr in approver_list:
                        if appr.status == 0:
                            flag = 0
                            break
                     # 当前审批级别审批结束，进入下一级审批
                    if flag == 1:
                        level = approver.level + 1
                        next_approver = Approve.objects.filter(flow_id=record.id, level=level)
                        if next_approver:
                            next_approver.update(status=Approve.SUBMITTED)
                        else:
                            record.status = WkRecords.PASS
                            record.save()
                else:
                    approver.touser_id = touser.id
                    approver.save()
                    # 保存转批人员
                    approve_touser = Approve()
                    approve_touser.flow_id = approver.flow_id
                    approve_touser.approver_id = touser.id
                    approve_touser.level = approver.level
                    approve_touser.and_or = approve_touser.and_or
                    approve_touser.save()

            else:
                result['status'] = WKRECORDS_APPROVER_TOUSER_NOT_FOUND
                result['msg'] = 'Need touser id POST'
                return HttpResponse(json.dumps(result), content_type="application/json")

        result['status'] = SUCCESS
        result['msg'] = '已完成'

        return HttpResponse(json.dumps(result), content_type="application/json")


