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
from appfile.comm import AppFileMgr
from django.conf import settings
from appfile.models import Attachment
from property.entity import EntityType

logger = getLogger(True, 'wkrecords', False)


def get_record_dict_one(record):
    """
    返回record的字典实例
    字典格式：
     {
                    "creator_name":creator_name,
                    "creator_id":creator_id,
                    "category_name":category_name,
                    "category_level": category_level ,
                    "name":record.name,
                    "context":record.context,
                    "status":record.status,
                    "create_time":record.create_time,
                    "over_time":record.over_time,
                    "extra":record.extra,
                    "template_name":template_name,
                    "template_id":template_id,
                    "associate_list":associate_list,
                    "receiver_list":receiver_list,
                    "approver_list":approver_list,
                    "attachment": attachment,
                    }
    """

    creator_name = record.user.username
    creator_id = record.user.id
    category_name = ''
    category_level = ''
    if record.category_id:
        category_name = record.category.name
        category_level = record.category.level
    create_time = record.date.strftime('%Y-%m-%d %H:%M:%S') #setting里面设置USE_TZ和TIME_ZONE以后才可以显示北京时间
    over_time = ''
    if record.over_time:
        over_time =record.over_time.strftime('%Y-%m-%d %H:%M:%S')
    extra = ''
    if record.extra:
        extra = record.extra
    template_name = ''
    template_id= ''
    if record.template_id:
        template_name = record.template.name
        template_id = record.template.id
    #获取关联表
    associate_list = []
    try:
        associate = record.associate_id.all()
        for value in associate:
            associate_dict = {}
            associate_dict['id'] = value.be_associate_id
            associate_dict['name'] = value.be_associate.name
            associate_list.append(associate_dict)
    except Associate.DoesNotExist:
        associate_list = []
    #获取收文人员和审批人员信息
    receiver_list = []
    approver_list = []
    try:
        approver = record.flow_id.all()
        for value in approver:
            receiver_dict = {}
            approver_dict = {}
            #通过level判断是收文人员还是审批人员
            if value.level == 0:
                receiver_dict['id'] = value.approver_id
                receiver_dict['name'] = value.approver.username
                receiver_list.append(receiver_dict)
            else:
                approver_dict['id'] = value.approver_id
                approver_dict['name'] = value.approver.username
                approver_dict['level'] = value.level
                approver_dict['status'] = value.status
                if value.touser_id:
                    approver_dict['touser_id'] = value.touser_id
                    approver_dict['touser_name'] = value.touser.username
                else:
                    approver_dict['touser'] = ''
                if value.time:
                    approver_dict['time'] = value.time.strftime('%Y-%m-%d %H:%M:%S')
                    approver_dict['opinion'] = value.opinion
                else:
                    approver_dict['time'] = ''
                    approver_dict['opinion'] = ''
                approver_list.append(approver_dict)
    except Approve.DoesNotExist:
        receiver_list = {}
        approver_list = {}
    #添加附件
    attach_temp = AppFileMgr.filelist(Attachment.FLOWATTACH, record.id)
    attachment_list = []
    for attach_value in attach_temp:
        attachment_dict = {attach_value.filename: attach_value.filepath}
        attachment_list.append(attachment_dict)

    record_dict = {
        "creator_name": creator_name,
        "creator_id": creator_id,
        "category_name": category_name,
        "category_level": category_level,
        "name": record.name,
        "context": record.context,
        "status": record.status,
        "create_time": create_time,
        "over_time": over_time,
        "extra": extra,
        "template_name": template_name,
        "template_id": template_id,
        "associate_list": associate_list,
        "receiver_dict": receiver_list,
        "approver_dict ": approver_list,
        "attachment": attachment_list,
    }

    return record_dict

