from common.logutils import getLogger
import pdb
import json
import uuid  
import time
from community.models import Community
from rest_framework.views import APIView 
from django.http import HttpResponse
from django.views import View 
from property.code import ERROR, SUCCESS
from record.comm import verify_data, get_record_dict, get_record_detail, sortrecordThread
from record.i18 import *
from record.models import Record, RecordUserInfo
from django.conf import settings
from role.models import Cert
from mobile.detectmobilebrowsermiddleware import DetectMobileBrowser
dmb = DetectMobileBrowser()
logger = getLogger(True, 'record', False)

class RecordAnonymousView(View):
    def get(self, request):
        # 匿名获取records列表
        # 
        content={
            "status":SUCCESS,
            "msg" : []
        }
        kwargs = {}
        if 'uuid' in request.GET:
            # 获取详情
            recorduuid = request.GET['uuid']
            try:
                record = Record.objects.get(uuid = recorduuid) 
                content['msg'] = get_record_detail(record)
                
            except Record.DoesNotExist:
                content={
                            "status":ERROR,
                            "msg" : RECORD_NOT_FOUND
                    }
            return HttpResponse(json.dumps(content), content_type="application/json") 
        kwargs['status'] = Record.PUBLISHED
        if 'keyword' in request.GET:
            title = request.GET['keyword'].strip()
            if len(title) > 0:
                kwargs['title__icontains'] = title
        if 'status' in request.GET:
            status = request.GET['status']
            if int(status) != -1:
                kwargs['status'] = status
            
        kwargs['show_in_list'] = Record.YES # 只显示可以展示在小区列表中的登记簿
        if "communityuuid" in request.GET:
            # 按小区信息获得record记录(这个功能先放着)
            communityuuid = request.GET['communityuuid']
            kwargs['community__uuid'] = communityuuid

        if "page" in request.GET and "pagenum" in request.GET:
            # 分页
            pagenum = request.GET['pagenum']
            page = request.GET['page']
            try:
                page = int(page) - 1
                pagenum = int(pagenum)
            except ValueError:
                page = 0
                pagenum = settings.PAGE_NUM 
        else:
            page = 0
            pagenum = settings.PAGE_NUM
        records = Record.objects.filter(**kwargs).order_by("-date")[page*pagenum : (page+1)*pagenum]
        content['msg'] = get_record_dict(records)
        return HttpResponse(json.dumps(content), content_type="application/json") 
    
      
