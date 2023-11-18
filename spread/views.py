#! -*- coding:utf-8 -*-
import json
import pdb
import os
import time
import requests 
from django.db.models import Q
from django.http import HttpResponse   
from datetime import datetime, date 
from community.models import Community
from rest_framework.views import APIView 
from common.fileupload import FileUpload 
from property.code import ERROR, SUCCESS 
from spread.models import Spread  
from django.views import View
from common.logutils import getLogger
logger = getLogger(True, 'spread', False)

def get_spread_dict(spread):
    spread_dict = {}
    spread_dict['id'] = spread.id
    spread_dict['title'] = spread.title
    spread_dict['content'] = spread.content
    spread_dict['date'] = time.mktime(spread.date.timetuple())
    spread_dict['image'] = spread.image
    spread_dict['url'] = spread.url
    spread_dict['status'] = spread.status
    if spread.community is None:
        spread_dict['communityname'] = "平台"
    else:
        spread_dict['communityname'] = spread.community.name
    return spread_dict

class SpreadView(View):
    """
    活动视图
    """ 
    def get(self, request): 
        content = {}
        content['status'] = SUCCESS 
        if 'app' in request.GET: 
            # 图片为空的不展示
            if 'communityuuid' in request.GET:
                communityuuid = request.GET['communityuuid']  
                spreads = Spread.objects.filter(Q(status = Spread.AVAILABLE), 
                Q(image__isnull = False), 
                Q( community__isnull = True ) | Q( community__uuid = communityuuid ))
            else:
                # 如果参数没有community uuid，则默认获取平台的活动
                spreads = Spread.objects.filter(
                    status = Spread.AVAILABLE , 
                    image__isnull = False,
                    community__isnull = True   
                )
            spreads_ls = []
            for spread in spreads: 
                spreads_ls.append(get_spread_dict(spread)) 
            
            content['msg'] = spreads_ls
         
        return HttpResponse(json.dumps(content), content_type="application/json")
    
    def post(self, request):
          
        if 'base64' in request.POST:
            logger.debug("i got u....")
            base64 = request.POST['base64']
            logger.debug("base64: " + base64)
        else:     
            logger.debug("base 64 missed")
        return HttpResponse(json.dumps({}), content_type="application/json")

class SpreadAuthView(APIView):
    """
    活动视图
    """  
    def get(self, request):
        # 获取 本小区发布的活动或者超级用户获取平台活动
        content = {}
        content['status'] = SUCCESS
        user = request.user
        if 'pc' in request.GET:
            communityuuid_ls = []
            if 'communityuuids' in request.GET:
                # pc 端获取活动接口, 图片为空的不展示
                communityuuids = request.GET['communityuuids'] 
                communityuuid_ls = communityuuids.split(",")
                if len(communityuuid_ls) > 0: 
                    spreads = Spread.objects.filter(Q(status = Spread.AVAILABLE), 
                    Q(image__isnull = False), 
                    Q( community__isnull = True ) | Q( community__uuid__in = communityuuid_ls ))
            elif 'communityuuid' in request.GET:
                # 物业管理员获取当前小区的活动进行管理
                communityuuid = request.GET['communityuuid']
                if user.is_superuser:
                    # 如果是超级管理员，则获取当前小区和全平台的。
                    spreads = Spread.objects.filter(  
                       Q( community__isnull = True ) | Q( community__uuid = communityuuid ))
                else:
                    spreads = Spread.objects.filter(  
                        community__uuid  = communityuuid )
            else:
                # 如果参数没有community uuid，则默认获取平台的活动
                spreads = Spread.objects.filter(
                    status = Spread.AVAILABLE , 
                    community__isnull = True   
                )
            spreads_ls = []
            for spread in spreads: 
                spreads_ls.append(get_spread_dict(spread)) 
            
            content['msg'] = spreads_ls
        elif 'auth' in request.GET and 'communityuuid' in request.GET: 
            communityuuid = request.GET['communityuuid'] 
            try:
                community = Community.objects.get(uuid = communityuuid)
                # 判断是否有权限
                perm = user.has_community_perm('spread.spread.addspread', community)
                content['msg'] =  perm
                return HttpResponse(json.dumps(content), content_type="application/json") 
            except Community.DoesNotExist:
                content['status'] = ERROR
                content['msg'] = '未找到对应小区信息' 
            
        return HttpResponse(json.dumps(content), content_type="application/json")

    def post(self, request):
        """
        权限: 1、物业可以在自己的小区范围内发布活动
              2、超级用户可以在全平台范围内发布活动
        """
        content = {
            "status":ERROR
        }
        user = request.user 
        superuser = user.is_superuser #  超级用户可以发布全平台的活动
        data = request.POST 
        community = None
        if 'communityuuid' in data and not superuser:
            communityuuid = data['communityuuid'] 
            try:
                community = Community.objects.get(uuid = communityuuid)
                # 判断是否有权限
                perm = user.has_community_perm('spread.spread.addspread', community)
                if not perm:
                    # 没有编辑权限，返回权限错误
                    content['msg'] = "没有权限发布活动"
                    return HttpResponse(json.dumps(content), content_type="application/json") 
            except Community.DoesNotExist:
                content['status'] = ERROR
                content['msg'] = '未找到对应小区信息'
                return HttpResponse(json.dumps(content), content_type="application/json")
    
        if 'method' in data:
            method = data['method'].strip().lower()
            if method == 'put':  # 修改
                return self.put(request)
            elif method == 'delete':
                return self.delete(request)
       
        if  'title' in data:
            title = data['title'].strip() 
            
            spread = Spread.objects.create(title = title)
            spread.community = community
            if 'content' in data:
                spread.content = data['content'].strip() 
            if 'url' in data:
                spread.url = data['url'].strip() 
            if 'image' in request.FILES: 
                image = request.FILES['image'] 
                FileUpload.upload(image, "spread", image.name)
                filepath = os.path.join("images", "spread", image.name)
                spread.image = filepath
            elif 'image' in data:
                image = data['image']
                spread.image = image
            if 'status' in data:
                status = int(data['status'].strip() )
                if status in spread.getstatus(): 
                   spread.status = status
                else:
                    content['status'] = ERROR
                    content['msg'] = 'status 状态错误，只能是0， 1， 2'
                    spread.delete()
                    return HttpResponse(json.dumps(content), content_type="application/json")
            spread.save()
            content['status'] = SUCCESS
            content['msg'] = '保存成功'
        else:
            content['status'] = ERROR
            content['msg'] = '参数错误，缺少title'
        return HttpResponse(json.dumps(content), content_type="application/json")

    def put(self, request):
        """
        记录轨迹：关闭轨迹记录
        """
        result = {}
        user = request.user
        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST 

        if 'id' in data :
            id = data['id']
        else:
            result['status'] = ERROR
            result['msg'] = '参数错误，缺少mapid'

        return HttpResponse(json.dumps(result), content_type="application/json")

    
    def delete(self, request):
        """
        删除
        """
        result = {}
        user = request.user
        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST 

        if 'ids' in data:
            ids = data['ids'].split(",")
            Spread.objects.filter( id__in = ids).delete() 
            result['status'] = SUCCESS
            result['msg'] = '已删除' 
        else:
            result['status'] = ERROR
            result['msg'] = '参数错误，缺少ids'

        return HttpResponse(json.dumps(result), content_type="application/json")
 