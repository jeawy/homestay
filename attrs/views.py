import pdb
import time
import json
import traceback

from rest_framework.views import APIView
from datetime import datetime

from attrs.interface import AttrsFunction
from attrs.models import AttrsCreate, AttrsBind, AttrsInstances
from common.logutils import getLogger

from django.http import HttpResponse

from attrs.comm import check_entitytype, check_number, check_char, check_bool, check_enum,\
    check_name_exist,check_name, check_enum
from excel.imageparsing import compenent
from property import settings
from property.code import *
from property.entity import EntityType, AttrsTypes 
from dept.models import Dept
from appuser.models import AdaptorUser as User
from wktemplate.models import WkTemplate_V2

logger = getLogger(True, 'attrs', False)

class TestView(APIView): 
    def get(self, request):
        """
        查询
        """
        content = {} 
        user = request.user
        if 'id' in request.GET:
            id = request.GET['id']

            try:
                id = int(id)
            except ValueError:
                content['status'] = ARGUMENT_ERROR_ID_NOT_INT
                content['msg'] = 'id not int'
                return HttpResponse(json.dumps(content), content_type="application/json")

            try: 
                excel_path = 'D:\\wk\\EP11任务分配表.xlsx'
            
                content['status'] = SUCCESS
            except AttrsBind.DoesNotExist:
                content['status'] = ATTRS.ATTRS_NOTFOUND
                content['msg'] = '404 Not found the id'
        return HttpResponse(json.dumps(content), content_type="application/json")


def get_attrsinstance_dict(attrs_instance):
    '''
        返回attrsinstance_dict的字典实例
        字典格式：
        {
            "id": attrs_instance.id,
            "entity_id": attrs_instance.entity_id,
            "entity_name":
            "entity_type": attrs_instance.entity_type,
            "attr_name": attrs_instance.attr_name,
            "attr_value": attrs_instance.attr_value,
            "attr_type": attrs_instance.attr_type
        }
        '''
    result = {}
    entity_id = attrs_instance.entity_id
    entity_type = attrs_instance.entity_type
    attrsinstance_dict = {
        "id": attrs_instance.id,
        "entity_id": entity_id,
        "entity_type": attrs_instance.entity_type,
        "attr_name": attrs_instance.attr_name,
        "attr_value": attrs_instance.attr_value,
        "attr_type": attrs_instance.attr_type
    }

    # 根据entity_type去找对应的实体属性EntityType
    if entity_type  not in EntityType.get_entities():
        result['status'] = ERROR
        result['msg'] = "没有该实体类型"
        return HttpResponse(json.dumps(result),content_type="application/json")

    # 设置默认为None
    attrsinstance_dict['entity_name'] = None
    try:
         
        # 模板实体
        if entity_type == EntityType.WK_TEMPLATE:
            attrsinstance_dict['entity_name'] = WkTemplate_V2.objects.get(id = entity_id).name
         
        # 工种实体
        if entity_type == EntityType.WORKTYPE:
            attrsinstance_dict['entity_name'] = Dept.objects.get(id = entity_id).name
        # 用户实体
        if entity_type == EntityType.USER:
            attrsinstance_dict['entity_name'] = User.objects.get(id = entity_id).username
    except:
        pass
    return attrsinstance_dict

def get_attrsbind_dict(attrs_bind):
    '''
        返回attrs_bind的字典实例
        字典格式：
        {
            "id": attrs_bind.id,
            "attr_type": attrs_bind.attr.type,
            "attr_name": attrs_bind.attr.name,
            "attr_value": attrs_bind.attr.value,
            "attr_default": attrs_bind.attr.default,
            "entity_id": attrs_bind.entity_id,
            "entity_type": attrs_bind.entity_type
        }
        '''
    attrsbind_dict = {
        "id": attrs_bind.id,
        "attr_type": attrs_bind.attr.type,
        "attr_name": attrs_bind.attr.name,
        "attr_value": attrs_bind.attr.value,
        "attr_default": attrs_bind.attr.default,
        "entity_id": attrs_bind.entity_id,
        "entity_type": attrs_bind.entity_type
    }
    return attrsbind_dict

