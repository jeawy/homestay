
from common.logutils import getLogger
import pdb
import json
import uuid
from datetime import datetime 
from django.db.models import Q  
from rest_framework.views import APIView 
from django.views import View 
from django.http import HttpResponse
from property.code import ERROR, SUCCESS
from record.excel import save_record_excel
from record.comm import get_userinfos, sortrecord , verify_fillup_data
from record.i18 import *
from record.models import Record, RecordUserInfo
from property.entity import EntityType
from notice.comm import NoticeMgr

logger = getLogger(True, 'recorduserinfo', False)

 
class RecordUserInfoAnonymousView(View):
     
    def get(self, request):
        """
        导出excel
        """
        # 返回excel的路径
        result = {
            'status':ERROR
        }
        if 'uuid' in request.GET:
            recorduuid = request.GET['uuid']
            try:
                record = Record.objects.get(uuid = recorduuid)
                sortrecord(record) # 导出excel的时候进行排序
                result['status'] = SUCCESS
                excel_result =  save_record_excel(record)
                if excel_result['status'] == SUCCESS:
                    result['status'] =  SUCCESS
                    result['msg'] = excel_result['path']
                else:
                    result['msg'] = excel_result['msg']
            except Record.DoesNotExist:
                result['msg'] = RECORD_NOT_FOUND

        return HttpResponse(json.dumps(result), content_type="application/json")
    
    def post(self, request):
        """
        匿名用户进行登记
        """
        result = {
            'status': ERROR
        }
        
        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST
          
        if 'uuid' in data and 'values' in data:
            # 进行登记 
            recorduuid = data['uuid'].strip()
            try:
                record = Record.objects.get(uuid = recorduuid, status = Record.PUBLISHED) 
                if record.limits and record.limits > 0 and RecordUserInfo.objects.filter(record=record).count() >= record.limits:
                    result['status'] = ERROR
                    result['msg'] = "登记人数已满" 
                    return HttpResponse(json.dumps(result), content_type="application/json")
                now = datetime.now() 
                if record.deadline and record.deadline < now:
                    record.status = record.TIMEOUT # 已超时
                    record.save()
                    result['status'] = ERROR
                    result['msg'] = RECORD_TIMEOUT
                else: 
                    values = data['values'].strip() 
                    v_result, values = verify_fillup_data(record, values)
                    if v_result:
                        # 数据验证通过
                        userinfo = RecordUserInfo()
                        userinfo.uuid = uuid.uuid4() 
                        userinfo.record = record
                        userinfo.values = values
                        userinfo.save() 
                        result['status'] = SUCCESS
                        result['msg'] = str(userinfo.uuid )
                        # 发通知
                        if record.notice == 1:# 开启通知
                            title = "新匿名登记"
                            content = "匿名用户在《{0}》进行了登记".format( record.title)
                            appurl = "/pages/record/detail?uuid="+str(record.uuid)
                            pcurl = "record-detail?uuid="+str(record.uuid)
                            entity_type = EntityType.RECORD
                            entity_uuid = record.uuid
                            NoticeMgr.create(
                                title = title,
                                content = content,
                                user = record.owner,
                                appurl = appurl,
                                pcurl = pcurl, 
                                entity_type = entity_type,
                                entity_uuid = entity_uuid
                            )
                    else:
                        # 填写的数据与表头不一致，没有填的数据也应该发空字符 
                        result['msg'] = RECORD_USERINFO_DATA_ERROR  
            except Record.DoesNotExist: 
                result['msg'] = RECORD_NOT_FOUND 
        else:  
            result['msg'] = RECORD_TITLE_ERROR
        return HttpResponse(json.dumps(result), content_type="application/json")
  
