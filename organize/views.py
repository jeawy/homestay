from django.contrib.auth.backends import RemoteUserBackend
from common.logutils import getLogger
import pdb
import json
import uuid  
from rest_framework.views import APIView 
from django.http import HttpResponse
from django.views import View
from property.code import ERROR, SUCCESS
from organize.comm import verify_data, get_organize_dict, get_organize_detail 
from organize.i18 import *
from organize.models import Organize
from django.conf import settings
from area.models import Area

logger = getLogger(True, 'organize', False)

class OrganizeAnonymousView(View):
    def get(self, request):
        # 匿名获取Organizes列表
        # 
        content={
            "status":SUCCESS,
            "msg" : []
        }
        kwargs = {}

        if 'uuid' in request.GET:
            # 获取详情
            organizeuuid = request.GET['uuid']
            try:
                organize = Organize.objects.get(uuid = organizeuuid)
                content['msg'] = get_organize_detail(organize)
            except Organize.DoesNotExist:
                content={
                            "status":ERROR,
                            "msg" : COMMUNITY_NOT_FOUND
                    }
            return HttpResponse(json.dumps(content), content_type="application/json") 
        if 'name' in request.GET:
            name = request.GET['name']
            kwargs['name__icontains'] = name
        if 'area' in request.GET:
            area = request.GET['area']
            kwargs['area__ID'] = area

        if "organizeuuid" in request.GET:
            # 按物业信息获得Organize记录(这个功能先放着)
            pass
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
        communities = Organize.objects.filter(**kwargs).order_by("-date")[page*pagenum : (page+1)*pagenum]
        content['msg'] = get_organize_dict(communities)
        return HttpResponse(json.dumps(content), content_type="application/json") 
    
      
class OrganizeView(APIView): 

    def get(self, request):
        # 获取Organizes列表
        # 
        content={
            "status":SUCCESS,
            "msg" : []
        }
        kwargs = {}
        
        if 'uuid' in request.GET:
            # 获取详情
            organizeuuid = request.GET['uuid']
            try:
                organize = Organize.objects.get(uuid = organizeuuid)
                content['msg'] = get_organize_detail(organize)
            except Organize.DoesNotExist:
                content={
                            "status":ERROR,
                            "msg" : COMMUNITY_NOT_FOUND
                    }
            return HttpResponse(json.dumps(content), content_type="application/json") 
        if 'name' in request.GET:
            name = request.GET['name']
            kwargs['name__icontains'] = name
        
        
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
        organizes = Organize.objects.filter(**kwargs)\
            .order_by("-date")[page*pagenum : (page+1)*pagenum]
        total =  Organize.objects.filter(**kwargs).count()
        content['msg'] = {
            "total" :total,
            "organizes":get_organize_dict(organizes)
            } 
        return HttpResponse(json.dumps(content), content_type="application/json") 
    

    def post(self, request):
        """
        新建物业：仅超级管理员可以
        
        """
        result = {
            'status': ERROR
        }
        user = request.user
        
        
        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST
         
        if 'method' in data:
            if not user.has_perms('organize.organize.manager_organize'):
                # 可以编辑，但必须有编辑权限
                result['msg'] = COMMUNITY_AUTH_ERROR
                return HttpResponse(json.dumps(result), content_type="application/json")
            method = data['method'].lower().strip()
            if method == 'put':  # 修改
                return self.put(request)
            if method == 'delete':  # 删除
                return self.delete(request)
        if not user.is_superuser:
            # 不是超级管理员，返回权限错误
            result['msg'] = COMMUNITY_AUTH_ERROR
            return HttpResponse(json.dumps(result), content_type="application/json")
        if 'name' in data :
            # 创建
            verify_result = verify_data(data)
            if verify_result[0] == ERROR:
                # 验证失败
                result['status'] = ERROR
                result['msg'] = verify_result[1]
                return HttpResponse(json.dumps(result), content_type="application/json")
            name = data['name'].strip()  
            

            try:
                Organize.objects.get(name = name)
                result['status'] = ERROR
                result['msg'] = "物业公司已存在"
                return HttpResponse(json.dumps(result), content_type="application/json")
            except Organize.DoesNotExist: 
                organize = Organize()
                organize.name = name
                
                organize.uuid = uuid.uuid4() 
                
                if 'alias' in data:
                    alias = data['alias'].strip() 
                    organize.alias = alias

                if 'code' in data:
                    code = data['code'].strip()
                    organize.code = code  

                if 'logo' in data:
                    logo = data['logo'].strip()
                    organize.logo = logo  
                if 'license' in data:
                    orglicense = data['license'].strip()
                    organize.license = orglicense 
                if 'managerid' in data:
                    managerid = data['managerid'].strip()
                    organize.manager__id = managerid 


                organize.save()
                result['status'] = SUCCESS
                result['msg'] = "创建成功"
                
                return HttpResponse(json.dumps(result), content_type="application/json")
        else: 
            result['status'] = ERROR
            result['msg'] = "确实name字段"
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
            organizeuuid = data['uuid'].strip()
            try:
                organize = Organize.objects.get(uuid = organizeuuid)
                 
                if 'name' in data:
                    name = data['name'].strip()
                    organize.name = name

                if 'alias' in data:
                    alias = data['alias'].strip() 
                    organize.alias = alias

                if 'code' in data:
                    code = data['code'].strip()
                    organize.code = code  

                if 'logo' in data:
                    # 问题：旧logo在系统中没有被删除
                    logo = data['logo'].strip()
                    organize.logo = logo  
                if 'license' in data:
                    orglicense = data['license'].strip()
                    organize.license = orglicense
  
                organize.save()
                result['status'] = SUCCESS
                result['msg'] = "修改成功" 
            except Organize.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = "未找到相关物业"
        else:
            result['msg'] = "缺少uuid"         
        return HttpResponse(json.dumps(result), content_type="application/json")
 
    def delete(self, request):
        """
        删除
        """
        result = {
            'status': ERROR,
            'msg': '暂时不支持删除'
        }
        data = request.POST
        if not request.user.is_superuser:
            # 仅仅超级管理员可以删
            result['msg'] = COMMUNITY_AUTH_ERROR
            return HttpResponse(json.dumps(result), content_type="application/json")
        if 'uuids' in data  :
            uuids = data['uuids']  
            Organize.objects.filter(uuid__in = uuids.split(",")).delete()  
            result['status'] = SUCCESS
            result['msg'] ='已删除'
        else: 
            result['msg'] ='Need uuids in POST'
        
        
        return HttpResponse(json.dumps(result), content_type="application/json")
        