def get_attrscreate_dict(attrs_create):
    '''
    返回attrs_create的字典实例
    字典格式：
    {
                    "id":attrs_create.id,
                    "name":attrs_create.name,
                    "type":attrs_create.type,
                    "value":attrs_create.value,
                    "default": attrs_create.default
    }
    '''
    attrscreate_dict = {}
    attrscreate_dict['id'] = attrs_create.id
    attrscreate_dict['name'] = attrs_create.name
    attrscreate_dict['type'] = attrs_create.type
    attrscreate_dict['value'] = attrs_create.value
    attrscreate_dict['default'] = attrs_create.default
    return attrscreate_dict



class AttrsView(APIView):
    """
    属性创建的功能
    增加属性
    修改属性的名称
    删除属性
    查询属性的名称，类型，值
    """ 
    def get(self, request):
        """
        查询
        """
        content = {} 
        user = request.user
        kwargs = {}
        auth = user.has_role_perm('attrs.attrscreate.can_manage_attr')
        content['auth'] = {
            "manage_attr" : auth
        }
    
        if 'id' in request.GET:
            attrs_id = request.GET['id']
            try:
                attrs_id = int(attrs_id)
            except ValueError:
                content['status'] = ARGUMENT_ERROR_ID_NOT_INT
                content['msg'] = 'id not int'
                return HttpResponse(json.dumps(content), content_type="application/json")
            try:
                attrs_create = AttrsCreate.objects.get(id=attrs_id)
                content['status'] = SUCCESS
                content['msg'] = get_attrscreate_dict(attrs_create)
                return HttpResponse(json.dumps(content), content_type="application/json")
            except AttrsCreate.DoesNotExist:
                content['status'] = ATTRS.ATTRS_NOTFOUND
                content['msg'] = '404 Not found the id'

        elif 'name' in request.GET:
            name = request.GET['name'].strip()
            kwargs['name__icontains'] = name
        # 按照类型筛选
        elif 'type' in request.GET:
            try:
                type = int(request.GET['type'])
                kwargs['type'] = type
            except:
                content['status'] = ERROR
                content['msg'] = 'type不是int'

        # 按照默认值筛选
        elif 'default' in request.GET:
            default = request.GET['default']
            kwargs['default'] = default

        # 按照值筛选
        elif 'value' in request.GET:
            value = request.GET['value']
            kwargs['value'] = value

        attrs_creates = AttrsCreate.objects.filter(**kwargs)
        attrs_creates_list = []
        for attrs_create in attrs_creates:
            attrs_creates_list.append(get_attrscreate_dict(attrs_create))
        content['status'] = SUCCESS
        content['msg'] = attrs_creates_list
        return HttpResponse(json.dumps(content), content_type="application/json")
 
    def post(self, request):
        """
        创建属性
        """

        result = {}
        user = request.user
        # 新建
        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST
        if 'method' in data:
            method = data['method'].lower()
            if method == 'put':  # 修改
                return self.put(request)
            elif method == 'delete':  # 删除
                return self.delete(request)

        # 
        # 创建属性
        attrs_create = AttrsCreate()
        attrs_create.creator = user
        # name字段是属性名称，最大长度为128
        if 'name' in request.POST:
            name = request.POST['name'].strip()
            if not check_name(name, result):
                return HttpResponse(json.dumps(result), content_type="application/json")
            else:
                attrs_create.name = name
        else:
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NEED_NAME
            result['msg'] = 'Need name in POST'
            return HttpResponse(json.dumps(result), content_type="application/json")

        # type 属性类型判断
        # 1 代表 数字
        # 2 代表 字符 长度不超过1024
        # 3 代表 日期
        # 4 代表 布尔
        # 5 代表 枚举
        # 
        if 'type' in request.POST:
            type = request.POST['type'].strip()
            try:
                ty = int(type)
                # 1 数字
                types_list = AttrsTypes.get_attrs()
                if ty in types_list:
                    if ty == AttrsTypes.NUMBER:
                        attrs_create.type = ty
                        if 'value' in request.POST:
                            value = request.POST['value'].strip()
                            if not check_number(value, result):
                                return HttpResponse(json.dumps(result), content_type="application/json")
                            else:
                                attrs_create.value = value
                        if 'default' in request.POST:
                            default = request.POST['default'].strip()
                            if not check_number(default, result):
                                return HttpResponse(json.dumps(result), content_type="application/json")
                            else:
                                attrs_create.default = default
                        else:
                            if 'value' in request.POST:
                                attrs_create.default = value
                    # 2 字符
                    elif ty == AttrsTypes.CHARACTER:
                        attrs_create.type = ty
                        # 
                        if 'value' in request.POST:
                            char = request.POST['value'].strip()
                            if not check_char(char, result):
                                return HttpResponse(json.dumps(result), content_type="application/json")
                            else:
                                attrs_create.value = char
                        if 'default' in request.POST:
                            default = request.POST['default'].strip()
                            if not check_char(default, result):
                                return HttpResponse(json.dumps(result), content_type="application/json")
                            else:
                                attrs_create.default = default
                        else:
                            if 'value' in request.POST:
                                attrs_create.default = char

                    # 3 日期
                    elif ty == AttrsTypes.DATE:
                        attrs_create.type = ty
                        if 'value' in request.POST:
                            value = request.POST['value'].strip()
                            try:
                                date = datetime.strptime(value, settings.DATETIMEFORMAT)
                                attrs_create.value = date
                            except ValueError:
                                result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_DATE_FORMAT
                                result['msg'] = 'date time format is error.'
                                return HttpResponse(json.dumps(result), content_type="application/json")
                        if 'default' in request.POST:
                            default = request.POST['default'].strip()
                            try:
                                date = datetime.strptime(default, settings.DATETIMEFORMAT)
                                attrs_create.default = date
                            except ValueError:
                                result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_DATE_FORMAT
                                result['msg'] = 'date time format is error.'
                                return HttpResponse(json.dumps(result), content_type="application/json")
                        else:
                            if 'value' in request.POST:
                                attrs_create.default = date
                    # 4 布尔
                    elif ty == AttrsTypes.BOOLEAN:
                        attrs_create.type = ty
                        if 'value' in request.POST:
                            value = request.POST['value'].strip()
                            if not check_bool(value, result):
                                return HttpResponse(json.dumps(result), content_type="application/json")
                            else:
                                attrs_create.value = value
                        if 'default' in request.POST:
                            default = request.POST['default'].strip()
                            if not check_bool(default, result):
                                return HttpResponse(json.dumps(result), content_type="application/json")
                            else:
                                attrs_create.default = default
                        else:
                            if 'value' in request.POST:
                                attrs_create.default = value
                    # 5 枚举
                    elif ty == AttrsTypes.ENUMERATE:
                        attrs_create.type = ty
                        # 
                        if 'value' in request.POST:
                            value = request.POST['value'].strip()
                            # 枚举类型验证
                            # 将字符串转化为字典
                            # 
                            try:
                                # 不用判断重复key，API中给出重复key的处理方法的说明
                                # json.loads()传的字符串要用双引号
                                # json.loads()会自动删除重复的key，保留最后的key，value
                                # 例如{"aa": 1, "aa": 2, "bb": 1， "bb": 2}
                                # json.loads()处理后，保留{"aa": 2,"bb": 2}
                                try:
                                    enum = json.loads(value)
                                except json.decoder.JSONDecodeError:
                                    result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_TYPE_NOT_ENUMERATE
                                    result['msg'] = '枚举格式错误'
                                    return HttpResponse(json.dumps(result), content_type="application/json")
                                if not check_enum(enum, result):
                                    return HttpResponse(json.dumps(result), content_type="application/json")
                                else:
                                    attrs_create.value = enum
                                value_list = list(enum['selection'].values())
                                # 默认default值为第一个key对应的值
                                attrs_create.default = value_list[0]
                            except TypeError:
                                result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_TYPE_NOT_ENUMERATE
                                result['msg'] = 'type not enumerate'
                                return HttpResponse(json.dumps(result), content_type="application/json")
                        if 'default' in request.POST:
                            default = request.POST['default'].strip()
                            if not check_number(default, result):
                                return HttpResponse(json.dumps(result), content_type="application/json")
                            else:
                                attrs_create.default = default
                        else:
                            # 如果没有default,默认值为第一个key对应的value
                            if 'value' in request.POST:
                                attrs_create.default = value_list[0]
                else:
                    result['status'] = ATTRS.ATTRS_NOTFOUND_TYPE
                    result['msg'] = '404 Not find the type'
                    return HttpResponse(json.dumps(result), content_type="application/json")

                attrs_create.save()
                result['id'] = attrs_create.id
                result['status'] = SUCCESS
                result['msg'] = 'done'
                return HttpResponse(json.dumps(result), content_type="application/json")
            except ValueError:
                logger.error (traceback.format_exc())
                result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_ATTR_TYPE_NOT_INT
                result['msg'] = 'type not int'
                return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NEED_TYPR
            result['msg'] = 'Need type in POST'
            return HttpResponse(json.dumps(result), content_type="application/json")

    def put(self, request):
        """
        属性修改功能
        可以修改属性的名称
        """
        result = {}
        user = request.user
        data = request.POST
        if 'id' in data:
            attrs_id = data['id']
            try:
                attrs = AttrsCreate.objects.get(id=attrs_id)
                # 属性名称修改
                if 'name' in data:
                    name = data['name']
                    if not check_name(name, result):
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    else:
                        attrs.name = name
                    attrs.save()
                result['status'] = SUCCESS
                result['msg'] = '已完成'
            except AttrsCreate.DoesNotExist:
                result['status'] = ATTRS.ATTRS_NOTFOUND
                result['msg'] = '404 Not found the id'
        else:
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NEED_ID
            result['msg'] = 'Need id in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self, request):
        """
        删除属性
        """
        result = {}
        user = request.user

        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST
        if 'id' in data:
            attrs_id = data['id']
            try:
                attrs = AttrsCreate.objects.get(id=attrs_id)
                logger.warning("user:{0} has deleted attrs(id:{1}, name:{2}".format(user.username, attrs.id, attrs.name))
                attrs.delete()
                result['status'] = SUCCESS
                result['msg'] = '已完成'
            except AttrsCreate.DoesNotExist:
                result['status'] = ATTRS.ATTRS_NOTFOUND
                result['msg'] = '404 Not found the id'
        elif 'ids' in data:
            attrs_ids = data['ids']

            try:
                attrs = AttrsCreate.objects.filter(id__in = attrs_ids)
                for attr in attrs:
                    logger.warning(
                        "user:{0} has deleted attrs(id:{1}, name:{2}".format(user.username, attr.id, attr.name))
                    attr.delete()
                result['status'] = SUCCESS
                result['msg'] = '删除已完成'
            except:
                pass
        else:
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NEED_ID
            result['msg'] = 'Need id or ids in POST'
            
        return HttpResponse(json.dumps(result), content_type="application/json")

