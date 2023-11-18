import pdb

from django.http import HttpResponse

from rest_framework.views import APIView

from common.logutils import getLogger
import json

from oprecords.comm import OperateRec
from oprecords.models import opRecords
from property.code import *

logger = getLogger(True, 'oprecords', False)


class TestView(APIView):
    """
    测试View
    """
    
    def get(self, request):
        """
        查询
        """
        content = {}
        returnjson = False
        if 'json' in request.GET:
            returnjson = True
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
                aaa = OperateRec.create_record(6,2,'bbb','127.0.0.1:8000/oprecords/test/?id=1',user)
                content['status'] = SUCCESS

            except:
                content['status'] = 0
                content['msg'] = '404 Not found the id'
        return HttpResponse(json.dumps(content), content_type="application/json")

def get_opRecords_dict(operate_record):
    '''
        返回attrsinstance_dict的字典实例
        字典格式：
        {
            "id": operate_record.id,
            "entity_id": operate_record.entity_id,
            "entity_type": operate_record.entity_type,
            "content": operate_record.content,
            "url": operate_record.url,
            "creator": operate_record.creator
        }
        '''
    opRecords_dict = {
        "id": operate_record.id,
        "entity_id": operate_record.entity_id,
        "entity_type": operate_record.entity_type,
        "content": operate_record.content,
        "url": operate_record.url,
        "creator": operate_record.creator.id
    }
    return opRecords_dict

class opRecordsView(APIView):
    """
    操作记录查询功能
    """

    
    def get(self, request):
        """
        查询
        """
        content = {}
        returnjson = False

        if 'json' in request.GET:
            returnjson = True
        user = request.user
        if 'id' in request.GET:
            operate_id = request.GET['id']
            try:
                operate_id = int(operate_id)
            except ValueError:
                content['status'] = OPRECORDS.OPRECORDS_ERROR_ID_NOT_INT
                content['msg'] = 'id not int'
                return HttpResponse(json.dumps(content), content_type="application/json")

            try:
                operate_record = opRecords.objects.get(id=operate_id)
                content['status'] = SUCCESS
                content['msg'] = get_opRecords_dict(operate_record)

            except opRecords.DoesNotExist:
                content['status'] = OPRECORDS.OPRECORDS_RECORDS_NOTFOUND
                content['msg'] = '404 Not found the id'
        else:
            operate_records = opRecords.objects.all()
            operate_records_list = []
            for operate_record in operate_records:
                operate_records_list.append(get_opRecords_dict(operate_record))
            content['status'] = SUCCESS
            content['msg'] = operate_records_list

        return HttpResponse(json.dumps(content), content_type="application/json")
