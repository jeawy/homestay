import pdb
from this import i
import logging
from django.contrib.auth.models import User
from django.template.base import logger

from appuser.models import AdaptorUser as User 


from common.logutils import getLogger
from dept.models import Dept
from property.code import SUCCESS, ERROR, ATTRS

result = {
    'status': SUCCESS
}
data = {}
content = {}



def check_name(name):
    if len(name) > 128:
        logger.info("用户名长度过长")
        return True
    elif len(name) == 0:
        logger.info("用户名长度为0")
        return True
    else:
        return False


def check_email(email):
    if len(email) > 128:
        logger.info("email长度过长")
        return True
    elif len(email) == 0:
        logger.info("email长度为0")
        return True
    else:
        return False


def check_name_exist(name, excludeid=None):
    """检查名称是否已经存在，如果存在返回True，否则返回False"""
    if excludeid:
        # 排除指定id记录
        return User.objects.filter(username=name).exclude(id=excludeid).exists()
    else:
        return User.objects.filter(username=name).exists()


def check_email_exist(email, excludeid=None):
    """检查email是否已经存在，如果存在返回True，否则返回False"""
    if excludeid:
        # 排除指定id记录
        return User.objects.filter(email=email).exclude(id=excludeid).exists()
    else:
        return User.objects.filter(email=email).exists()


def check_phone_exist(phone, excludeid=None):
    """检查phone是否已经存在，如果存在返回True，否则返回False"""
    if excludeid:
        # 排除指定id记录
        return User.objects.filter(phone=phone).exclude(id=excludeid).exists()
    else:
        return User.objects.filter(phone=phone).exists()
 
# def check_sex(sex):
#     # 性别列表
#     # 0 代表 男
#     # 1 代表 女
#     sex_codes = [0,1]
#     # 如果前端传递的性别在性别列表中 返回True,否则返回False
#     if sex in sex_codes:
#         return True
#     else:
#         return False
# 验证值是否符合布尔规范格式要求
def check_bool(isactive, result):
    try:
        bool = int(isactive)
        if bool != 0 and bool != 1:
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_BOOL_FORMAT
            result['msg'] = 'isactive字段只能为0或1'
            return True
        else:
            return False
    except ValueError:
        result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_VALUE_NOT_NUMBER
        result['msg'] = ' isactive字段只能为数字'
        return True


# 验证值是否为数字
def check_number(value, result):
    try:
        num = int(value)
        return False
    except ValueError:
        result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_VALUE_NOT_NUMBER
        result['msg'] = '输入值不为数字'
        return True


# 验证性别是否正确
def check_sex(value, result):
    if value == '男' or value == '女':
        return True
    else:
        result['status'] = ERROR
        result['msg'] = '性别不合法'
        return False
