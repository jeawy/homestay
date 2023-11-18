# ！ -*- coding:utf-8 -*-
import os
import pdb
from common.fileupload import FileUpload
from wktemplate.models import WkTemplate
from property.code import *
from common.logutils import getLogger
from wktemplate.models import Rule
from appuser.models import AdaptorUser as User
from role.views import RoleMgr
logger = getLogger(True, 'appfile', False)


class TemplateMgr(object):
    """
    使用模板接口
    """

    @classmethod
    def getuser(cls, user_id,template_id):
        """
        根据用户id和模板id绑定对应的审批人/收文人相关信息
        """
        result = {
            "status": SUCCESS,
            "msg": ""
        }
        try:
            user = User.objects.get(id = user_id)
        except User.DoesNotExist:
            result["status"] = USER_NOT_FOUND
            result ["msg"] = "未找到指定用户"
            return result
        try:
            template = WkTemplate.objects.get(id = template_id)
        except WkTemplate.DoesNotExist:
            result["status"] = WKTEMPLATE_ARGUMENT_ID_NOTFOUND
            result["msg"] = "Not find the id"
            return result

        rule_lists = Rule.objcets.filter(template_id)
        for rule in rule_lists:
            #如果保存的是role_id
            if(rule.rule_type == ROLE_ID):
                user_lists = RoleMgr.getusers(rule.entity_id)
                for role_user in user_lists:
                    #将role_user与user相同部门的信息返回
                    if role_user.dept == user.dept:
                        #审批级别
                        result['level'] = rule.level
                        #审批人
                        result['approver'] = role_user
                        #审批类型
                        result['approver_type'] = rule.approve_type
                        return result
            else:
                approver = User.objects.get(id = rule.entity_id)
                result['level'] = rule.level
                result['approver'] = approver
                result['approver_type'] = rule.approve_type
                return result