def get_record_dict_all(record):
    """
    返回record部分信息的字典实例
    字典格式：
     {
                    "record_id":record_id
                    "creator_name":creator_name,
                    "creator_id":creator_id,
                    "category_name":category_name,
                    "category_level": category_level ,
                    "name":record.name,
                    "status":record.status,
                    "create_time":record.create_time,
                    "over_time":record.over_time,
                    }
    """

    creator_name = record.user.username
    creator_id = record.user.id
    category_name = ''
    category_level = ''
    if record.category_id:
        category_name = record.category.name
        category_level = record.category.level
    create_time = record.date.strftime('%Y-%m-%d %H:%M:%S') #setting里面设置USE_TZ和TIME_ZONE以后才可以显示北京时间
    over_time = ''
    if record.over_time:
        over_time =record.over_time.strftime('%Y-%m-%d %H:%M:%S')

    record_dict = {
        "record_id": record.id,
        "creator_name": creator_name,
        "creator_id": creator_id,
        "category_name": category_name,
        "category_level": category_level,
        "name": record.name,
        "context": record.context,
        "status": record.status,
        "create_time": create_time,
        "over_time": over_time,
    }

    return record_dict


class propertyView(APIView):
    """创建、修改、删除和查看流程"""

    
    def get(self, request):
        content = {}
        returnjson = False
        if 'json' in request.GET:
            returnjson = True
        user = request.user
        #获取单个流程的详细信息
        if 'id' in request.GET:
            record_id = request.GET['id']
            try:
                record_id = int(record_id)
            except ValueError:
                content['status'] = WKRECORDS_RECORD_ARGUMENT_ERROR_ID_NOT_INT
                content['msg'] = 'Record id not int'
                return HttpResponse(json.dumps(content), content_type="application/json")
            try:
                record = WkRecords.objects.get(id=record_id)
                content['status'] = SUCCESS
                content['msg'] = get_record_dict_one(record)
            except WkRecords.DoesNotExist:
                content['status'] = WKRECORDS_RECORD_NOT_FOUND
                content['msg'] = '404 Not found the id'
        #获取全部流程
        else:
            records = WkRecords.objects.all()
            records_list = []
            for record in records:
                records_list.append(get_record_dict_all(record))
            content['msg'] = records_list
            content['status'] = SUCCESS

        return HttpResponse(json.dumps(content), content_type="application/json")

    
    def post(self, request):
        """
        新建流程
        """
        result = {}
        user = request.user
        # 新建流程
        if len(request.POST) == 0:
            request.POST = request.data
        if 'method' in request.POST:
            method = request.POST['method'].lower()
            if method == 'put':  # 修改流程
                return self.put(request)
            elif method == 'delete':  # 删除流程
                return self.delete(request)
            elif method == 'recall': #撤回流程
                return self.recall(request)

       #新建流程模块
       #验证数据是否合法
        record = WkRecords()
        record.user_id = user.id
        # 外键，验证流程类别是否存在，存在的时候是否在类别表中
        if 'category_id' in request.POST:
            #验证category_id是不是整形
            category_id = request.POST['category_id'].strip()
            if category_id:
                try:
                    category_id = int(category_id)
                except ValueError:
                    result['status'] = WKRECORDS_RECORD_ARGUMENT_ERROR_CATEGORY_ID_NOT_INT
                    result['msg'] = 'Catetory_id not int'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                try:
                    category = Category.objects.get(id=category_id)
                    #验证类别的实体是否是流程实体
                    if category.entity == EntityType.RECORD:
                       record.category_id = category_id
                    else:
                        result['status'] = WKRECORDS_RECORD_ARGUMENT_ERROT_CATEGORY_ID_NOT_LEGAL
                        result['msg'] = 'Catetory entity not record'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                except Category.DoesNotExist:
                    result['status'] = WKRECORDS_RECORD_ARGUMENT_ERROT_CATEGORY_ID_NOT_EXIST
                    result['msg'] = 'Catetory_id not exist'
                    return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = WKRECORDS_RECORD_ARGUMENT_ERROT_NEED_CATETORY_IN_POST
            result['msg'] = 'Need category in POST'
            return HttpResponse(json.dumps(result), content_type="application/json")

        #name字段是必须的
        if 'name' in request.POST:
            name = request.POST['name'].strip()
            if not check_name(name, record, result):
                return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = WKRECORDS_RECORD_ARGUMENT_ERROR_NEED_NAME
            result['msg'] = 'Need name in POST'
            return HttpResponse(json.dumps(result), content_type="application/json")

        #验证审批状态，只有为草稿的时候才允许内容为空
        if not check_status(request.POST, record, result):
            return HttpResponse(json.dumps(result), content_type="application/json")

        #template字段不是必须的
        if 'template' in request.POST:
            #验证模板id是否合法
            template = request.POST['template']
            if template:
                try:
                    template_id = int(request.POST['template'].strip())
                except ValueError:
                    result['status'] = WKRECORDS_RECORD_ARGUMENT_ERROR_TEMPLATE_IS_NOT_INT
                    result['msg'] = 'Template is not int'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                if WkTemplate.objects.filter(id=template_id):
                    record.template_id = template_id
                else:
                    result['status'] = WKRECORDS_RECORD_ARGUMENT_ERROR_TEMPLATE_NOT_EXIST
                    result['msg'] = 'Template is not exist'
                    return HttpResponse(json.dumps(result), content_type="application/json")

        #扩展属性不是必须的
        if 'extra' in request.POST:
            extra = request.POST['extra'].strip()
            if not check_extra(extra, record, result):
                return HttpResponse(json.dumps(result), content_type="application/json")

        # 关联表不是必填的
        associate = []
        if 'associate_list' in request.POST:
            associate_list = request.POST['associate_list'].strip()
            if associate_list:
                if not check_associate_list(associate_list, associate, result):
                    return HttpResponse(json.dumps(result), content_type="application/json")

        #验证审批人员
        approver = []
        if not check_approver(request.POST, user.id, approver, record, result):
            return HttpResponse(json.dumps(result), content_type="application/json")

        #判断收文人员是否符合规定
        receiver = []
        if not check_receiver(request.POST, approver, user.id, receiver, result):
            return HttpResponse(json.dumps(result), content_type="application/json")
        # 验证数据结束

        #保存提交记录
        try:
            # 
            record.save()
            # 遍历审批人员列表，添加审批人员
            if approver:
                approver_add(approver, record.id, record.status)
            # 遍历收文人员，添加收文人员
            if receiver:
                receiver_add(receiver, record.id, record.status)
            #添加关联列表
            if associate:
                associate_add(associate, record.id)
            # 如果附件存在，保存附件
            #filepath = r'E:\ZjwProject\myproject\attachment'
            filepath = settings.WKRECORDS
            if request.FILES:
                for filename in request.FILES:
                    file_obj = request.FILES[filename]
                    result = AppFileMgr.upload(file_obj, filepath, filename, Attachment.FLOWATTACH, record.id)
        except:
            #删除附件
            appid = record.id
            apptype = Attachment.FLOWATTACH
            AppFileMgr.removefile(None, appid, apptype)
            record.delete()  # 保存出错，删除记录
            result['status'] = WKRECORDS_RECEORD_SAVE_ERROR
            result['msg'] = 'Receord save fail.'
            logger.error(record, approver, receiver, associate)# traceback
            return HttpResponse(json.dumps(result), content_type="application/json")

        result['id'] = record.id
        result['status'] = SUCCESS
        result['msg'] = '已完成'

        return HttpResponse(json.dumps(result), content_type="application/json")

    def put(self, request):
        """
        修改
        """
        result = {}
        user = request.user
        data = request.POST
        record = WkRecords()
        associate = []
        approver = []
        receiver = []
        if 'id' in data:
            try:
                flow_id = int(data['id'])
            except ValueError:
                result['status'] = WKRECORDS_RECORD_ARGUMENT_ERROR_ID_NOT_INT
                result['msg'] = 'The record id not int'
                return HttpResponse(json.dumps(result), content_type="application/json")
            try:
                record = WkRecords.objects.get(id=flow_id)
            except WkRecords.DoesNotExist:
                result['status'] = WKRECORDS_NOT_FOUND
                result['msg'] = '404 Not found the id'
                return HttpResponse(json.dumps(result), content_type="application/json")
            #只有当前用户id和创建流程的用户id相等才可以进行修改
            # 
            if record.user_id == user.id:
                #只有当流程处于撤销、草稿才可以进行修改
                if record.status == WkRecords.DRAFT or record.status == WkRecords.RECALL:
                    if 'name' in data:
                        name = data['name'].strip()
                        if not check_name(name, record, result):
                            return HttpResponse(json.dumps(result), content_type="application/json")
                    #检查内容和状态是否合法
                    if not check_status(data, record, result):
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    if 'extra' in data:
                        extra = data['extra']
                        if not check_extra(extra, record, result):
                            return HttpResponse(json.dumps(result), content_type="application/json")
                    #如果关联列表存在，检查关联列表
                    if 'associate_list' in data:
                        associate_list = data['associate_list']
                        if not check_associate_list(associate_list, associate, result):
                            return HttpResponse(json.dumps(result), content_type="application/json")
                    #检查审批人员
                    if not check_approver(data, user.id, approver, record, result):
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    #检查收文人员
                    if not check_receiver(data, approver, user.id, receiver, result):
                        return HttpResponse(json.dumps(result), content_type="application/json")

                    try:
                        record.save()
                        # 遍历审批人员列表，添加审批人员
                        if approver:
                            Approve.objects.filter(flow_id=record.id, level__gt=0).delete()
                            approver_add(approver, record.id, record.status)
                        # 遍历收文人员，添加收文人员
                        if receiver:
                            Approve.objects.filter(flow_id=record.id, level=0).delete()
                            receiver_add(receiver, record.id, record.status)
                        # 添加关联列表
                        if associate:
                            Associate.objects.filter(associate_id=record.id).delete()
                            associate_add(associate, record.id)
                        #添加附件
                        #filepath = r'E:\ZjwProject\myproject\attachment'
                        filepath = settings.WKRECORDS
                        if request.FILES:
                            appid = record.id
                            apptype = Attachment.FLOWATTACH
                            AppFileMgr.removefile(None, appid, apptype)
                            for filename in request.FILES:
                                file_obj = request.FILES[filename]
                                result = AppFileMgr.upload(file_obj, filepath, filename, Attachment.FLOWATTACH,
                                                           record.id)

                        result['status'] = SUCCESS
                        result['msg'] = '已完成'
                    except ValueError:
                        #record.delete()  # 保存出错，删除记录
                        logger.error(record, approver, receiver, associate)
                        result['status'] = WKRECORDS_RECEORD_SAVE_ERROR
                        result['msg'] = 'Receord save fail.'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                else:
                    result['status'] = WKRECORDS_CAN_NOT_CHANGE
                    result['msg'] = 'Can not change'
            else:
                result['status'] = WKRECORDS_NOT_RIGHTS_CHANGE
                result['msg'] = 'Can not change anthor flow'
        else:
            result['status'] = WKRECORDS_ARGUMENT_ERROR_NEED_ID
            result['msg'] = 'Need id  in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self, request):
        """
        删除流程
        """
        result = {}
        user = request.user
        data = request.POST
        if 'id' in data:
            try:
                record_id = int(data['id'])
            except ValueError:
                result['status'] = WKRECORDS_RECORD_ARGUMENT_ERROR_ID_NOT_INT
                result['msg'] = 'The id is not int'
                return HttpResponse(json.dumps(result), content_type="application/json")
            if record_id:
                try:
                    #删除流程
                    record = WkRecords.objects.get(id=record_id)
                    flow_id = record.id
                    logger.warning("user:{0} has deleted dept(id:{1}, name:{2}". \
                                   format(user.username, record.id, record.name))
                    record.delete()
                    #删除附件
                    appid = flow_id
                    apptype = Attachment.FLOWATTACH
                    AppFileMgr.removefile(None, appid, apptype)

                    result['status'] = SUCCESS
                    result['msg'] = '已完成'
                except WkRecords.DoesNotExist:
                    result['status'] = WKRECORDS_RECORD_NOT_FOUND
                    result['msg'] = '404 Not found the id'
            else:
                result['status'] = WKRECORDS_ID_IS_EMPTY
                result['msg'] = 'The id is empty'
        else:
            result['status'] = WKRECORDS_RECORD_ARGUMENT_ERROR_NEED_ID
            result['msg'] = 'Need id in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")

    def recall(self, request):
        """用户撤回,流程审批转态变为-2，审批人员审批状态变为-2"""
        result = {}
        user = request.user
        if 'id' in request.POST:
            # 判断id相关的流程是否存在
            flow_id = request.POST['id'].strip()
            if flow_id:
                try:
                    record = WkRecords.objects.get(id=flow_id)
                except WkRecords.DoesNotExist:
                    result['status'] = WKRECORDS_NOT_FOUND
                    result['msg'] = '404 Not found the id'
                    # return False
                    return HttpResponse(json.dumps(result), content_type="application/json")
                    # 验证是不是自己的流程
                if record.user_id == user.id:
                    # 只有没有审批之前才可以撤回
                    if record.status == WkRecords.SUBMITTED:
                        try:
                            approvers_set = Approve.objects.filter(flow_id=record.id)
                            for approver in approvers_set:
                                approver.status = Approve.DRAFT
                                approver.save()
                            record.status = WkRecords.RECALL
                            record.save()

                            result['status'] = SUCCESS
                            result['msg'] = '已完成'
                        except Approve.DoesNotExist:
                            result['status'] = WKRECORDS_RECALL_FAIL
                            result['msg'] = 'Recall fail'
                            return HttpResponse(json.dumps(result), content_type="application/json")
                    else:
                        result['status'] = WKRECORDS_CAN_NOT_RECALL
                        result['msg'] = 'Can not recall flow'
                else:
                    result['status'] = WKRECORDS_NOT_RIGHTS_CHANGE
                    result['msg'] = 'Can not recall anthor flow'
            else:
                result['status'] = WKRECORDS_ID_IS_EMPTY
                result['msg'] = 'The id is empty'
        else:
            result['status'] = WKRECORDS_RECORD_ARGUMENT_ERROR_NEED_ID
            result['msg'] = 'Need id in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")


