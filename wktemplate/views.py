#! -*- coding:utf-8 -*-
import json
import pdb
from datetime import datetime
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.translation import ugettext as _
from wktemplate.models import WkTemplate,WkTemplate_V2,Rule_V2,Rule,\
    ROLE_ID,APPROVE_ONE,DRAFT,NORMAL,AND,OR,RECEIVE_LEVEL,RULE_ARGUMENT_NULL,RECEIVE_RULE,\
    RULE_ROLE_ID_NOT_FIND,USER_ID

from appuser.models import AdaptorUser as User


from rest_framework.views import APIView
from property.code import *
from common.logutils import getLogger
from dept.models import Dept
from category.models import Category
from django.conf import settings
from wktemplate.models import Rule
from role.comm import RoleMgr
from role.models import Role

logger = getLogger(True, 'wktemplate', False)
#定义一个template_id 全局变量

def get_rule_dict(rule,approver):
    '''返回模板以及用户的规则'''
    if rule.approve_type == 2:
        rule.approve_type = 1
    rule_dict ={
        #审批级别
        'level':rule.level,
        #审批人
        'approver':approver,
        #审批类型(and or one to one)
        'approve_type':rule.approve_type
    }
    return rule_dict
def get_role(rule):
    rule_type = rule.rule_type
    entity_id = rule.entity_id
    if(rule_type == USER_ID):
        #找到角色id和角色名字
        user = User.objects.get(id = entity_id)
        role = Role.objects.get(users = user)
    else:
        role = Role.objects.get(id = entity_id)
    get_role_dict = {
        "role_id": role.id,
        "role_name":role.name
    }
    return get_role_dict

def get_wktemplate_dict(template,rule):
    """
    返回流程模板的字典实例
    字典格式：
     {
                    "id":id
                    "name":name,
                    "type":type,
                    "extra":extra,
                    "status":status,
                    "creater":creater,
                    "modifier":modifier，
                    }
    """
    create_time = template.date.strftime(settings.DATETIMEFORMAT)
    if template.creator is not None:
        creator = template.creator.username
    else:
        creator = None

    if template.dept is not None:
        dept_id = template.dept.id
    else:
        dept_id = None
    modifier = template.modifier.username
    wktemplate_dict = {
        "id": template.id,
        "name": template.name,
        #"type": template.type.name,
        "status": template.status,
        "dept":dept_id,
        "create_time": create_time,
        "creator": creator,
        "modifier": modifier,
        #"rule_type":rule.rule_type,
        "entity_id":get_role(rule),
        #"approve_type":rule.approve_type,
        "level":rule.level
    }
    return wktemplate_dict

def check_name_exist(name):
    """检查模板名称是否已经存在，如果存在返回True，否则返回False"""
    return WkTemplate.objects.filter(name=name).exists()

def check_rule_type(role_id):
    """根据role_id保存entity_id内容，如果role_id存在返回SUCESS,如果不存在返回RULE_ROLE_ID_NOT_FIND"""
    ret = RoleMgr.getusers(role_id)
    status = ret['status']
    result={}
    if(status == SUCCESS):
        msg = ret['msg']
        role = msg['role']
        users = msg['users']
        #一对一的关系,rule_type存0
        if len(users) == 1:
            rule_type = 0
            entity_id = users[0]
        #一个角色对应多个人的关系,rule_type存1
        else:
            rule_type = 1
            entity_id = role_id
        result['rule_type'] = rule_type
        result['entity_id'] = entity_id
        return  result
    #没有找到role_id
    else:
        return RULE_ROLE_ID_NOT_FIND

