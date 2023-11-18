#! -*- coding:utf-8 -*-
import json
import pdb 
import os
import time
import platform
from datetime import datetime  
from django.utils.translation import ugettext as _
from dept.models import Dept  
from appuser.models import AdaptorUser as User
from common.customjson import LazyEncoder
from notice.comm import NoticeMgr    
from category.models import Category
from appuser.comm import get_user_info
from property.entity import EntityType
from property.code import ATTRS
from attrs.models import AttrsCreate
from common.logutils import getLogger
logger = getLogger(True, 'attrs', False)

def check_name_exist(name):
    """检查属性名称是否已经存在，如果存在返回True，否则返回False"""
    return AttrsCreate.objects.filter(name=name).exists()

#检查name是否合法
def check_name(name, result):
    if len(name) > 128:
        result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NAME_TOO_LONG
        result['msg'] = 'name too long'
        return False
    elif len(name) == 0:
        result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NAME_EMPTY
        result['msg'] = 'name is empty.'
        return False
    elif check_name_exist(name):
        # 属性名称已经存在
        result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NAME_DUPLICATED
        result['msg'] = 'name duplicated.'
    else:
        return True

def check_enum(enum, result):
    # key,value验证
    # {"selectway":0,"selection":{"男":0,"女":1}}
    try:
        selectway = enum['selectway']
        if selectway != 0 and selectway != 1:
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_SELECTWAY
            result['msg'] = 'selectway is error.'
            return False
        selection = enum['selection']
        for key in selection.keys():
            # 判断字典key对应的值是否为空
            if selection.get(key, 0) == '':
                result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_VALUE_IS_NULL
                result['msg'] = 'value is null.'
                return False
        # key不能少于两个
        # 
        if len(selection) < 2:
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_KEY_LESS_TWO
            result['msg'] = 'key is less than two'
            return False
        # 通过set函数，删除重复数据，获取value个数，不相等就有重复的value
        elif len(selection.values()) != len(set(enum['selection'].values())):
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_VALUE_DUPLICATED
            result['msg'] = 'duplicate value'
            return False
        else:
            return True
    except KeyError:
        result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_SELECTKEY_NOT_EXIST
        result['msg'] = 'select key is not exist'
        return False

# 验证值是否符合布尔规范格式要求
def check_bool(value,result):
    # 
    try:
        bool = int(value)
        if bool != 0 and bool != 1:
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_BOOL_FORMAT
            result['msg'] = 'boolean format is error.'
            return False
        else:
            return True
    except ValueError:
        result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_VALUE_NOT_NUMBER
        result['msg'] = 'value not number'
        return False

# 验证值是否为字符，并进行校验
def check_char(char,result):
    if len(char) > 1024:
        result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_VALUE_TOO_LONG
        result['msg'] = 'value too long.'
        return False
    elif len(char) == 0:
        result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_VALUE_EMPTY
        result['msg'] = 'value is empty.'
        return False
    else:
        return True

# 验证值是否为数字
def check_number(value,result):
    try:
        num = int(value)
        return True
    except ValueError:
        result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_VALUE_NOT_NUMBER
        result['msg'] = 'value not number'
        return False

# 验证实体类别是否存在
def check_entitytype(entity_type,attrs_instances,result):
    
    entity_list = EntityType.get_entities()
    try:
        entity_type = int(entity_type)
        # 判断添加的实体类别是否存在
        if entity_type in entity_list:
            # 属性实体不需要判断entity_id
            # 只需要判断entity_type存不存在
            attrs_instances.entity_type = entity_type
            return True
        else:
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_ENTITY_TYPE_NOT_FOUND
            result['msg'] = 'entity_type not found'
            return False

    except ValueError:
        result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_ENTITY_TYPE_NOT_INT
        result['msg'] = 'entity_type not int'
        return False