#检查name是否合法
def check_name(name, record, result):
    if len(name) > 200:
        result['status'] = WKRECORDS_RECORD_ARGUMENT_ERROR_NAME_TOO_LONG
        result['msg'] = 'name too long'
        return False
    elif len(name) == 0:
        result['status'] = WKRECORDS_RECORD_ARGUMENT_ERROR_NAME_IS_EMPTY
        result['msg'] = 'name is empty.'
        return False
    else:
        record.name = name
        return True


#检测状态和内容是否合法
def check_status(data, record, result):

    if 'status' in data:
        # 验证状态是否整形
        try:
            status = int(data['status'].strip())
        except ValueError:
            result['status'] = WKRECORDS_RECORD_ARGUMENT_ERROR_STATUS_NOT_INT
            result['msg'] = 'status is not int'
            return False
        #草稿状态，内容可以为空
        if status == WkRecords.DRAFT:
            record.status = status
            if 'context' in data:
                record.context = data['context'].strip()
            return True
        #提交状态，验证详细内容是否存在或者为空
        elif status == WkRecords.SUBMITTED:
            record.status = status
            if 'context' in data:
                context = data['context'].strip()
                if len(context) == 0:
                    result['status'] = WKRECORDS_RECORD_ARGUMENT_ERROR_CONTEXT_IS_EMPTY
                    result['msg'] = 'context is empty.'
                    return False
                else:
                    # context字段合法，添加进对象
                    record.context = context
                    return True
            else:
                result['status'] = WKRECORDS_RECORD_ARGUMENT_ERROR_NEED_CONTEXT
                result['msg'] = 'Need context in POST'
                return False
        else:
            result['status'] = WKRECORDS_RECORD_ARGUMENT_ERROR_STATUS_ERROR
            result['msg'] = 'status is error'
            return False
    else:
        result['status'] = WKRECORDS_RECORD_ARGUMENT_ERROR_NEED_STATUS
        result['msg'] = 'Need status in POST'
        return False


