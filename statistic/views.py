import json, os
import pdb
import operator
import pandas as pd
from appuser.models import AdaptorUser as User 
from datetime import datetime, timedelta
from django.views import View
from notice.comm import get_unread_notice_count 
from rest_framework.views import APIView
from django.http import HttpResponse
from content.models import   TxtContent
from product.models import Product
from property.code import SUCCESS,ERROR 
from aid.models import Aid
from community.comm import getUserCommunities
from prorepair.models import ProRepair
from paidservice.models import PaidOrder
from notice.models import Notice
from organize.comm import getUserOrganize


class StatisticAnonymousView(View):
    def get(self, request):
        """
        统计：最新社区见闻（30天内的）、
        积分好礼（30天内的）、
        邻里互助统计数据
        """
        result = {}   
        if 'communityuuid' in request.GET:
            now = datetime.now()
            communityuuid = request.GET['communityuuid']
            latestday = now + timedelta(days = -30)
            newscount = Product.objects.filter(
                date__gte = latestday,
                product_type = Product.NEWS,
                community__uuid = communityuuid
                ).count() # 最新社区见闻（30天内的）统计
            
            giftcount = Product.objects.filter(
                date__gte = latestday, 
                community__uuid = communityuuid
                ).count() # 最新积分好礼（30天内的）统计
            
            aidcount = Aid.objects.filter(
                date__gte = latestday, 
                community__uuid = communityuuid,
                status = Aid.OPEN
                ).count() # 邻里互助统计
            result['status'] = SUCCESS
            result['msg'] = {
                "newscount":newscount,
                "giftcount":giftcount,
                "aidcount":aidcount
            } 
        else:
            result['status'] = ERROR    
            result['msg'] = "缺少communityuuid"    

        return HttpResponse(json.dumps(result), content_type="application/json")



class StatisticView(APIView):
    """
    统计
    """
    def get(self, request):
        """
        查询
        """
        result = {} 
        # 统计“我的”页面角标数字
        user = request.user
        
        unread_notice_count = get_unread_notice_count(user) # 未读消息数
         
        result['msg'] = {
            "unread_notice_count":unread_notice_count 
        } 
         
        result['msg'][ "repaircount"] = 0
        result['msg'][ "paidservicecount"] = 0
        result['msg'][ "unreadcount"] = 0    
        result['status'] = SUCCESS
        return HttpResponse(json.dumps(result), content_type="application/json")
 