class RecordView(APIView): 
    def get(self, request):
        content = {
            'status': SUCCESS
        }
        user = request.user
        isMble = dmb.process_request(request)
        if isMble:
            print("mobile")
        else:
            print("pc")
        
        kwargs = {}
        if 'communityuuids' in request.GET :
            # pc 端首页用到
            communityuuids = request.GET['communityuuids'].strip()
            if ',' in communityuuids:
                communityuuids = communityuuids.split(",")
                kwargs['community__uuid__in'] = communityuuids
            else:
                kwargs['community__uuid'] = communityuuids
            kwargs['show_in_list'] = Record.YES
            kwargs['status'] = Record.PUBLISHED
        elif 'communityuuid' in request.GET:
            kwargs['owner'] = user
            communityuuid = request.GET['communityuuid']
            community = Community.objects.get(uuid = communityuuid)
            hasrole = Cert.objects.has_community_role(user = user, rolecode="wuye", community=community)
            print(hasrole)
         
        
        if 'uuid' in request.GET:
            # 获取登记的详细信息
            recorduuid = request.GET['uuid']
            onlyShowMine = False
            if 'onlyShowMine' in request.GET:
                onlyShowMine = request.GET['onlyShowMine']
                if onlyShowMine == "true":
                    onlyShowMine = True  
            try:
                record = Record.objects.get(uuid = recorduuid)
                if 'owner' in request.GET:
                    # 用户编辑时获详情，验证权限
                    if record.owner != user: 
                        content['msg'] = "无权限编辑"
                        content['status'] = ERROR
                        return HttpResponse(json.dumps(content), content_type="application/json")
                      
                content['msg'] = get_record_detail(record, user, onlyShowMine)
                content['status'] = SUCCESS
            except Record.DoesNotExist:
                content['status'] = ERROR
                content['msg'] = RECORD_NOT_FOUND
            return HttpResponse(json.dumps(content), content_type="application/json")
        mykwargs = { } # 我参与的
        if 'keyword' in request.GET:
            title = request.GET['keyword'].strip()
            if len(title) > 0:
                kwargs['title__icontains'] = title
                mykwargs['record__title__icontains'] = title
        
        if 'status' in request.GET:
            status = request.GET['status'].strip()
            if int(status) != -1: # -1 == 全部
                kwargs['status'] = status
                mykwargs['record__status'] = status
        
        if "page" in request.GET and "pagenum" in request.GET:
            # 分页
            pagenum = request.GET['pagenum']
            page = request.GET['page']
            try:
                page = int(page) - 1
                pagenum = int(pagenum)
            except ValueError:
                page = 0
                pagenum = settings.PAGE_NUM 
        else:
            page = 0
            pagenum = settings.PAGE_NUM 


        if 'mine' in request.GET:
            mine = request.GET['mine'].strip()
            if int(mine) == 0: # 0 == 我发起
                kwargs['owner'] = user
            elif int(mine) == 1: # 1 == 我参与
                # 我参与查询速度比较慢，采用values_list，
                # 返回少量数据，加快查询速度  
                mykwargs['recorder'] = user
                records = list(RecordUserInfo.objects.filter(**mykwargs).\
                    distinct('record__id').order_by("-record__id")\
                    [page*pagenum : (page+1)*pagenum].values(
                        "record__id","record__uuid", "record__title", "record__date", 
                        "record__content", 
                        "record__owner__username",
                        "record__status", 
                    )) 
                for record in records:
                    record['record__date'] = time.mktime(record['record__date'].timetuple())
                content['msg'] = records
                return HttpResponse(json.dumps(content), content_type="application/json")

        
        records = Record.objects.filter(**kwargs).\
            order_by("-date")[page*pagenum : (page+1)*pagenum]
          
        content['msg'] = get_record_dict(records)
        return HttpResponse(json.dumps(content), content_type="application/json")


    def post(self, request):
        """
        新建登记
        任何登录用户都可以发起登记
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
        community =  None 
        if 'communityuuid' in data:
            communityuuid = data['communityuuid']
            try:
                community = Community.objects.get(uuid = communityuuid)
            except Community.DoesNotExist:
                result['msg'] = "小区信息不存在"
                return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['msg'] = "请选择小区"
            return HttpResponse(json.dumps(result), content_type="application/json")
            
        if 'title' in data :
            # 创建
            verify_result = verify_data(data)
            if verify_result[0] == ERROR:
                # 验证失败
                result['status'] = ERROR
                result['msg'] = verify_result[1]
                return HttpResponse(json.dumps(result), content_type="application/json")

            record = Record()
            title = data['title'].strip() 
            record.owner = user
            record.title = title
            record.uuid = uuid.uuid4() 
            record.community = community # 绑定小区，查询用。
            
            if 'content' in data:
                content = data['content'].strip() 
                record.content = content
            if 'status' in data:
                status = data['status'].strip()
                record.status = status  
            if 'notice' in data:
                notice = data['notice'].strip()
                record.notice = notice 
            if 'duplicate' in data:
                duplicate = data['duplicate'].strip()
                record.duplicate = duplicate  
            
            if 'need_login' in data:
                need_login = data['need_login'].strip()
                record.need_login = need_login 
                  
            if 'only_owner_export' in data:
                only_owner_export = data['only_owner_export'].strip()
                record.only_owner_export = only_owner_export

            if 'show_in_list' in data:
                show_in_list = data['show_in_list'].strip()
                record.show_in_list = show_in_list  
                    
            if 'deadline' in data:
                deadline = data['deadline'].strip()  
                record.deadline = deadline
            if 'show_userinfo' in data:
                show_userinfo = data['show_userinfo'].strip()  
                record.show_userinfo = show_userinfo

            
            if 'autorecord' in data:
                autorecord = data['autorecord'].strip()  
                record.autorecord = autorecord
            
            if 'autotype' in data:
                autotype = data['autotype'].strip()  
                record.autotype = autotype
            
            if 'available_appside' in data:
                available_appside = data['available_appside'].strip()  
                record.available_appside = available_appside
            
            if 'autodays' in data:
                autodays = data['autodays'].strip()  
                record.autodays = autodays
            
            if 'limits' in data:
                limits = data['limits'].strip()  
                if limits:
                    record.limits = limits
            
            if 'allow_delete' in data:
                allow_delete = data['allow_delete'].strip()
                record.allow_delete = allow_delete 

            if 'allow_modify' in data:
                allow_modify = data['allow_modify'].strip()
                record.allow_modify = allow_modify 


            if 'extra' in data:
                extra = data['extra'].strip()  
                record.extra = extra
            
            
            
            record.save()
            result['status'] = SUCCESS
            result['msg'] = RECORD_ADD_SUCCESS
            result['uuid'] = str(record.uuid)
            return HttpResponse(json.dumps(result), content_type="application/json")
        else: 
            result['status'] = ERROR
            result['msg'] = RECORD_TITLE_ERROR
        return HttpResponse(json.dumps(result), content_type="application/json")
 
    def put(self, request):
        """
        编辑 
        """
        result = {
            'status': ERROR,
            'msg': ''
        }
        # 处理前端发送数据
        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST
        verify_result = verify_data(data)
        if verify_result[0] == ERROR:
            # 验证失败
            result['status'] = ERROR
            result['msg'] = verify_result[1]
            return HttpResponse(json.dumps(result), content_type="application/json")
 
        if 'uuid' in data:
            recorduuid = data['uuid'].strip()
            try:
                record = Record.objects.get(uuid = recorduuid)
                 
                if 'title' in data:
                    title = data['title'].strip()
                    record.title = title
                
                if 'content' in data:
                    content = data['content'].strip() 
                    record.content = content
                if 'status' in data:
                    status = data['status'].strip()
                    if int(status) == record.CANCEL and record.status == record.PUBLISHED:
                        # 原来正在登记，现在要结束登记，确认下是否需要进行排序
                        sortrecordThread(record)
                    record.status = status  

                if 'duplicate' in data:
                    duplicate = data['duplicate'].strip()
                    record.duplicate = duplicate  
                
                if 'need_login' in data:
                    need_login = data['need_login'].strip()
                    record.need_login = need_login  
                
                if 'notice' in data:
                    notice = data['notice'].strip()
                    record.notice = notice 
                
                if 'only_owner_export' in data:
                    only_owner_export = data['only_owner_export'].strip()
                    record.only_owner_export = only_owner_export
                    
                if 'deadline' in data:
                    deadline = data['deadline'].strip()  
                    if deadline: 
                        record.deadline = deadline
                if 'show_userinfo' in data:
                    show_userinfo = data['show_userinfo'].strip()  
                    record.show_userinfo = show_userinfo
                
                if 'autorecord' in data:
                    autorecord = data['autorecord'].strip()  
                    record.autorecord = autorecord
                
                if 'autotype' in data:
                    autotype = data['autotype'].strip()  
                    record.autotype = autotype
                
                if 'available_appside' in data:
                    available_appside = data['available_appside'].strip()  
                    record.available_appside = available_appside
                
                if 'show_in_list' in data:
                    show_in_list = data['show_in_list'].strip()
                    record.show_in_list = show_in_list 
                    
                if 'autodays' in data:
                    autodays = data['autodays'].strip()  
                    record.autodays = autodays
                
                if 'limits' in data:

                    limits = data['limits']
                    if limits:
                        record.limits = limits 
                
                if 'allow_delete' in data:
                    allow_delete = data['allow_delete'].strip()
                    record.allow_delete = allow_delete 

                if 'allow_modify' in data:
                    allow_modify = data['allow_modify'].strip()
                    record.allow_modify = allow_modify 
                    
                if 'extra' in data:
                    #修改时，如果已经有登记记录，
                    # 则要求修改之后的列数与修改之前的列数一致，
                    # 否则会忽略掉对列的修改
                    extra = data['extra'].strip()   
                    record.extra = extra
                     
                record.save()
                result['status'] = SUCCESS
                result['msg'] = RECORD_MODIFY_SUCCESS
                result['uuid'] = str(record.uuid)
            except Record.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = RECORD_PARAM_ERROR_NEED_UUID
                 
        return HttpResponse(json.dumps(result), content_type="application/json")
 
    def delete(self, request):
        """
        删除:仅可以删除自己的，或者管理员超级用户可以删除所有的
        """
        result = {
            'status': ERROR,
            'msg': ''
        }
        # 处理前端发送数据
        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST
 
        if 'uuids' in data:
            record_uuid_ids = data['uuids'].split(",")
            user = request.user
            if user.is_superuser: 
                Record.objects.filter(uuid__in=record_uuid_ids).delete() 
            else:
                # 普通用户仅仅可以删除自己的
                Record.objects.filter(uuid__in=record_uuid_ids, owner= user).delete() 
            result['status'] = SUCCESS
            result['msg'] = RECORD_DELETE_SUCCESS 
        else:
            result['msg'] = RECORD_PARAM_ERROR_NEED_UUID
        
        return HttpResponse(json.dumps(result), content_type="application/json")
        
