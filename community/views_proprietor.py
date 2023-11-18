from django.contrib.auth.backends import RemoteUserBackend
from django.db import connections
from common.logutils import getLogger
import pdb
import json
import uuid  
from rest_framework.views import APIView 
from django.http import HttpResponse
from django.views import View
from common.utils import getStrFirstAplha 
from property.code import ERROR, SUCCESS
from django.db.models import Sum 
from community.i18 import *
from community.models import Community, Proprietor
from building.models import Room
from django.conf import settings 
from appuser.models import AdaptorUser as User  
logger = getLogger(True, 'community', False)

 
class CommunityProprietorView(APIView): 

    def get(self, request):
        # 获取我的关注列表
        # 
        content={
            "status":SUCCESS,
            "msg" : []
        }
        kwargs = {}
        user = request.user
        kwargs['user'] = user 
        if 'name' in request.GET:
            name = request.GET['name']
            kwargs['community__name__icontains'] = name
        
        communities = Proprietor.objects.filter(**kwargs)\
                .order_by("-community__name").values_list("community__uuid",
                "community__name")


        if 'sort' in request.GET:
            # 带字幕排序返回我的关注
            msg = []
            letters = []
            totalindex = 0 # 为了前端方便选中增加的字段
            for community in communities:
                firstletter = getStrFirstAplha(community[1]) 
                if firstletter not in letters:
                    letters.append(firstletter)
                    community_dict = {
                        "letter":firstletter,
                        "data":[[community[1], community[0], totalindex]]
                    }
                    msg.append(community_dict)
                else:
                    for msgitem in msg:
                        if msgitem['letter'] == firstletter:
                            msgitem['data'].append([community[1], community[0], totalindex])
                            break
                totalindex += 1
            
            content['msg'] = sorted(msg, key=lambda d:d['letter'])
        else:   
            content['msg'] =  list(communities)
        return HttpResponse(json.dumps(content), content_type="application/json") 
    

    def post(self, request):
        """
        新建添加关注 
        
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
            method = data['method'].lower().strip() 
            if method == 'delete':  # 删除
                return self.delete(request)
 
        if 'communityuuids' in data : 
            communityuuids = data['communityuuids'].split(",")
            for communityuuid in communityuuids:
                if len(communityuuid) < 10: # 不合法的uui
                    continue
                try:
                    community = Community.objects.get(uuid = communityuuid)
                    proprietor, created = Proprietor.objects.get_or_create(
                            community = community,
                            user = user
                        )

                    # 看一下该用户是否在业主信息表中，是的话，可以认证为业主
                    hasroom = Room.objects.filter(community=community).exists()
                    if hasroom:
                        proprietor.certificated = proprietor.YES
                        proprietor.save()
                    result['status'] = SUCCESS
                    result['msg'] = "已关注"
                except Community.DoesNotExist: 
                    result['msg'] = "未找到相关小区"  
                    return HttpResponse(json.dumps(result), content_type="application/json")
        else:  
            result['msg'] = "缺少community uuid"
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
        user = request.user
        if 'uuids' in data  :
            uuids = data['uuids'] 
            Proprietor.objects.filter(
                user = user,
                community__uuid__in = uuids.split(",")).delete()  
            result['status'] = SUCCESS
            result['msg'] ='已取消'
        else: 
            result['msg'] ='Need uuid prioryty POST'
        
        
        return HttpResponse(json.dumps(result), content_type="application/json")
        
