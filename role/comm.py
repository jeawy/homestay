#！ -*- coding:utf-8 -*-
import pdb
from role.models import Role
from property.code import ERROR,SUCCESS
from common.logutils import getLogger
logger = getLogger(True, 'appfile', False)


class RoleMgr(object):
    """
    角色管理接口
    """
    @classmethod
    def getusers(cls, roleid):
        """
        根据角色id获取用户列表，并返回角色实例
        apptype: app类型
        appid：app id
        返回： 文件列表
        """
        result = {
            "status":SUCCESS,
            "msg":""
        }
        try:
            role = Role.objects.get(id = roleid)
            userids = [user.id for user in role.users.all()]
            result['msg'] = {'role':role, 'users':userids}
        except Role.DoesNotExist:
            result['status'] = ERROR
            result['msg'] = "未找到角色实例"
        
        return result