class AttrsBindView(APIView):
    """
    属性绑定功能
    """
 
    def get(self, request):
        """
        查询
        """
        # 
        content = {}
        search_dict = {} 
        user = request.user
        # 返回权限
        content['auth'] = {
            "can_manage_attrsbind": user.has_role_perm('attrs.attrsbind.can_manage_attrsbind')  # 管理部门的权限
        }
        if "entity_type" in request.GET:
            entity_type = request.GET['entity_type']
            try:
                if 'entity_id' in request.GET :
                    entity_id = request.GET['entity_id']
                    entity_id = int(entity_id)
                    search_dict['entity_id'] = entity_id

                attrs_binds_list = [] 
                entity_type = int(entity_type) 
                search_dict['entity_type'] = entity_type
                # 查询结果转化为字典列表
                """
                value = AttrsBind.objects.filter(**search_dict).values('id')
                value_list = list(value)
                # 如果字典列表为空，说明entity_id，entity_type找不到对应的属性实体id
                if value_list == []:
                    content['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_ENTITY_NOT_FOUND
                    content['msg'] = 'entity_id or entity_type not found'
                # 取出字典列表中每个字典的id，并调用get_attrsbind_dict方法，拼接成字典列表返回
                for value_id in value_list:
                    bind_id = value_id['id']
                    attrs_bind = AttrsBind.objects.get(id=bind_id)
                    attrs_binds_list.append(get_attrsbind_dict(attrs_bind))
                """
                binds = AttrsBind.objects.filter(**search_dict) 
                # 取出字典列表中每个字典的id，并调用get_attrsbind_dict方法，拼接成字典列表返回
                for bind in binds: 
                    attrs_binds_list.append(get_attrsbind_dict(bind))
                content['status'] = SUCCESS
                content['msg'] = attrs_binds_list
            except ValueError:
                content['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_ENTITY_NOT_INT
                content['msg'] = 'entity_id or entity_type not int'
                return HttpResponse(json.dumps(content), content_type="application/json")
        elif 'id' in request.GET:
            bind_id = request.GET['id']
            try:
                bind_id = int(bind_id)
            except ValueError:
                content['status'] = ARGUMENT_ERROR_ID_NOT_INT
                content['msg'] = 'id not int'
                return HttpResponse(json.dumps(content), content_type="application/json")
            try:
                attrs_bind = AttrsBind.objects.get(id=bind_id)
                content['status'] = SUCCESS
                content['msg'] = get_attrsbind_dict(attrs_bind)
            except AttrsBind.DoesNotExist:
                content['status'] = ATTRS.ATTRS_NOTFOUND
                content['msg'] = '404 Not found the id'
        else:

            attrs_binds = AttrsBind.objects.all()
            attrs_binds_list = []
            for attrs_bind in attrs_binds:
                attrs_binds_list.append(get_attrsbind_dict(attrs_bind))
            content['status'] = SUCCESS
            content['msg'] = attrs_binds_list

        return HttpResponse(json.dumps(content), content_type="application/json")
 
    # 添加属性和实体类型的绑定
    def post(self, request):

        result = {}
        user = request.user
        # 验证是否有权限
        if not user.has_role_perm('attrs.attrsbind.can_manage_attrsbind'):
            return HttpResponse('Forbidden', status=403)

        # 新建
        if len(request.POST) == 0:
            request.POST = request.data
        if 'method' in request.POST:
            method = request.POST['method'].lower()
            if method == 'put':  # 修改
                return self.put(request)
            elif method == 'delete':  # 删除
                return self.delete(request)


        attrs_bind = AttrsBind()
        if 'attr_id' in request.POST:
            attr_id = request.POST['attr_id'].strip()
            try:
                attr = int(attr_id)
                try:
                    attr_bind = AttrsCreate.objects.get(id=attr)
                except AttrsCreate.DoesNotExist:
                    result['status'] = ATTRS.ATTRS_NOTFOUND
                    result['msg'] = 'Not find the id'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                attrs_bind.attr = attr_bind
            except ValueError:
                result['status'] = ARGUMENT_ERROR_ID_NOT_INT
                result['msg'] = 'id not int'
                return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NEED_ATTR_ID
            result['msg'] = 'Need attr id in POST'
            return HttpResponse(json.dumps(result), content_type="application/json")

        if 'entity_type' in request.POST:
            entity_type = request.POST['entity_type'].strip()
            if not check_entitytype(entity_type,attrs_bind,result):
                return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NEED_ENTITY_TYPR
            result['msg'] = 'Need entity type in POST'
            return HttpResponse(json.dumps(result), content_type="application/json")
        # 绑定的实体类别
        # 1 代表 任务实体 TASK
        # 2 代表 模板实体 WK_TEMPLATE
        # 3 代表 流程实体 RECORD
        # 4 代表 项目实体 PROJECT
        if 'entity_id' in request.POST:
            entity_id = request.POST['entity_id'].strip()
            try:
                entity_id = int(entity_id)
                attrs_bind.entity_id = entity_id
            except ValueError:
                result['status'] = ARGUMENT_ERROR_ID_NOT_INT
                result['msg'] = 'id not int'
                return HttpResponse(json.dumps(result), content_type="application/json")
        attrs_bind.save()
        result['id'] = attrs_bind.id
        result['status'] = SUCCESS
        result['msg'] = '已完成'
        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self, request):
        """
        删除属性
        """
        result = {}
        user = request.user
        data = request.POST
        if 'id' in data:
            bind_id = data['id']
            try:
                bind = AttrsBind.objects.get(id=bind_id)
                logger.warning("delete bind_id{0}, entity_type:{1}".format(bind.attr, bind.entity_type))
                bind.delete()
                result['status'] = SUCCESS
                result['msg'] = '已完成'
            except AttrsBind.DoesNotExist:
                result['status'] = ATTRS.ATTRS_NOTFOUND
                result['msg'] = '404 Not found the id'
        else:
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NEED_ID
            result['msg'] = 'Need id in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")