class WkTemplateView(APIView):
    """
    模板管理
    """
    
    def get(self, request):
        """
        获取模板信息
        返回值为model_records_dict
        """
        if 'method' in request.GET:
            method = request.GET['method'].lower()
            if method == 'get_rule':  # 修改
                return self.get_rule(request)
        content = {}
        returnjson = False

        if 'json' in request.GET:
            returnjson = True
        user = request.user

        if 'dept' in request.GET:
            try:
                # 模板id
                template_dept = request.GET['dept']
                template_dept = int(template_dept)
            except ValueError:
                content['status'] = ARGUMENT_ERROR_ID_NOT_INT
                content['msg'] = 'dept not int'
                return HttpResponse(json.dumps(content), content_type="application/json")
            try:
                # 返回模板对象
                template = WkTemplate.objects.get(dept=template_dept)
                try:
                    #规则
                   rules = Rule.objects.filter(template=template)
                   rules_list = []
                   for rule in rules:
                       rules_list.append(get_wktemplate_dict(template,rule))
                       content['status'] = SUCCESS
                       content['msg'] = rules_list
                   return HttpResponse(json.dumps(content), content_type="application/json")
                except Rule.DoesNotExist:
                    content['status'] = RULE_NOTFOUND
                    content['msg'] = '404 This id not mapping a rule'
                    return HttpResponse(json.dumps(content), content_type="application/json")
            except WkTemplate.DoesNotExist:
                content['status'] = DEPT_NOTFOUND
                content['msg'] = []
                return HttpResponse(json.dumps(content), content_type="application/json")
        #没有id返回所有对象,返回所有模板
        #如果没有输入id,将返回所有模板信息
        else:
            templates = WkTemplate.objects.all()
            templates_list = []
            rules = []
            for template in templates:
                rules = Rule.objects.filter(template = template)
                for rule in rules:
                    templates_list.append(get_wktemplate_dict(template,rule))
            content['msg'] = templates_list
            content['status'] = SUCCESS
            return HttpResponse(json.dumps(content), content_type="application/json")


    
    def post(self, request):
        """
        新建
        """
        result = {}
        user = request.user
        # 新建
        if len(request.POST) == 0:
            request.POST = request.data
        if 'method' in request.POST:
            method = request.POST['method'].lower()
            if method == 'put':  # 修改
                return self.put(request)
            elif method == 'delete':  # 删除
                return self.delete(request)

        # 新建模板
        # name、type、approve_rule、creator字段是必须的
        #name语法判断

        if 'name' in request.POST:
            name = request.POST['name'].strip()
            if len(name) > 200:
                result['status'] = WKTEMPLATE_ARGUMENT_ERROR_NAME_TOO_LONG
                result['msg'] = 'name too long.'
                return HttpResponse(json.dumps(result), content_type="application/json")
            elif len(name) == 0:
                result['status'] = WKTEMPLATE_ARGUMENT_ERROR_NAME_EMPTY
                result['msg'] = 'name is empty.'
                return HttpResponse(json.dumps(result), content_type="application/json")
            elif check_name_exist(name):
                # 模板名称已经存在
                result['status'] = WKTEMPLATE_DUPLICATED_NAME
                result['msg'] = 'name duplicated.'
                return HttpResponse(json.dumps(result), content_type="application/json")
            #创建模板
            template = WkTemplate(name = name)
        else:
            result['status'] = WKTEMPLATE_ARGUMENT_ERROR_NAME_EMPTY
            result['msg'] = 'Need name in POST'
            return HttpResponse(json.dumps(result), content_type="application/json")
        #name结束语法判断

        #type是必填字段
        #type语法判断 与Category关联
        if 'type'in request.POST:
            type = request.POST['type'].strip()
            #类型判断
            try:
                type = int(type)
            except:
                result['status'] = -1
                result['msg'] = 'type is not int'
                return HttpResponse(json.dumps(result), content_type="application/json")
            try:
                type = Category.objects.get(id=type)
                #保存type
                template.type = type
            except Category.DoesNotExist:
                result['status']=WKTEMPLATE_ARGUMENT_ERROR_TYPE_NOT_FOUND
                result['msg'] ='404 Not find the type'
                return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = WKTEMPLATE_ARGUMENT_ERROR_TYPE_EMPTY
            result['msg'] = "Need type in POST"
            return HttpResponse(json.dumps(result), content_type="application/json")
        #type结束语法判断

        #status模板状态必填字段
        #0 代表 草稿
        #1 代表 可用
        #语法判断
        if 'status' in request.POST:
            status = request.POST['status'].strip()
            #类型判断
            try:
                status = int(status)
            except:
                result['status'] = -1
                result['msg'] = 'status is not int'
                return HttpResponse(json.dumps(result), content_type="application/json")
            #DRAFT,表示草稿
            #NORMAL，表示正式可用模板
            if(status!=DRAFT and status!=NORMAL):
                result['status'] = WKTEMPLATE_ARGUMENT_ERROR_STATUS_NOT_FOUND
                result['msg']= '404 Not find the status'
                return HttpResponse(json.dumps(result), content_type="application/json")
            #保存status
            template.status = status
        else:
            result['status'] = WKTEMPLATE_ARGUMENT_ERROR_STATUS_EMPTY
            result['msg'] = 'status is empty'
            return HttpResponse(json.dumps(result), content_type="application/json")
        #结束语法判断
        #新建工种
        if 'dept' in request.POST:
            dept = request.POST['dept'].strip()
            try:
                dept = int(dept)
            except:
                result['status'] = WKTEMPLATE_ARGUMENT_DEPT_IS_NOT_INT
                result['msg'] = 'dept is not int'
                return HttpResponse(json.dumps(result), content_type="application/json")
            #工种是不能重复的
            dept_list = WkTemplate.objects.filter(dept = dept)
            #获取到dept字段不为空,说明模板中已经保存了相应的dept.
            if(len(dept_list)!=0):
                result['status']= WKTEMPLATE_ARGUMENT_ERROR_DEPT_DUPLICATE
                result['msg'] = '404 dept is duplicate'
                return HttpResponse(json.dumps(result), content_type="application/json")
            try:
                dept = Dept.objects.get(id = dept)
                template.dept = dept
            except Dept.DoesNotExist:
                result['status'] = DEPT_NOTFOUND
                result['msg'] = '404 Not found the dept id'
                return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = WKTEMPLATE_ARGUMENT_ERROR_DEPT_EMPTY
            result['msg'] = 'Need dept in POST'
            return HttpResponse(json.dumps(result), content_type="application/json")
        #creator 创建人必填字段
        #creator 创建人必填字段
        creator = request.user
        #保存creator，modifier
        template.creator = creator
        template.modifier = creator
        template.save()
        #规则判断
        if 'rule' in request.POST:
            rule = request.POST['rule']
            #去除\r \n \t
            # rule = rule.replace('\r', '').replace('\n', '').replace('\t', '').replace('\xa0','')
            # #将字符串解析为JSON文件
            # try:
            #     rule = json.loads(rule)
            # except:
            #     #删除对应模板
            #     template.delete()
            #     result['status'] = -1
            #     result['msg'] = "json串语法格式错误"
            #     return HttpResponse(json.dumps(result), content_type="application/json")
            levels = rule['level']
            role_ids = rule['role_id']
            names = rule['name']
            approve_types = rule['approve_type']
            # 没有审批环节
            flag = 0
            for level in levels:
                flag += level
            if (flag == 0):
                result['status'] = WKTEMPLATE_ARGUMENT_ERROR_APPROVE_RULE_EMPTY
                result['msg'] = "approve_rule is empt"
                return HttpResponse(json.dumps(result), content_type="application/json")
            i = 0
            #j = 0
            while i < len(levels):
                #当前对应的级别
                level = levels[i]
                #当前级别的role_id
                role_id = int(role_ids[i])
                if(level == RECEIVE_LEVEL):
                    # role_id不为空(前端传-1,表示为空)
                    # RULE_ARGUMENT_NULL = -1
                    if(role_id) != RULE_ARGUMENT_NULL:
                        #判断role_id是否正确
                        try:
                            Role.objects.get(id = role_id)
                        except Role.DoesNotExist:
                            template.delete()
                            result['status'] = NOTFOUND
                            result['msg'] = "未找到角色实例"
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        ret = check_rule_type(role_id)
                        ret['template'] = template
                        ret['name'] = "收文规则"
                        ret['approve_type'] = RECEIVE_RULE
                        ret['level'] = RECEIVE_LEVEL
                    else:
                        i = i + 1
                        continue
                #审批人员规则
                else:
                    name = names[i]
                    #name语法判断
                    if len(name) > 200:
                        result['status'] = RULE_ARGUMENT_ERROR_NAME_TOO_LONG
                        result['msg'] = 'name too long.'
                        rule_lists = Rule.objects.filter(template = template)
                        for rule in rule_lists:
                            rule.delete()
                        template.delete()
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    #用户没有填写name
                    if name == "":
                        result['status'] = RULE_ARGUMENT_ERROR_NAME_EMPTY
                        result['msg'] = 'name is empty.'
                        rule_lists = Rule.objects.filter(template=template)
                        for rule in rule_lists:
                            rule.delete()
                        template.delete()
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    #name语法判断结束

                    #审批形式
                    approve_type = approve_types[i]
                    approve_type = int(approve_type)
                    try:
                        Role.objects.get(id = role_id)
                    except Role.DoesNotExist:
                        #规则信息错误，删除之前保存在数据库的内容。
                        rule_lists = Rule.objects.filter(template=template)
                        for rule in rule_lists:
                            rule.delete()
                        template.delete()
                        result['status'] = NOTFOUND
                        result['msg'] = "未找到角色实例"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    ret = check_rule_type(role_id)
                    # approve_type语法判断
                    if (approve_type == AND):
                        approve_type = AND
                    if (approve_type == OR):
                        approve_type = OR
                    if(approve_type == APPROVE_ONE):
                        approve_type = APPROVE_ONE

                    # approve_type为空(前端传-1表示空)
                    # RULE_ARGUMENT_NULL = -1
                    if (approve_type == RULE_ARGUMENT_NULL):
                        result['status'] = RULE_ARGUMENT_ERROR_APPROVE_TYPE_EMPTY
                        result['msg'] = 'approve_type is empty.'
                        rule_lists = Rule.objects.filter(template=template)
                        for rule in rule_lists:
                            rule.delete()
                        template.delete()
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    ret['name'] = name
                    ret['approve_type'] = approve_type
                    ret['template'] = template
                    ret['level'] = level
                Rule.objects.create(**ret)
                i = i + 1
        result['id'] = template.id
        result['status'] = SUCCESS
        result['msg'] = 'done'
        return HttpResponse(json.dumps(result), content_type="application/json")

    def put(self, request):
        """
        修改
        """
        result = {}
        user = request.user
        data = request.POST

        if 'id' in data:
            templateid = data['id']
            # 获取模板对象
            try:
                template = WkTemplate.objects.get(id=templateid)
            except WkTemplate.DoesNotExist:
                result['status'] = WKTEMPLATE_ARGUMENT_ID_NOTFOUND
                result['msg'] = 'Not find the id'
                return HttpResponse(json.dumps(result), content_type="application/json")
            result['id'] = templateid
            if 'name' in data:
                template_name = data['name']
                #name语法判断
                if len(template_name) > 200:
                    result['status'] = WKTEMPLATE_ARGUMENT_ERROR_NAME_TOO_LONG
                    result['msg'] = 'name too long.'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                elif len(template_name) == 0:
                    result['status'] = WKTEMPLATE_ARGUMENT_ERROR_NAME_EMPTY
                    result['msg'] = 'name is empty.'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                elif check_name_exist(template_name):
                    # 模板名称已经存在
                    if(template.name!=template_name):
                         result['status'] = WKTEMPLATE_DUPLICATED_NAME
                         result['msg'] = 'name duplicated.'
                         return HttpResponse(json.dumps(result), content_type="application/json")
                #name语法判断错误
                template.name = template_name
            if 'type' in data:
                template_type = data['type']
                # 模板类别为空
                if template_type == '':
                    result['status'] = WKTEMPLATE_ARGUMENT_ERROR_TYPE_EMPTY
                    result['msg'] = 'Need type in POST'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                else:
                    try:
                        template_type = int(template_type)
                        # 模板属于category中
                        category = Category.objects.get(id=template_type)
                        template.type = category
                    except Category.DoesNotExist:
                        result['status'] = WKTEMPLATE_ARGUMENT_ERROR_TYPE_NOT_FOUND
                        result['msg'] = 'Not find the type'
                        return HttpResponse(json.dumps(result), content_type="application/json")
            if 'status' in data:
                template_status = data['status']
                status = int(template_status)
                #status只有两种状态
                #DRAFT，表示模板状态为草稿
                #NORMAL，模板正式可用
                if (status == DRAFT or status == NORMAL):
                    template.status = template_status
                else:
                    result['status'] = WKTEMPLATE_ARGUMENT_ERROR_STATUS_NOT_FOUND
                    result['msg'] = 'status not found.'
                    return HttpResponse(json.dumps(result), content_type="application/json")
            if 'dept' in data:
                dept = data['dept']
                try:
                    dept = int(dept)
                except:
                    result['status'] = WKTEMPLATE_ARGUMENT_DEPT_IS_NOT_INT
                    result['msg'] = 'dept is not int'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                #模板中的dept不能重复
                try:
                    #获取模板,模板和dept是一一对应的，所以通过dept可以获取到对应的模板。
                    temp = WkTemplate.objects.get(dept = dept)
                    # 如果获取到一个模板，确认是否可以修改dept,如果已经存在一个模板对应该dept,则dept重复,不能修改。
                    if (template != temp):
                        result['status'] = WKTEMPLATE_ARGUMENT_ERROR_DEPT_DUPLICATE
                        result['msg'] = '404 dept is duplicate'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                except WkTemplate.DoesNotExist:
                    pass
                try:
                    dept = Dept.objects.get(id=dept)
                    template.dept = dept
                except Dept.DoesNotExist:
                    result['status'] = DEPT_NOTFOUND
                    result['msg'] = '404 Not found the id'
                    return HttpResponse(json.dumps(result), content_type="application/json")
            if 'rule' in data:
                rule = data['rule']
                #解析json字段
                rule = json.loads(rule)
                levels = rule['level']
                #删除原先的记录
                for level in levels:
                    ret_rule_list = Rule.objects.filter(template=template, level=level)
                    for ret_rule in ret_rule_list:
                        ret_rule.delete()
                #只有收文，没有审批
                #ONLY_EXIST_RECEIVE
                flag = 0
                for level in levels:
                    flag+=level
                if flag == 0:
                    result['status'] = RULE_ARGUMENT_ERROR_APPROVE_LEVEL_EMPTY
                    result['msg'] = "没有审批环节"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                role_ids = rule['role_id']
                names = rule['name']
                approve_types = rule['approve_type']
                i = 0
                while i < len(levels):
                    #当前角色id
                    role_id = role_ids[i]
                    # 获取对应要修改的审批
                    level = levels[i]
                    #各级审批名称
                    name = names[i]
                    # 根据模板id和审批级别level找到该模板id下的对应的收文规则
                    if level == RECEIVE_LEVEL:
                        #删除收文人员规则
                        if(role_id == -1):
                            rules = Rule.objects.filter(template = template,level = level)
                            for rule in rules:
                                rule.delete()
                            i = i + 1
                            continue
                        # 新增/修改收文规则
                        else:
                            # 对id先进行判断
                            result = {}
                            try:
                                role = Role.objects.get(id=role_id)
                            except Role.DoesNotExist:
                                result['status'] = NOTFOUND
                                result['msg'] = "未找到角色实例"
                                return HttpResponse(json.dumps(result), content_type="application/json")
                            ret = check_rule_type(role_id)
                            ret['template'] = template
                            ret['name'] = "收文规则"
                            ret['approve_type'] = 3
                            ret['level'] = 0
                        #审批规则修改
                    else:
                        # 根据模板id和审批级别level找到该模板id下的对应的审批规则
                        ret_rule = Rule.objects.filter(template=template, level=level)
                        #获取名称，收文规则用户不必填写名称，所以审批名称从[j]开始
                        approve_type = approve_types[i]
                        # name语法判断
                        if len(name) > 200:
                            result['status'] = RULE_ARGUMENT_ERROR_NAME_TOO_LONG
                            result['msg'] = 'name too long.'
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        # 用户没有填写name
                        if name == "":
                            result['status'] = RULE_ARGUMENT_ERROR_NAME_EMPTY
                            result['msg'] = 'name is empty.'
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        # name语法判断结束
                        try:
                            Role.objects.get(id=role_id)
                        except Role.DoesNotExist:
                            # 规则信息错误
                            result['status'] = NOTFOUND
                            result['msg'] = "未找到角色实例"
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        ret = check_rule_type(role_id)
                        # 审批形式
                        approve_type = approve_types[i]
                        # approve_type语法判断
                        if (approve_type == AND):
                            approve_type = AND
                        if (approve_type == OR):
                            approve_type = OR
                        if(approve_type == APPROVE_ONE):
                            approve_type = APPROVE_ONE
                        # approve_type用户不传
                        if (approve_type == int(RULE_ARGUMENT_NULL)):
                            result['status'] = RULE_ARGUMENT_ERROR_APPROVE_TYPE_EMPTY
                            result['msg'] = 'approve_type is empty.'
                            return HttpResponse(json.dumps(result), content_type="application/json")

                        ret['template'] = template
                        ret['name'] = name
                        ret['level'] = level
                        ret['approve_type'] = approve_type

                    Rule.objects.create(**ret)
                    i = i + 1
                #获取该template下所有规则
                rule_list = []
                rule_list = Rule.objects.filter(template = template)
                for rule in rule_list:
                    if(rule.level>level):
                        rule.delete()
            #保存模板基本信息
            template.save()
            #记录修改人信息
            template.modifier = request.user
            result['id'] = templateid
            result['status']  = SUCCESS
            result['msg'] = 'put done sucess'
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = WKTEMPLATE_ARGUMENT_ID_EMPTY
            result['msg'] = 'id is empty'
            return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self, request):
        """
        删除
        """
        result = {}
        user = request.user
        data = request.POST
        if 'id' in data:
            # 要删除的模板id
            template_id = data['id']
            result['id'] = template_id
            try:
                #Rule依赖WK_Template，在删除WK_Template前先删除Rule.
                rules = Rule.objects.filter(template = template_id)
                for rule in rules:
                    rule.delete()
                template = WkTemplate.objects.get(id=template_id)
                logger.warning("user:{0} has deleted template(id:{1}, name:{2}". \
                               format(user.username, template.id, template.name))
                # 删除
                template.delete()
                result['status'] = SUCCESS
                result['msg'] = 'delete done sucess'
            except WkTemplate.DoesNotExist:
                result['status'] = WKTEMPLATE_ARGUMENT_ID_NOTFOUND
                result['msg'] = '404 Not found the id'
        else:
            result['status'] = WKTEMPLATE_ARGUMENT_ERROR_NEED_ID
            result['msg'] = 'Need id in POST'
        return HttpResponse(json.dumps(result), content_type="application/json")

    
    def get_rule(self, request):
        """
               获取模板信息
               返回值为model_records_dict
        """
        content = {}
        returnjson = False

        if 'json' in request.GET:
            returnjson = True
        user = request.user

        if 'id' in request.GET:
            try:
                # 模板id
                templateid = request.GET['id']
                templateid = int(templateid)
            except ValueError:
                content['status'] = ARGUMENT_ERROR_ID_NOT_INT
                content['msg'] = 'id not int'
                return HttpResponse(json.dumps(content), content_type="application/json")
            try:
                # 返回模板对象
                template = WkTemplate.objects.get(id=templateid)

                #如果模板是草稿，也不能创建工作流
                if(int(template.status) == DRAFT):
                    content['status'] = WKTEMPLATE_ARGUMENT_STATUS_IS_DRAFT
                    content['msg'] = 'template status is draf'
                    return HttpResponse(json.dumps(content), content_type="application/json")
                user = User.objects.get(id=user.id)
                try:
                    # 规则
                    rules = Rule.objects.filter(template=template)
                    rules_list = []
                    for rule in rules:
                        #rule_type如果保存的是role_id
                        if (rule.rule_type == ROLE_ID):
                            user_lists = RoleMgr.getusers(rule.entity_id)
                            user_lists = (user_lists['msg'])['users']
                            for enitity_user_id in user_lists:
                                # 将role_user与user相同部门的信息返回
                                role_user = User.objects.get(id = enitity_user_id)
                                if role_user.dept == user.dept:
                                    #审批人id
                                    approver_id = role_user.id
                                    rules_list.append(get_rule_dict(rule, approver_id))
                            content['status'] = NOTFOUND
                            content['msg'] = '没有对应角色信息，不能创建工作流'
                            return HttpResponse(json.dumps(content), content_type="application/json")

                        else:
                            approver = User.objects.get(id=rule.entity_id)
                            #审批人员id
                            approver_id = approver.id
                            rules_list.append(get_rule_dict(rule, approver_id))

                    content['status'] = SUCCESS
                    content['msg'] = rules_list
                    return HttpResponse(json.dumps(content), content_type="application/json")

                except Rule.DoesNotExist:
                    content['status'] = RULE_NOTFOUND
                    content['msg'] = '404 This id not mapping a rule'
                    return HttpResponse(json.dumps(content), content_type="application/json")
            except WkTemplate.DoesNotExist:
                content['status'] = WKTEMPLATE_ARGUMENT_ID_NOTFOUND
                content['msg'] = '404 Not found the id'
                return HttpResponse(json.dumps(content), content_type="application/json")
            except User.DoesNotExist:
                content['status'] = RULE_ARGUMENT_ERROR_USER_ID_NOT_FOUND
                content['msg'] = 'user_id not find'
                return HttpResponse(json.dumps(content), content_type="application/json")
        # 没有id返回所有对象,返回所有模板
        else:
            content['status'] = RULE_ARGUMENT_ERROR_ID_EMPTY
            content['msg'] = 'id is empty.'
            return HttpResponse(json.dumps(content), content_type="application/json")

