#! -*- coding:utf-8 -*-
import json
import pdb
from django.http import HttpResponse, HttpResponseForbidden
from wktemplate.models import Rule_V2
from appuser.models import AdaptorUser as User


from rest_framework.views import APIView
from common.logutils import getLogger
from role.comm import RoleMgr
from property.code import ERROR,SUCCESS
from role.models import Role
from wktemplate.models import ExtraWorkRule

logger = getLogger(True, 'extraworkrule', False)

class ExtraWorkRuleView(APIView):
    """
    加班审批规则
    """
    
    def get(self, request):
        """
        获取加班审批规则
        """
        user = request.user
        content = {}
        message_list = []
        # 查询加班审批规则列表
        extra_work_rules = ExtraWorkRule.objects.all()
        # 空列表说明还没有创建审批规则
        if len(extra_work_rules) == 0:
            content['status'] = ERROR
            content['msg'] = "目前没有请假审批的规则,请创建"
            return HttpResponse(json.dumps(content), content_type="application/json")

        for extra_work_rule in extra_work_rules:
            message = {}
            # 保存的是用户
            if extra_work_rule.type == ExtraWorkRule.USER:
                try:
                    user = User.objects.get(id = extra_work_rule.entity_id)
                    message['id'] = user.id
                    message['name'] = user.username
                    message['level'] = extra_work_rule.level
                    message['type'] = extra_work_rule.type
                except User.DoesNotExist:
                    content['status'] = ERROR
                    content['msg'] = "用户没有找到"
                    return HttpResponse(json.dumps(content), content_type="application/json")
            # 保存的是角色
            if extra_work_rule.type == ExtraWorkRule.ROLE:
                try:
                    role = Role.objects.get(id=extra_work_rule.entity_id)
                    message['id'] = role.id
                    message['name'] = role.name
                    message['level'] = extra_work_rule.level
                    message['type'] = extra_work_rule.type
                except Role.DoesNotExist:
                    content['status'] = ERROR
                    content['msg'] = "角色没有找到"
                    return HttpResponse(json.dumps(content), content_type="application/json")
            # 将每一等级的添加中列表
            message_list.append(message)

        content['status'] = SUCCESS
        content['msg'] = message_list
        content['auth'] = {
            "can_manage_extrawork": user.has_role_perm('wktemplate.extraworkrule.can_manage_extrawork')
        }
        return HttpResponse(json.dumps(content), content_type="application/json")

    
    def post(self,request):
        """
        新建加班审批模板
        {
            "rule": [
                    {"role_id": 10, "level": 1,"type":0}, 用type == 0 来表示role_id中传的是角色id
                    {"role_id": 8, "level": 2,"type":1}   用type == 1 来表示role_id中传的是用户id
                ]
            }
        }
        """

        # 新建
        user = request.user
        # 权限认证
        # 验证是否有权限新建模板
        if not user.has_role_perm('wktemplate.extraworkrule.can_manage_extrawork'):
            return HttpResponse('Forbidden', status=403)

        if 'method' in request.POST:
            method = request.POST['method'].lower()
            if method == 'put':  # 修改
                return self.put(request)
            elif method == 'delete':  # 删除
                return self.delete(request)
        result = {}
        if not request.POST:
            data = request.data
        else:
            data = request.POST
        # 删除之前所有的数据
        extra_list = ExtraWorkRule.objects.all()
        for extra in extra_list:
            extra.delete()
        rule_list = data['rule']
        # 循环数据验证
        for rule in rule_list:
            role_id = rule['role_id']
            level = rule['level']
            try:
                type = rule['type']
            except:
                type = 1  # 默认为角色id
            # type类型判断
            try:
                type = int(type)
            except:
                result['status'] = ERROR
                result['msg'] = "type不是int"
                return HttpResponse(json.dumps(result), content_type="application/json")
            # role_id判断
            try:
                role_id = int(role_id)
            except:
                result['status'] = ERROR
                result['msg'] = "role_id不是int"
                return HttpResponse(json.dumps(result), content_type="application/json")
            # 修改时传的是role_id
            if type == Rule_V2.ROLE:
                # 通过role_id查找是否有role
                try:
                    role = Role.objects.get(id=role_id)
                    # 通过role_id查找是否role有对应的user
                    ret = RoleMgr.getusers(role.id)
                    # 如果没有根据角色找到人的话,就规则创建不成功
                    if (ret['status'] != SUCCESS):
                        # 创建过程中有错误,删除新创建的规则
                        result['status'] = ERROR
                        result['msg'] = "该角色没有对应的人"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                except Role.DoesNotExist:
                    result['status'] = ERROR
                    result['msg'] = "role没有找到"
                    return HttpResponse(json.dumps(result), content_type="application/json")

            # 修改时传的是user_id
            else:
                # 通过user_id查找是否有user
                try:
                    user = User.objects.get(id=role_id)
                except User.DoesNotExist:
                    result['status'] = ERROR
                    result['msg'] = "user没有找到"
                    return HttpResponse(json.dumps(result), content_type="application/json")

            # level判断下
            try:
                level = int(level)
            except:
                # 创建过程中有错误,删除新创建的规则
                result['status'] = ERROR
                result['msg'] = "level不是int"
                return HttpResponse(json.dumps(result), content_type="application/json")
        # 循环验证数据不报错保存数据
        for rule in rule_list:
            role_id = rule['role_id']
            level = rule['level']
            type = rule['type']
            ExtraWorkRule.objects.create(entity_id=role_id, level=level, type=type)
        # 审批模板修成功
        result['status'] = SUCCESS
        result['msg'] = "成功创建"
        return HttpResponse(json.dumps(result), content_type="application/json")

    
    def put(self,request):
        """
        修改加班模板
        {
            "rule": [
                    {"role_id": 10, "level": 1,"type":0}, 用type == 0 来表示role_id中传的是角色id
                    {"role_id": 8, "level": 2,"type":1}   用type == 1 来表示role_id中传的是用户id
                ]
            }
        }
        """
        result = {}
        if not request.POST:
            data = request.data
        else:
            data = request.POST

        rule_list = data['rule']
        # 删除之前所有的数据
        extra_list = ExtraWorkRule.objects.all()
        for extra in extra_list:
            extra.delete()
        # 循环数据验证
        for rule in rule_list:
            role_id = rule['role_id']
            level = rule['level']
            try:
                type = rule['type']
            except:
                type = 1  # 默认为角色id
            # type类型判断
            try:
                type = int(type)
            except:
                result['status'] = ERROR
                result['msg'] = "type不是int"
                return HttpResponse(json.dumps(result), content_type="application/json")
            # role_id判断
            try:
                role_id = int(role_id)
            except:
                result['status'] = ERROR
                result['msg'] = "role_id不是int"
                return HttpResponse(json.dumps(result), content_type="application/json")
            # 修改时传的是role_id
            if type == Rule_V2.ROLE:
                # 通过role_id查找是否有role
                try:
                    role = Role.objects.get(id=role_id)
                except Role.DoesNotExist:
                    result['status'] = ERROR
                    result['msg'] = "role没有找到"
                    return HttpResponse(json.dumps(result), content_type="application/json")
            # 修改时传的是user_id
            else:
                # 通过user_id查找是否有user
                try:
                    user = User.objects.get(id=role_id)
                except User.DoesNotExist:
                    result['status'] = ERROR
                    result['msg'] = "user没有找到"
                    return HttpResponse(json.dumps(result), content_type="application/json")
            # 通过role_id查找是否role有对应的user
            ret = RoleMgr.getusers(role.id)
            # 如果没有根据角色找到人的话,就规则创建不成功
            if (ret['status'] != SUCCESS):
                # 创建过程中有错误,删除新创建的规则
                result['status'] = ERROR
                result['msg'] = "该角色没有对应的人"
                return HttpResponse(json.dumps(result), content_type="application/json")
            # level判断下
            try:
                level = int(level)
            except:
                # 创建过程中有错误,删除新创建的规则
                result['status'] = ERROR
                result['msg'] = "level不是int"
                return HttpResponse(json.dumps(result), content_type="application/json")
        # 循环验证数据不报错保存数据
        for rule in rule_list:
            role_id = rule['role_id']
            level = rule['level']
            type = rule['type']
            ExtraWorkRule.objects.create(entity_id=role_id, level=level, type=type)
        # 审批模板修成功
        result['status'] = SUCCESS
        result['msg'] = "修改成功"
        return HttpResponse(json.dumps(result), content_type="application/json")

    
    def delete(self,requset):
        """
        删除请假模板
        """
        result = {}
        # 遍历请假模板
        extral_work_rules = ExtraWorkRule.objects.all()

        for extral_work_rule in extral_work_rules:
            # 删除
            extral_work_rule.delete()

        result['status'] = SUCCESS
        result['msg'] = "删除加班审批模板成功"
        return HttpResponse(json.dumps(result), content_type="application/json")