#检查扩展属性
def check_extra(extra, record, result):
    if extra:
        try:
            extra_list = eval(extra)
        except ValueError:
            result['status'] = WKRECORDS_EXTRA_ARGUMENT_ERROR
            result['msg'] = 'Extra value error.'
            return False
        except NameError:
            result['status'] = WKRECORDS_EXTRA_ARGUMENT_ERROR_EXTRA_LIST_NAME_ERROR
            result['msg'] = 'Extra context name error.'
            return False
        except TypeError:
            result['status'] = WKRECORDS_EXTRA_ARGUMENT_ERROR_EXTRA_LIST_TYPE_ERROR
            result['msg'] = 'Extra list type error.'
            return False
        except SyntaxError:
            result['status'] = WKRECORDS_EXTRA_ARGUMENT_ERROR_EXTRA_LIST_SYNTAX_ERROR
            result['msg'] = 'Extra list syntax error.'
            return False
        for value in extra_list:
            if type(value) != dict:
                result['status'] = WKRECORDS_APPROVER_ARGUMENT_ERROR_EXTRA_VALUE_NOT_DICT
                result['msg'] = 'Extra value is not dict.'
                return False
    record.extra = extra
    return True


#检查关联列表
def check_associate_list(associate_list, associate, result):

    try:
        associate_temp = eval(associate_list)
    except ValueError:
        result['status'] = WKRECORDS_ASSOCIATE_ARGUMENT_ERROR_ASSOCIATE_ERROR
        result['msg'] = 'Accociate value error'
        return False
    except NameError:
        result['status'] = WKRECORDS_ASSOCIATE_ARGUMENT_ERROR_ASSOCIATE_LIST_NAME_ERROR
        result['msg'] = 'Associate list name error.'
        return False
    except TypeError:
        result['status'] = WKRECORDS_ASSOCIATE_ARGUMENT_ERROR_ASSOCIATE_LIST_TYPE_ERROR
        result['msg'] = 'Associate list type error.'
        return False
    except SyntaxError:
        result['status'] = WKRECORDS_ASSOCIATE_ARGUMENT_ERROR_ASSOCIATE_LIST_SYNTAX_ERROR
        result['msg'] = 'Associate list syntax error.'
        return False
    if isinstance(associate_temp, list):
        # 验证关联的流程是否WkRecords
        for value in associate_temp:
            try:
                flow_id = int(value)
            except ValueError:
                result['status'] = WKRECORDS_ASSOCIATE_ARGUMENT_ERROR_VALUE_NOT_INT
                result['msg'] = 'Accociate value not int'
                return False
            if not WkRecords.objects.filter(id=flow_id):
                result['status'] = WKRECORDS_ASSOCIATE_ARGUMENT_ERROR_ASSOCIATE_NOT_EXIST
                result['msg'] = 'Accociate is not exist'
                return False
            else:
                associate.append(flow_id)
    else:
        result['status'] = WKRECORDS_ASSOCIATE_ARGUMENT_ERROR_ASSOCIATE_ERROR
        result['msg'] = 'Accociate is not list'
        return False
    if len(associate) != len(set(associate)):
        result['status'] = WKRECORDS_ASSOCIATE_ARGUMENT_ERROR_ASSOCIATE_REPEAT
        result['msg'] = 'Accociate is can not repeat'
        return False
    return True


