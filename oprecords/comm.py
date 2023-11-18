import pdb

from common.logutils import getLogger
from oprecords.models import opRecords
from property import settings
from property.code import *
from property.entity import EntityType

logger = getLogger(True, 'appfile', False)


class OperateRec(object):
    """
    操作记录管理
    """

    @classmethod
    def create_record(cls, entity_id, entity_type, content, url, creator):
        """
        新增操作记录
        entity_id: 实体id
        entity_type: 实体类别
        content: 内容
        url: url
        creator: 创建人
        返回result字典
        """
        result = {}
        oprecords = opRecords()

        # 内容
        oprecords.content = content
        try:
            # 实体id
            entity_id = int(entity_id)
            oprecords.entity_id = entity_id
            # 实体类别校验
            if not check_entitytype(entity_type, oprecords, result):
                return result
        except ValueError:
            result['status'] = OPRECORDS.OPRECORDS_ARGUMENT_ERROR_ENTITY_ID_NOT_INT
            result['msg'] = 'entity id not int'
            return result
        # url长度校验
        if not check_url(url, result):
            return result
        else:
            oprecords.url = url

        oprecords.creator = creator
        oprecords.save()
        result['id'] = oprecords.id
        result['status'] = SUCCESS
        result['msg'] = '已完成'
        return result

# 实体类别验证
def check_entitytype(entity_type,oprecords,result):
    entity_list = EntityType.get_entities()
    try:
        entity_type = int(entity_type)
        # 判断添加的实体类别是否存在
        if entity_type in entity_list:
            # 属性实体不需要判断entity_id
            # 只需要判断entity_type存不存在
            oprecords.entity_type = entity_type
            return True
        else:
            result['status'] = OPRECORDS.OPRECORDS_ARGUMENT_ERROR_ENTITY_TYPE_NOT_FOUND
            result['msg'] = 'entity_type not found'
            return False
    except ValueError:
        result['status'] = OPRECORDS.OPRECORDS_ARGUMENT_ERROR_ENTITY_TYPE_NOT_INT
        result['msg'] = 'entity_type not int'
        return False

# url长度校验
def check_url(url,result):
    if len(url) > 1024:
        result['status'] = OPRECORDS.OPRECORDS_ARGUMENT_ERROR_URL_TOO_LONG
        result['msg'] = 'url too long.'
        return False
    elif len(url) == 0:
        result['status'] = OPRECORDS.OPRECORDS_ARGUMENT_ERROR_URL_EMPTY
        result['msg'] = 'url is empty.'
        return False
    else:
        return True