class RecordUserInfoView(APIView): 
    """
    登录用户进行登记
    """ 
    def get(self, request):
        """
        pc端获取用户登记情况
        """ 
        result = {
            'status':ERROR
        }
        if 'uuid' in request.GET and  'userlength' in request.GET:
            recorduuid = request.GET['uuid']
            userlength = int(request.GET['userlength'])
            kwargs = {}
            kwargs['record__uuid'] = recorduuid
            if 'keyword' in request.GET:
                keyword = request.GET['keyword'].strip()
                kwargs['values__icontains'] = keyword
            userinfos = RecordUserInfo.objects.filter( **kwargs ).order_by('id')[userlength:]
             
            result['status'] =  SUCCESS
            result['msg'] = get_userinfos(userinfos)
             
        return HttpResponse(json.dumps(result), content_type="application/json")
    

    def post(self, request):
        """
        进行登记
        任何用户都可以登记
        """
        result = {
            'status': ERROR
        }
        user = request.user 
        data = request.POST
         
        if 'method' in data:
            method = data['method'].lower().strip()
            if method == 'put':  # 修改
                return self.put(request)
            if method == 'delete':  # 删除
                return self.delete(request)
 
        if 'uuid' in data :
            # 进行登记 
            recorduuid = data['uuid'].strip()
            try:
                record = Record.objects.get(uuid = recorduuid, status = Record.PUBLISHED) 
                 
                if record.duplicate == 0 and RecordUserInfo.objects.filter(recorder = user, record=record).exists():
                    #  要求不能重复登记，因此需要验证是否进行了重复登记
                    #  已登记，无需再次登记
                    result['status'] = ERROR
                    result['msg'] = RECORD_DUPLICATED_USERINFO 
                elif record.limits and record.limits > 0 and RecordUserInfo.objects.filter(record=record).count() >= record.limits:
                    result['status'] = ERROR
                    result['msg'] = "登记人数已满" 
                else:
                    now = datetime.now()
                    if record.deadline and record.deadline < now:
                        record.status = record.TIMEOUT # 已超时
                        record.save()
                        result['status'] = ERROR
                        result['msg'] = RECORD_TIMEOUT
                    else:
                        values = data['values'].strip() 
                        v_result, values = verify_fillup_data(record, values)
                        if v_result:
                            # 数据验证通过
                            userinfo = RecordUserInfo()
                            userinfo.uuid = uuid.uuid4() 
                            userinfo.record = record
                            userinfo.recorder = user
                            userinfo.values = values
                            userinfo.save()
                            result['status'] = SUCCESS
                            result['msg'] = {
                                "uuid":str(userinfo.uuid ),
                                "values":values.split(",")
                            } 
                            # 发通知
                            if record.notice == 1:# 开启通知
                                title = "新登记"
                                content = "{0}在《{1}》进行了登记".format(user.username, record.title)
                                appurl = "/pages/record/detail?uuid="+str(record.uuid)
                                pcurl = "record-detail?uuid="+str(record.uuid)
                                entity_type = EntityType.RECORD
                                entity_uuid = record.uuid
                                NoticeMgr.create(
                                    title = title,
                                    content = content,
                                    user = record.owner,
                                    appurl = appurl,
                                    pcurl = pcurl, 
                                    entity_type = entity_type,
                                    entity_uuid = entity_uuid
                                )
                        else:
                            # 填写的数据与表头不一致，没有填的数据也应该发空字符 
                            result['msg'] = RECORD_USERINFO_DATA_ERROR 
            except Record.DoesNotExist: 
                result['msg'] = RECORD_NOT_FOUND 
        else:  
            result['msg'] = RECORD_UUID_ERROR
        return HttpResponse(json.dumps(result), content_type="application/json")
 
    def put(self, request):
        """
        登记发起人可以给登记记录打标记
        """
        result = {
            'status': ERROR,
            'msg': ''
        }
        # 处理前端发送数据
        data = request.POST 
      
        if 'record_info_uuid' in data:
            record_info_uuid = data['record_info_uuid'].strip()
            try:
                userinfo = RecordUserInfo.objects.get(uuid = record_info_uuid)
                record = userinfo.record

                if 'tags' in data:
                    tags = data['tags'].strip()
                    userinfo.tags = tags 
                
                if record.allow_modify == record.YES and 'values' in data:
                    # 允许本人修改登记记录 
                    values = data['values'].strip() 
                    v_result, values = verify_fillup_data(record, values)
                    if v_result:
                        # 数据验证通过  
                        userinfo.values = values
                        userinfo.save() 
                        # 发通知
                        if record.notice == 1:# 开启通知
                            title = "登记信息修改提醒"
                            content = "{0}在《{1}》修改了登记信息".format(userinfo.user.username, record.title)
                            appurl = "/pages/record/detail?uuid="+str(record.uuid)
                            pcurl = "record-detail?uuid="+str(record.uuid)
                            entity_type = EntityType.RECORD
                            entity_uuid = record.uuid
                            NoticeMgr.create(
                                title = title,
                                content = content,
                                user = record.owner,
                                appurl = appurl,
                                pcurl = pcurl, 
                                entity_type = entity_type,
                                entity_uuid = entity_uuid
                            )
                    else:
                        # 填写的数据与表头不一致，没有填的数据也应该发空字符 
                        result['msg'] = RECORD_USERINFO_DATA_ERROR
                        return HttpResponse(json.dumps(result), content_type="application/json") 

                userinfo.save()
                
                result['status'] = SUCCESS
                result['msg'] = RECORD_MODIFY_SUCCESS
            except RecordUserInfo.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = RECORD_PARAM_ERROR_NEED_UUID
                 
        return HttpResponse(json.dumps(result), content_type="application/json")
 
    def delete(self, request):
        """
        删除:仅可以删除自己的，或者管理员超级用户可以删除所有的
        发起人可以删除他发起的登记
        """
        content = {
            'status': ERROR,
            'msg': ''
        }
        # 处理前端发送数据
        data = request.POST 
        if 'uuids' in data:
            record_uuid_ids = data['uuids'].split(",")
            user = request.user
            if user.is_superuser: 
                # 超级管理员可以删除任何人的
                RecordUserInfo.objects.filter(uuid__in=record_uuid_ids).delete() 
            else:
                # 普通用户仅仅可以删除自己的 
                # 发起人删除 
                RecordUserInfo.objects.filter(Q(uuid__in=record_uuid_ids), 
                Q(record__owner = user, record__allow_delete=1)|Q(recorder= user)).delete()
            content['status'] = SUCCESS
            content['msg'] = RECORD_DELETE_SUCCESS 
        else:
            content['msg'] = RECORD_PARAM_ERROR_NEED_UUID
        
        return HttpResponse(json.dumps(content), content_type="application/json")
        