#检查审批人员
def check_approver(data, user_id, approver, record, result):

    temp_list = [] #用来测试审批人员是否重复
    if 'approver_list' in data:
        approver_list = data['approver_list']
        if approver_list == 0:
            result['status'] = WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_IS_EMPTY
            result['msg'] = 'Approver is empty.'
            return False
        else:
            # 转化为列表
            try:
                approver_temp = eval(approver_list)
            except ValueError:
                result['status'] = WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_LIST_VALUE_ERROR
                result['msg'] = 'Approver is value error.'
                return False
            except TypeError:
                result['status'] = WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_LIST_TYPE_ERROR
                result['msg'] = 'Approver list type error.'
                return False
            except SyntaxError:
                result['status'] = WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_LIST_SYNTAX_ERROR
                result['msg'] = 'Approver list syntax error.'
                return False
            except NameError:
                result['status'] = WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_LIST_VALUE_ERROR
                result['msg'] = 'Approver list value error.'
                return False
        # 遍历list，
        #0：并行，1：串行
        flag = [0, 1]
        for appr_dict in approver_temp:
            if type(appr_dict) != dict:
                result['status'] = WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_NOT_DICT
                result['msg'] = 'The approver must be dict'
                return False
            # 遍历字典，验证数据格式是否正确，查看每一级审批人员是否符合规定
            for key, value_list in appr_dict.items():
                if type(appr_dict[key]) != list:
                    result['status'] = WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_VALUE_NOT_LIST
                    result['msg'] = 'The value of approver must be list'
                    return False
                try:
                    # key代表的是当前同级审批是串行和并行
                    and_or = int(key)
                except ValueError:
                    result['status'] = WKRECORDS_APPROVER_ARGUMENT_ERROR_LEVEL_IS_NOT_INT
                    result['msg'] = 'Approve level must be int.'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                # 验证审批级别是否是串行或并行
                if and_or not in flag:
                    result['status'] = WKRECORDS_APPROVER_ARGUMENT_ERROR_ORDER_IS_NOT_LEGAL
                    result['msg'] = 'Approve order must be legal.'
                    return False

                # 验证审批人员是否存在，以及是否自己是审批人
                for appr_value in value_list:
                    try:
                        approver_id = int(appr_value)
                    except:
                        result['status'] = WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_NOT_INT
                        result['msg'] = 'Approver is not int'
                        return False
                    if not User.objects.filter(id=approver_id):
                        result['status'] = WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_NOT_EXIST
                        result['msg'] = 'Approver is not exist'
                        return False
                    if user_id == approver_id:
                        result['status'] = WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_CAN_NOT_SELF
                        result['msg'] = 'Approver is can not self'
                        return False
                    temp_list.append(approver_id)
            approver.append(appr_dict)
        if len(temp_list) != len(set(temp_list)):
            result['status'] = WKRECORDS_APPROVER_ARGUMENT_ERROR_APPROVER_REPEAT
            result['msg'] = 'Approver is can not repeat'
            return False
        return True
    #当根据模板来创建工作流或者提交状态的时候必须要有审批人员
    elif record.template_id or record.status == WkRecords.SUBMITTED:
        result['status'] = WKRECORDS_APPROVER_ARGUMENT_ERROR_NEED_APPROVER
        result['msg'] = 'Need approver is POST.'
        return False
    return True


