#! -*- coding:utf-8 -*-
import json, os
import pdb
import uuid
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime 
from django.http import HttpResponse, HttpResponseForbidden 
from django.utils.translation import ugettext as _ 
from appuser.models import AdaptorUser as User 
from common.request import Code
from django import forms
from django.utils import timezone
from django.shortcuts import redirect 


from django.conf import settings
from rest_framework.views import APIView

from property.code import *
from appfile.comm import AppFileMgr
from appfile.models import Attachment
from common.logutils import getLogger
logger = getLogger(True, 'dept', False)

def get_dept_dict(dept):
    """
    返回deptment的字典实例
    字典格式：
     {
                    "name":dept.name,
                    "level":dept.level,
                    "charger_name":charger_name,
                    "charger_id": charger_id,
                    "top_dept_name":top_dept_name,}
                    "top_dept_id":top_dept_id
                    }
    """
    charger_name = ""
    charger_id = ""
    if dept.charger:

        charger_name = dept.charger.username
        charger_id = dept.charger.id
    top_dept_name = ""
    top_dept_id = ""
    if dept.parent:
        top_dept_name = dept.parent.name
        top_dept_id = dept.parent.id
    dept_dict = {
                    "id":dept.id,
                    "name":dept.name,
                    "level":dept.level,
                    "charger_name":charger_name,
                    "charger_id": charger_id,
                    "top_dept_name":top_dept_name ,
                    "top_dept_id":top_dept_id
    } 
    return dept_dict
 
 
class AppfileView(APIView): 
    def get(self, request):

        content = {}
        returnjson = False

        if 'json' in request.GET:
            returnjson = True
        user = request.user

        if 'id' in request.GET:
            dept_id = request.GET['id']
            try:
                dept_id = int(dept_id)
            except ValueError:
                content['status'] = ARGUMENT_ERROR_ID_NOT_INT
                content['msg'] = 'id not int'
                return HttpResponse(json.dumps(content), content_type="application/json")

            try:
                dept = Dept.objects.get(id=dept_id)
                content['status'] = SUCCESS
                content['msg'] = get_dept_dict(dept)
                 
            except Dept.DoesNotExist:
                content['status'] = DEPT_NOTFOUND
                content['msg'] = '404 Not found the id'
        else:
             depts = Dept.objects.all()
             depts_list = []
             for dept in depts:
                 depts_list.append(get_dept_dict(dept))
             content['msg'] = depts_list
             content['status'] = SUCCESS

        return HttpResponse(json.dumps(content), content_type="application/json")

 
    def post(self, request):
        """
        新建
        """
        result = {}  
        # 新建  
        fileobj = request.data['file'] 
        filepath = settings.APPFILEPATH

        # 获取当前时间戳与文件名称进行拼接作为唯一标识
        timestamp = str(datetime.now().timestamp())
        
        file_name, file_extension = os.path.splitext(fileobj.name)
        filename = timestamp + str(uuid.uuid4())+file_extension
        
        apptype = Attachment.TEMP
        appid = 1
        file_result = AppFileMgr.upload(fileobj, filepath, filename, apptype, appid )
        result['status'] = SUCCESS
        result['msg'] = os.path.join(settings.IMAGEROOTPATH, 'appfile', filename)
        result['id'] = file_result['msg']
        return HttpResponse(json.dumps(result), content_type="application/json")
 