class AttrsInstancesView(APIView):
    """
    实体属性提供属性的增删改查功能
    """ 
    def get(self, request):
        """
        查询
        """
        # 
        content = {} 
        user = request.user
        if 'id' in request.GET:
            instance_id = request.GET['id']
            try:
                instance_id = int(instance_id)
            except ValueError:
                content['status'] = ARGUMENT_ERROR_ID_NOT_INT
                content['msg'] = 'id not int'
                return HttpResponse(json.dumps(content), content_type="application/json")

            try:
                attrs_instance = AttrsInstances.objects.get(id=instance_id)
                content['status'] = SUCCESS
                content['msg'] = get_attrsinstance_dict(attrs_instance)

            except AttrsInstances.DoesNotExist:
                content['status'] = ATTRS.ATTRS_NOTFOUND
                content['msg'] = '404 Not found the id'
            return HttpResponse(json.dumps(content), content_type="application/json")
        kwargs = {}
        if 'entity_type' in request.GET:
            entity_type = request.GET['entity_type']
            kwargs['entity_type'] = entity_type
        if 'entity_id' in request.GET:
            entity_id = request.GET['entity_id']
            kwargs['entity_id'] = entity_id
        attrs_instances = AttrsInstances.objects.filter(**kwargs)
        attrs_instances_list = []
        for attrs_instance in attrs_instances:
            attrs_instances_list.append(get_attrsinstance_dict(attrs_instance))
        content['status'] = SUCCESS
        content['msg'] = attrs_instances_list

        return HttpResponse(json.dumps(content), content_type="application/json")

    
    def post(self, request):
        """
        创建属性实体
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

        attrs_instances = AttrsInstances()
        # 通过entity_type和entity_id来确认实体表
        # 
        if 'entity_id' in request.POST:
            entity_id = request.POST['entity_id'].strip()
            try:
                entity_id = int(entity_id)
                attrs_instances.entity_id = entity_id

                if 'entity_type' in request.POST:
                    entity_type = request.POST['entity_type'].strip()
                    if not check_entitytype(entity_type,attrs_instances,result):
                        return HttpResponse(json.dumps(result), content_type="application/json")
            except ValueError:
                result['status'] = ARGUMENT_ERROR_ID_NOT_INT
                result['msg'] = 'id not int'
                return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NEED_ENTITY_ID
            result['msg'] = 'Need entity id in POST'
            return HttpResponse(json.dumps(result), content_type="application/json")

        # name是属性名称，不能自定义，只能使用已出创建的属性名称
        # type是属性类型
        # 同一类型的属性只能有一种属性名称，不同属性类型的属性名称可以重复
        # 通过属性类型来查询是否有填写的属性名称
        # 
        if 'attr_type' in request.POST:
            attr_type = request.POST['attr_type'].strip()
            try:
                attr_type = int(attr_type)
                try:
                    # names_list = []
                    # names = AttrsCreate.objects.filter(type=attr_type)
                    # 
                    names = AttrsCreate.objects.filter(type=attr_type).values('name')
                    # 将获取的查询集转为列表
                    names_list = list(names)
                    # 
                    if 'attr_name' in request.POST:
                        attr_name = request.POST['attr_name'].strip()
                        # 获取列表里字典的value
                        for item in names_list:
                            if item['name'] == attr_name:
                                # 如果能找到name，用tag=1来标识
                                # 如果找不到name，则没有标识
                                tag = 1
                        # 
                        try:
                            tag == 1
                            attrs_instances.attr_type = attr_type
                            attrs_instances.attr_name = attr_name
                        # 使用了不存在的tag，即表示name不存在
                        except UnboundLocalError:
                            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NAME_NOT_EXIST
                            result['msg'] = 'name is not exist'
                            return HttpResponse(json.dumps(result), content_type="application/json")
                    else:
                        result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NEED_ATTR_NAME
                        result['msg'] = 'Need attr_name in POST'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                except AttrsCreate.DoesNotExist:
                    result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_ATTR_TYPE_NOT_FIND
                    result['msg'] = 'attr_type not find'
                    return HttpResponse(json.dumps(result), content_type="application/json")
            except ValueError:
                result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_ATTR_TYPE_NOT_INT
                result['msg'] = 'attr_type not int'
                return HttpResponse(json.dumps(result), content_type="application/json")

            # 不同属性类型的属性值判断
            # 1 数字
            if attr_type == AttrsTypes.NUMBER:
                if 'attr_value' in request.POST:
                    attr_value = request.POST['attr_value'].strip()
                    if not check_number(attr_value, result):
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    else:
                        attrs_instances.attr_value = attr_value
                else:
                    result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NEED_ATTR_VALUE
                    result['msg'] = 'Need attr_value in POST'
                    return HttpResponse(json.dumps(result), content_type="application/json")
            # 2 字符
            elif attr_type == AttrsTypes.CHARACTER:
                if 'attr_value' in request.POST:
                    char = request.POST['attr_value'].strip()
                    if not check_char(char, result):
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    else:
                        attrs_instances.attr_value = char
                else:
                    result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NEED_ATTR_VALUE
                    result['msg'] = 'Need attr_value in POST'
                    return HttpResponse(json.dumps(result), content_type="application/json")
            # 3 日期
            elif attr_type == AttrsTypes.DATE:
                if 'attr_value' in request.POST:
                    attr_value = request.POST['attr_value'].strip()
                    try:
                        date = time.strptime(attr_value, settings.DATEFORMAT)
                        attrs_instances.attr_value = attr_value
                    except ValueError:
                        result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_DATE_FORMAT
                        result['msg'] = 'date time format is error.'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                else:
                    result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NEED_ATTR_VALUE
                    result['msg'] = 'Need attr_value in POST'
                    return HttpResponse(json.dumps(result), content_type="application/json")
            # 4 布尔
            elif attr_type == AttrsTypes.BOOLEAN:
                # 
                if 'attr_value' in request.POST:
                    attr_value = request.POST['attr_value'].strip()
                    if not check_bool(attr_value, result):
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    else:
                        attrs_instances.attr_value = attr_value
                else:
                    result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NEED_ATTR_VALUE
                    result['msg'] = 'Need attr_value in POST'
                    return HttpResponse(json.dumps(result), content_type="application/json")
            # 5 枚举
            elif attr_type == AttrsTypes.ENUMERATE:
                # 
                if 'attr_value' in request.POST:
                    attr_value = request.POST['attr_value'].strip()
                    try:
                        enum = json.loads(attr_value)
                        if not check_enum(enum, result):
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        else:
                            attrs_instances.attr_value = enum
                    except TypeError:
                        result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_TYPE_NOT_ENUMERATE
                        result['msg'] = 'type not enumerate'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                else:
                    result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NEED_ATTR_VALUE
                    result['msg'] = 'Need attr_value in POST'
                    return HttpResponse(json.dumps(result), content_type="application/json")
            attrs_instances.save()
            result['status'] = SUCCESS
            result['msg'] = '已完成'
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NEED_ATTR_TYPE
            result['msg'] = 'Need attr_type in POST'
            return HttpResponse(json.dumps(result), content_type="application/json")

    def put(self, request):
        """
        属性修改功能
        可以修改属性值，修改实体id，entity_id
        """
        result = {}
        user = request.user
        data = request.POST
        # 
        if 'id' in data:
            binds_id = data['id']
            # 
            try:
                instance = AttrsInstances.objects.get(id=binds_id)
                # 获取属性类型
                attr_type = instance.attr_type
                if attr_type == AttrsTypes.NUMBER:
                    if 'value' in data:
                        value = data['value']
                        if not check_number(value,result):
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        else:
                            instance.attr_value = value
                # 2 字符
                elif attr_type == AttrsTypes.CHARACTER:
                    if 'value' in request.POST:
                        char = data['value']
                        if not check_char(char,result):
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        else:
                            instance.attr_value = char

                # 3 日期
                elif attr_type == AttrsTypes.DATE:
                    if 'value' in request.POST:
                        value = data['value'].strip()
                        # 
                        try:
                            date = time.strptime(value, settings.DATEFORMAT)
                            instance.attr_value = date
                        except ValueError:
                            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_DATE_FORMAT
                            result['msg'] = 'date time format is error.'
                            return HttpResponse(json.dumps(result), content_type="application/json")
                # 4 布尔
                elif attr_type == AttrsTypes.BOOLEAN:
                    # 
                    if 'value' in request.POST:
                        value = data['value']
                        if not check_bool(value,result):
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        else:
                            instance.attr_value = value

                # 5 枚举
                elif attr_type == AttrsTypes.ENUMERATE:
                    if 'value' in request.POST:
                        value = data['value']
                        try:
                            enum = json.loads(value)
                            if not check_enum(enum,result):
                                return HttpResponse(json.dumps(result), content_type="application/json")
                            else:
                                instance.attr_value = enum
                        except TypeError:
                            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_TYPE_NOT_ENUMERATE
                            result['msg'] = 'type not enumerate'
                            return HttpResponse(json.dumps(result), content_type="application/json")
                instance.save()
                result['status'] = SUCCESS
                result['msg'] = '已完成'
                return HttpResponse(json.dumps(result), content_type="application/json")
            except AttrsCreate.DoesNotExist:
                result['status'] = ATTRS.ATTRS_NOTFOUND
                result['msg'] = '404 Not found the id'
        else:
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NEED_ID
            result['msg'] = 'Need id in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self, request):
        """
        删除功能
        """
        result = {}
        user = request.user
        data = request.POST
        if 'id' in data:
            instance_id = data['id']
            try:
                instance = AttrsInstances.objects.get(id=instance_id)
                logger.warning("delete attr_type:{0}, attr_name:{1}, attr_value:{2}, entity_id:{3}, entity_type:{4}".
                               format(instance.attr_type, instance.attr_name,
                                      instance.attr_value, instance.entity_id,
                                      instance.entity_type))
                instance.delete()
                result['status'] = SUCCESS
                result['msg'] = '已完成'
            except AttrsInstances.DoesNotExist:
                result['status'] = ATTRS.ATTRS_NOTFOUND
                result['msg'] = '404 Not found the id'
        else:
            result['status'] = ATTRS.ATTRS_ARGUMENT_ERROR_NEED_ID
            result['msg'] = 'Need id in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")