#检查收文人员
def check_receiver(data, approver, user_id, receiver, result):

    if 'receiver_list' in data:
        receiver_list = data['receiver_list']
        try:
            receiver_temp = eval(receiver_list)
        except ValueError:
            result['status'] = WKRECORDS_RECEIVER_ARGUMENT_ERROR_RECEIVER_LIST_VALUE_ERROR
            result['msg'] = 'Receiver is list value error'
            return False
        except TypeError:
            result['status'] = WKRECORDS_RECEIVER_ARGUMENT_ERROR_RECEIVER_LIST_TYPE_ERROR
            result['msg'] = 'Receiver list type errorr.'
            return False
        except SyntaxError:
            result['status'] = WKRECORDS_RECEIVER_ARGUMENT_ERROR_RECEIVER_LIST_SYNTAX_ERROR
            result['msg'] = 'Approver list syntax errorr.'
            return False
        except NameError:
            result['status'] = WKRECORDS_RECEIVER_ARGUMENT_ERROR_RECEIVER_LIST_VALUE_ERROR
            result['msg'] = 'Approver list value error.'
            return False
        #验证收文列表是否是list
        if not isinstance(receiver_temp, list):
            result['status'] = WKRECORDS_RECEIVER_ARGUMENT_ERROR_RECEIVER_NOT_LIST
            result['msg'] = 'Receiver is not list'
            return False
        # 验证用户表里面是否有收文人员
        for re_value in receiver_temp:
            try:
                receiver_id = int(re_value)
            except ValueError:
                result['status'] = WKRECORDS_RECEIVER_ARGUMENT_ERROR_RECEIVER_NOT_INT
                result['msg'] = 'Receiver value not int'
                return False
            if not User.objects.filter(id=receiver_id):
                result['status'] = WKRECORDS_RECEIVER_ARGUMENT_ERROR_RECEIVER_NOT_EXIST
                result['msg'] = 'Receiver is not exist'
                return False
            # 验证收文人员和审批人员是否相同
            for appr_dict in approver:
                for key, value_list in appr_dict.items():
                    for appr_value in value_list:
                        if receiver_id == int(appr_value):
                            result['status'] = WKRECORDS_RECEIVER_ARGUMENT_ERROR_RECEIVER_AND_APPROVER_IS_SAME
                            result['msg'] = 'Receiver is same to approver'
                            return False
                        if receiver_id == user_id:
                            result['status'] = WKRECORDS_RECEIVER_ARGUMENT_ERROR_RECEIVER_CAN_NOT_SELF
                            result['msg'] = 'Receiver can not self'
                            return False
            receiver.append(receiver_id)
            #验证收文人员是否重复
            if len(receiver) != len(set(receiver)):
                result['status'] = WKRECORDS_RECEIVER_ARGUMENT_ERROR_RECEIVER_REPEAT
                result['msg'] = 'Receiver can not repeat'
                return False
    return True


#添加审批人员
def approver_add(approver, record_id, record_status):
    level =0 #审批级别
    for appr_dict in approver:
        level += 1
        for key, value_list in appr_dict.items():
            for appr_value in value_list:
                approver_record = Approve()
                approver_record.flow_id = record_id
                approver_record.approver_id = appr_value
                approver_record.level = level
                approver_record.and_or = key
                # 如果保存为草稿，审批状态为-2，当前不可审阅
                if record_status == WkRecords.DRAFT:
                    approver_record.status = Approve.DRAFT
                # 第一级审批人员审批状态为0，待批，其他人员为-1，还未到当前审批
                elif level != 1:
                    approver_record.status = Approve.WAIT
                approver_record.save()


#添加收文人员
def receiver_add(receiver, record_id, record_status):
    for value in receiver:
        receiver_record = Approve()
        receiver_record.flow_id = record_id
        receiver_record.approver_id = value
        if record_status == WkRecords.DRAFT:
           receiver_record.status = -2
        receiver_record.save()


#添加关联表
def associate_add(associate, record_id):
    for value in associate:
        associate_tb = Associate()
        associate_tb.associate_id = record_id
        associate_tb.be_associate_id = value
        associate_tb.save()

