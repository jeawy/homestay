import pdb
import traceback
from attrs.models import AttrsBind, AttrsCreate, AttrsInstances
import json
import time

from attrs.comm import check_entitytype, check_number, check_char, check_bool, check_enum,\
    check_name_exist,check_name, check_enum 
from property.code import *
from property.entity import EntityType, AttrsTypes
from property import settings
from common.logutils import getLogger 
logger = getLogger(True, 'attrs', False)

class AttrsFunction(object):
    """
    属性管理
    """
    @staticmethod
    def getattrs(entity_id= None,entity_type = None):
        """
        绑定属性后，
        通过entity_id，entity_type获取属性绑定信息
        entity_id: 实体id
        entity_type: 实体类别
        返回属性列表
        例如：{'attr_id': 1, 'attr_name': '数字', 'attr_type': 1,
        'default': '33', 'attr_value': '33'}
        """
        result = {}
        search_dict = dict()
        attr_dict = dict()

        try:
            entity_id = int(entity_id)
            entity_type = int(entity_type)
            # 获取entity_type列表
            entity_list = EntityType.get_entities()
            # 判断entity_type是否存在
            if not entity_type in entity_list:
                result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_ENTITY_TYPE_NOT_FOUND
                result['msg'] = 'entity_type not found'
                return result
             
            search_dict['entity_id'] = entity_id
            search_dict['entity_type'] = entity_type
            # 查询结果转化为字典列表 <QuerySet [{'attr': 1}]>
            attrs = AttrsInstances.objects.filter(**search_dict)
            return_list = []
            for attr_item in attrs:
                attr_dict['name'] = attr_item.attr_name
                attr_dict['type'] = attr_item.attr_type 
                attr_dict['value'] = attr_item.attr_value
                attr_dict['id'] = attr_item.id 
                return_list.append(attr_dict)
            return return_list
            
        except ValueError:
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_ENTITY_NOT_INT
            result['msg'] = 'entity_id or entity_type not int'
            return result

     
    @staticmethod
    def setattr_item(attr_dict, entity_id):
        """
        保存属性实体信息
        attr_dict:
        用字典传属性实体的信息
        例如：{'entity_id': 1, 'entity_type': 1, 'attr_name': '数字',
        'attr_value': 33, 'attr_type': 1}
        字段都是必需的
        保存成功，返回result字典
        """
        attrs_instances = AttrsInstances()
        result = {}
        try:
            # 用户先调用getattrs()方法获取属性信息，进行填写后提交保存
            # entity_id,attr_name不能修改
            # entity_type之前方法已经进行验证
            # 只需对attr_value进行验证
            entity_type = attr_dict['entity_type']
            entity_type = int(entity_type)
            attr_name = attr_dict['attr_name']
            if len(attr_name) > 128:
                result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NAME_TOO_LONG
                result['msg'] = 'name too long'
                return result
            elif len(attr_name) == 0:
                result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NAME_EMPTY
                result['msg'] = 'name is empty.'
                return result
            else:
                attrs_instances.attr_name = attr_name
            attr_value = attr_dict['attr_value']
            attr_type = attr_dict['attr_type']
            if attr_type == AttrsTypes.NUMBER:
                if not check_number(attr_value, result):
                    return result
                else:
                    attrs_instances.attr_value = attr_value
            # 2 字符
            elif attr_type == AttrsTypes.CHARACTER:
                if not check_char(attr_value, result):
                    return result
                else:
                    attrs_instances.value = attr_value
            # 3 日期
            elif attr_type == AttrsTypes.DATE:
                # 日期类型的值：attr_value: '2012/12/12'
                try:
                    date = time.strptime(attr_value, settings.DATEFORMAT)
                    attrs_instances.attr_value = date
                except ValueError:
                    result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_DATE_FORMAT
                    result['msg'] = 'date time format is error.'
                    return result
            # 4 布尔
            elif attr_type == AttrsTypes.BOOLEAN:
                if not check_bool(attr_value, result):
                    return result
                else:
                    attrs_instances.attr_value = attr_value

            # 5 枚举
            elif attr_type == AttrsTypes.ENUMERATE:
                # 枚举类型的值：attr_value:
                #  '{"selectway": 0, "selection": {"男": 0, "女": 1}, "selected":0}'
                try:
                    attr_value = attr_value.replace("'", '"')
                    enum = json.loads(attr_value)
                    if not check_enum(enum, result):
                        return result
                    else:
                        attrs_instances.attr_value = enum
                except ValueError:
                    result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_TYPE_NOT_ENUMERATE
                    result['msg'] = 'type not enumerate'
                    return result
            attrs_instances.entity_id = entity_id
            attrs_instances.entity_type = entity_type
            attrs_instances.attr_value = attr_value
            attrs_instances.attr_type = attr_type
            attrs_instances.save()
            result['status'] =  SUCCESS
            result['msg'] =  attrs_instances.id
            #return True
        except:
            logger.error(traceback.format_exc())
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_DICT_MISS_FIELD_OR_FILE_ERROR
            result['msg'] = '字典属性字段缺失或填写错误'
        return result

    @staticmethod
    def setattrs(attrs, entity_id):
        """
        批量设置属性实体
        attr_list 是实体填写好的属性列表
        """
        saved_ids = []
        result = {'status':SUCCESS, 'msg':"已保存"}
        try: 
            if isinstance(attrs, bytes):
                attrs = attrs.decode("utf-8")
             
            attrs_list = json.loads(attrs)
            for attr_item in attrs_list:
                result = AttrsFunction.setattr_item(attr_item, entity_id)
                if result['status'] is not SUCCESS:
                    # 删除已经保存的属性实体，并退出
                    if saved_ids:
                        AttrsInstances.objects.filter(id__in = saved_ids).delete()
                    return result
        except ValueError:
            logger.error(traceback.format_exc())
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NOT_DICT
            result['msg'] ='自定义属性格式错误'
        return result

    def updateattrs(id=None,value=None):
        """
        修改属性值，更新属性实体信息
        id: 属性实体id
        value: 属性值
        修改成功返回true
        """
        result = {}
        try:
            instance_id = int(id)
        except ValueError:
            result['status'] = ARGUMENT_ERROR_ID_NOT_INT
            result['msg'] = 'id not int'
            return result

        try:
            instance = AttrsInstances.objects.get(id=instance_id)
            # 获取属性类型
            attr_type = instance.attr_type
            if attr_type == AttrsTypes.NUMBER:
                if not check_number(value, result):
                    return result
                else:
                    instance.attr_value = value
            # 2 字符
            elif attr_type == AttrsTypes.CHARACTER:
                if not check_char(value, result):
                    return result
                else:
                    instance.attr_value = value

            # 3 日期
            elif attr_type == AttrsTypes.DATE:
                try:
                    date = time.strptime(value, settings.DATEFORMAT)
                    instance.attr_value = date
                except ValueError:
                    result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_DATE_FORMAT
                    result['msg'] = 'date time format is error.'
                    return result
            # 4 布尔
            elif attr_type == AttrsTypes.BOOLEAN:
                if not check_bool(value, result):
                    return result
                else:
                    instance.attr_value = value
            # 5 枚举
            elif attr_type == AttrsTypes.ENUMERATE:
                try:  
                    value = value.replace("'", '"')
                    enum = json.loads(value) 
                    if not check_enum(enum, result):
                        return result
                    else:
                        instance.attr_value = enum
                except TypeError:
                    result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_TYPE_NOT_ENUMERATE
                    result['msg'] = 'type not enumerate'
                    return result
            else:
                result['status'] = ATTRS.ATTRS_NOTFOUND_ATTR_TYPE
                result['msg'] = '404 Not find the attr type'
                return result
            instance.save()
            result['status'] = SUCCESS
            result['msg'] = instance.id

        except AttrsInstances.DoesNotExist:
            result['status'] = ATTRS.ATTRS_NOTFOUND
            result['msg'] = '404 Not found the id'
            return result

    def readattrs(entity_id=None,entity_type=None):
        """
        通过entity_id,entity_type获取属性实体信息
        entity_id: 实体id
        entity_type: 实体类别
        返回属性实体字典列表
        例如：[{'id': 9, 'entity_id': 50, 'entity_type': 2,
        'attr_name': '测', 'attr_value': "{'selectway': 0,
        'selection': {'男': 0, '女': 1}}", 'attr_type': 5}]
        """
        result = {}
        search_dict = dict()

        try:
            entity_id = int(entity_id)
            entity_type = int(entity_type)
            # 获取entity_type列表
            entity_list = EntityType.get_entities()
            # 判断entity_type是否存在
            if not entity_type in entity_list:
                result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_ENTITY_TYPE_NOT_FOUND
                result['msg'] = 'entity_type not found'
                return result
            try:
                search_dict['entity_id'] = entity_id
                search_dict['entity_type'] = entity_type
                # 查询结果转化为字典列表
                bind_id = AttrsInstances.objects.filter(**search_dict).values()
                bind_list = list(bind_id)
                return bind_list
            except AttrsInstances.DoesNotExist:
                result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_ENTITY_NOT_FOUND
                result['msg'] = 'entity_id or entity_type not found'
                return result
        except ValueError:
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_ENTITY_NOT_INT
            result['msg'] = 'entity_id or entity_type not int'
            return result

