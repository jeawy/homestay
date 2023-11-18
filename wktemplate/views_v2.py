#! -*- coding:utf-8 -*-
import json
import pdb
from django.http import HttpResponse, HttpResponseForbidden
from wktemplate.models import WkTemplate_V2,Rule_V2
from appuser.models import AdaptorUser as User


from rest_framework.views import APIView
from property.code import *
from common.logutils import getLogger
from dept.models import Dept
from django.conf import settings
from wktemplate.models import Rule
from role.comm import RoleMgr
from role.models import Role

logger = getLogger(True, 'wktemplate', False)
#定义一个template_id 全局变量

def get_role(rule):
    entity_id = rule.entity_id
    role = Role.objects.get(id = entity_id)
    get_role_dict = {
        "role_id": role.id,
        "role_name":role.name
    }
    return get_role_dict

def get_wktemplate_v2_dict(template,rule):
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
        "dept":dept_id,
        "create_time": create_time,
        "creator": creator,
        "modifier": modifier,
        #"entity_id":get_role(rule),
        "level":rule.level,
        "type":rule.type
    }
    #模板中规则保存的是用户人员user_id信息
    if rule.type == 1:
        approver_id = rule.entity_id
        approver = User.objects.get(id = approver_id)
        wktemplate_dict["entity_id"] = {
            "user_id":approver_id,
            "user_name":approver.username
        }
    else:
        wktemplate_dict["entity_id"] =  get_role(rule)
        
    return  wktemplate_dict

def check_name_exist(name):
    """检查模板名称是否已经存在，如果存在返回True，否则返回False"""
    return WkTemplate_V2.objects.filter(name=name).exists()

class WkTemplateView_V2(APIView):
    """
    模板管理
    """

    
    def get(self, request):
        """
        获取模板信息
        返回值为model_records_dict
        """
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
                content['status'] = ERROR
                content['msg'] = 'dept id not int'
                return HttpResponse(json.dumps(content), content_type="application/json")
            try:
                dept = Dept.objects.get(id = template_dept)
            except Dept.DoesNotExist:
                content['status'] = ERROR
                content['msg'] = 'dept不存在'
                return HttpResponse(json.dumps(content), content_type="application/json")
            try:
                # 返回模板对象 
                template = WkTemplate_V2.objects.get(dept=dept)
                try:
                    # 规则
                    rules = Rule_V2.objects.filter(template=template)
                    
                    rules_list = []
                    for rule in rules:
                        rules_list.append(get_wktemplate_v2_dict(template, rule))
                    
                    if not rules:
                        template.delete()
                    content['status'] = SUCCESS
                    content['msg'] = rules_list
                    return HttpResponse(json.dumps(content), content_type="application/json")
                except Rule.DoesNotExist:
                    content['status'] = RULE_NOTFOUND
                    content['msg'] = '404 This id not mapping a rule'
                    return HttpResponse(json.dumps(content), content_type="application/json")
            except WkTemplate_V2.DoesNotExist:
                content['status'] = DEPT_NOTFOUND
                content['msg'] = []
                return HttpResponse(json.dumps(content), content_type="application/json")
        # 没有id返回所有对象,返回所有模板
        # 如果没有输入id,将返回所有模板信息
        else:
            templates = WkTemplate_V2.objects.all()
            templates_list = []
            rules = []
            for template in templates:
                rules = Rule_V2.objects.filter(template=template)
                for rule in rules:
                    templates_list.append(get_wktemplate_v2_dict(template, rule))
            content['msg'] = templates_list
            content['status'] = SUCCESS
            return HttpResponse(json.dumps(content), content_type="application/json")

    
    def post(self, request):
        """
        新建
        """
        result = {}
        user = request.user

        # 验证是否有权限新建模板
        if not user.has_role_perm('wktemplate.wktemplate_v2.can_manage_wktemplate_v2'):
            return HttpResponse('Forbidden', status=403)
        # 新建 
        if not request.POST:
            data = request.data
        else:
            data = request.POST 

        if 'method' in data:
            method = data['method'].lower()
            if method == 'put':  # 修改
                return self.put(request)
            elif method == 'delete':  # 删除
                return self.delete(request)

        #status模板状态必填字段
        #0 代表 草稿
        #1 代表 可用
        #语法判断
        # if 'status' in data:
        #     status = data['status'].strip()
        #     #类型判断
        #     try:
        #         status = int(status)
        #     except:
        #         result['status'] = -1
        #         result['msg'] = 'status is not int'
        #         return HttpResponse(json.dumps(result), content_type="application/json")
        #     #DRAFT,表示草稿
        #     #NORMAL，表示正式可用模板
        #     if(status!=DRAFT and status!=NORMAL):
        #         result['status'] = WKTEMPLATE_ARGUMENT_ERROR_STATUS_NOT_FOUND
        #         result['msg']= '404 Not find the status'
        #         return HttpResponse(json.dumps(result), content_type="application/json")
        #     if(status == DRAFT):
        #         #flag用于标志模板是不是可以使用，在为草稿的情况下，模板是不可以使用的
        #         template.flag = False
        #     #保存status
        #     template.status = status
        # else:
        #     result['status'] = WKTEMPLATE_ARGUMENT_ERROR_STATUS_EMPTY
        #     result['msg'] = 'status is empty'
        #     return HttpResponse(json.dumps(result), content_type="application/json")
        #结束语法判断
        #新建工种
        if 'dept' in data:
            dept_id = data['dept']
            try:
                dept_id = int(dept_id)
            except:
                result['status'] = ERROR
                result['msg'] = 'dept is not int'
                return HttpResponse(json.dumps(result), content_type="application/json")
            #工种是不能重复的
            dept_list = WkTemplate_V2.objects.filter(dept__id = dept_id) 
            #获取到dept字段不为空,说明模板中已经保存了相应的dept.
            if(len(dept_list)!=0):
                result['status']= WKTEMPLATE_ARGUMENT_ERROR_DEPT_DUPLICATE
                result['msg'] = '404 dept is duplicate'
                return HttpResponse(json.dumps(result), content_type="application/json")
            try:
                dept = Dept.objects.get(id = dept_id)
                template = WkTemplate_V2(name = dept.name)
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
        creator = request.user
        #保存creator，modifier
        template.creator = creator
        template.modifier = creator
        template.save() 
        #规则判断

        if 'rule' in data:
            #{"rule":[{"name":"张三","role_id":1,"level":1,"type":0},
            #      {"name":"李四","role_id":2,"level":2},"type":1]}
            #rule = data['rule']
            """
            #去除\r \n \t
            #rule = rule.replace('\r', '').replace('\n', '').replace('\t', '').replace('\xa0','')
            #将字符串解析为JSON文件
            '''
            try:
                rule = json.loads(rule)
            except:
                #删除对应模板
                template.delete()
                result['status'] = -1
                result['msg'] = "json串语法格式错误"
                return HttpResponse(json.dumps(result), content_type="application/json")
            """
            #获取规则列表
            rule_list = data['rule'] 
            flag = True
            for rule in rule_list:
                try:
                    level = rule['level']
                except:
                    #删除创建好的模板
                    template.delete()
                    result['status'] = ERROR
                    result['msg'] = '规则中需要level'
                    return HttpResponse(json.dumps(result), content_type="application/json")

                try:
                    role_id = rule['role_id']
                except:
                    #删除创建好的模板
                    template.delete()
                    result['status'] = ERROR
                    result['msg'] = '规则中需要role_id'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                #role_id判断
                try:
                    role_id = int(role_id)
                except:
                    result['status'] = ERROR
                    result['msg'] = '角色id不是int类型'
                    template.delete()
                    return HttpResponse(json.dumps(result), content_type="application/json")
                
                try:
                    if 'type' in rule:
                        type = rule['type']
                        type = int(type)
                        if (type<0 or type>1):
                            template.delete()
                            result['status'] = ERROR
                            result['msg'] = 'type只能为0或者1'
                            return HttpResponse(json.dumps(result), content_type="application/json")
                    else:
                        type = 0 # 默认role_id中传的是角色id
                except:
                    # 删除创建好的模板
                    template.delete()
                    result['status'] = ERROR
                    result['msg'] = '规则中需要int类型的type'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                #传的是角色信息
                if type == 0:
                    try:
                        Role.objects.get(id = role_id)
                    except Role.DoesNotExist:
                        result['status'] = ERROR
                        result['msg'] = '在角色表中没有找到相关角色'
                        #删除创建好的模板
                        template.delete()
                        return HttpResponse(json.dumps(result), content_type="application/json")
                        
                    data = RoleMgr.getusers(role_id)
                    if data['status'] == SUCCESS:
                        #角色后面没有对应的用户，肯定是不能创建模板的
                        if len((data['msg'])['users']) == 0:
                            result['status'] = ERROR
                            result['msg'] = '角色没有对应的user'
                            template.delete()
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        #说明一个角色有两个或者以上的user
                        elif len((data['msg'])['users']) >=2:
                            user_ids = (data['msg'])['users']
                            for user_id in user_ids:
                                status = True
                                user = User.objects.get(id=user_id)
                                # 获取这个user所在的部门
                                user_dept_list = user.depts.all()
                                # 判断下user_dept是否和template中的dept是否一致
                                # 一致的情况下，将flag改为true
                                for user_dept in user_dept_list:
                                    if user_dept == template.dept:
                                        status = True
                                        # 跳出本次循环,去查验下个规则
                                        break
                                    else:
                                        status = False
                                if status:
                                    break
                                # 一个角色对应一个人，一个公司只有一个人是这个职位
                            else:
                                status = True
                            flag = flag and status
    
                    #对level进行判断
                    try:
                        level = int(level)
                    except:
                        result['status'] = ERROR
                        result['msg'] = 'level不是int类型'
                        template.delete()
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    Rule_V2.objects.create(entity_id = role_id,level = level,template = template)
                #如果传递user
                else: #type = 1 传递是user
                    Rule_V2.objects.create(entity_id=role_id, level=level, template=template,type = type)
                #如果各个审批规则审批人都是合格的，模板可用
                if flag == True:
                    template.flag = True
                    template.save()
        else:
            result['status'] = ERROR
            result['msg'] = '创建模板时，需要审批规则'
            #删除创建好的模板
            template.delete()
            return HttpResponse(json.dumps(result), content_type="application/json")
        result['id'] = template.id
        result['status'] = SUCCESS
        result['msg'] = '模板创建成功'
        return HttpResponse(json.dumps(result), content_type="application/json")

    
    def put(self,request):
        """
        修改模板
        """
        # {
        #     id:1
        #     "rule": [
        #         {"role_id": 10, "level": 1},
        #         {"role_id": 8, "level": 2}
        #     ]
        # }
        user = request.user
        #验证是否有修改模板的权限
        if not user.has_role_perm('wktemplate.wktemplate_v2.can_manage_wktemplate_v2'):
            return HttpResponse('Forbidden', status=403)
        result = {}
        if not request.POST:
            data = request.data
        else:
            data = request.POST

        if 'id' in data:
            id = data['id']
            # id类型判断
            try:
                id = int(id)
            except:
                result['status'] = ERROR
                result['msg'] = "id不是int类型"
                return HttpResponse(json.dumps(result), content_type="application/json")
            # 找模板
            try:
                template = WkTemplate_V2.objects.get(id=id)
            except WkTemplate_V2.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = "该模板不存在"
                return HttpResponse(json.dumps(result), content_type="application/json")
            #找到原始的规则
            origin_rule_list = Rule_V2.objects.filter(template = template)
            for rule in origin_rule_list:
                #删除原始的审批规则
                rule.delete()

            # 获取修改的模板规则
            rule_list = data['rule']
            """
            {
            "id":1,
            "rule": [
                    {"role_id": 10, "level": 1,"type":0}, 用type == 0 来表示role_id中传的是角色id
                    {"role_id": 8, "level": 2,"type":1}   用type == 1 来表示role_id中传的是用户id
                ]
            }
            """
            # 创建新的规则
            for rule in rule_list:
                role_id = rule['role_id']
                level = rule['level']
                try:
                    type = rule['type']
                except:
                    type = 1 #默认为角色id
                # type类型判断
                try:
                    type = int(type)
                except:
                    # 创建过程中有错误,删除新创建的规则
                    rule_instance_list = Rule_V2.objects.filter(template=template)
                    for rule in rule_instance_list:
                        # 删除
                        rule.delete()
                    result['status'] = ERROR
                    result['msg'] = "type不是int"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                #role_id判断
                try:
                    role_id = int(role_id)
                except:
                    #创建过程中有错误,删除新创建的规则
                    rule_instance_list = Rule_V2.objects.filter(template = template)
                    for rule in rule_instance_list:
                        #删除
                        rule.delete()
                    result['status'] = ERROR
                    result['msg'] = "role_id不是int"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                #修改时传的是role_id
                if type == Rule_V2.ROLE:
                    # 通过role_id查找是否有role
                    try:
                        role = Role.objects.get(id = role_id)
                    except Role.DoesNotExist:
                        rule_instance_list = Rule_V2.objects.filter(template=template)
                        for rule in rule_instance_list:
                            #删除
                            rule.delete()
                        result['status'] = ERROR
                        result['msg'] = "role没有找到"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                #修改时传的是user_id
                else:
                    # 通过role_id查找是否有role
                    try:
                        role = User.objects.get(id=role_id)
                    except User.DoesNotExist:
                        rule_instance_list = Rule_V2.objects.filter(template=template)
                        for rule in rule_instance_list:
                            # 删除
                            rule.delete()
                        result['status'] = ERROR
                        result['msg'] = "role没有找到"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                #通过role_id查找是否role有对应的user
                ret = RoleMgr.getusers(role_id)
                #如果没有根据角色找到人的话,就规则创建不成功
                if(ret['status']!=SUCCESS):
                    # 创建过程中有错误,删除新创建的规则
                    rule_instance_list = Rule_V2.objects.filter(template=template)
                    for rule in rule_instance_list:
                        # 删除
                        rule.delete()
                #level判断下
                try:
                    level = int(level)
                except:
                    # 创建过程中有错误,删除新创建的规则
                    rule_instance_list = Rule_V2.objects.filter(template=template)
                    for rule in rule_instance_list:
                        # 删除
                        rule.delete()
                    result['status'] = ERROR
                    result['msg'] = "role_id不是int"
                    return HttpResponse(json.dumps(result), content_type="application/json")

                #创建rule
                Rule_V2.objects.create(entity_id = role.id,level = level,template = template,type = type)
            #审批模板修成功
            result['status'] = SUCCESS
            result['msg'] = "审批模板修改成功"
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = ERROR
            result['msg'] = "没有提供要修改的模板id"
            return HttpResponse(json.dumps(result), content_type="application/json")

    
    def delete(self, request):
        """
        删除审批模板
        """
        result = {}
        user = request.user
        #验证是否有删除模板的权限
        if not user.has_role_perm('wktemplate.wktemplate_v2.can_manage_wktemplate_v2'):
            return HttpResponse('Forbidden', status=403)
        if not request.POST:
            data = request.data
        else:
            data = request.POST
        if 'id' in data:
            id = data['id']
            #id类型判断
            try:
                id = int(id)
            except:
                result['status'] = ERROR
                result['msg'] = "id不是int类型"
                return HttpResponse(json.dumps(result), content_type="application/json")
            #找模板
            try:
                template = WkTemplate_V2.objects.get(id = id)
            except WkTemplate_V2.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = "该模板不存在"
                return HttpResponse(json.dumps(result), content_type="application/json")
            #删除模板
            template.delete()
            result['status'] = SUCCESS
            result['msg'] = "模板删除成功"
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = ERROR
            result['msg'] = "没有提供要删除的模板id"
            return HttpResponse(json.dumps(result), content_type="application/json")