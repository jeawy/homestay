#! -*- coding:utf-8 -*-
import json
import pdb
import os
import time
from datetime import datetime 
from django.http import HttpResponse
from django.conf import settings
from django.views import View 
from property.code import SUCCESS,  ERROR 
from building.models import Room, FeeRate
from community.models import Community 
from rest_framework.views import APIView
from common.logutils import getLogger
from community.comm import getUserCommunities
logger = getLogger(True, 'building_fee_rate', False)
from common.utils import get_season

def get_last_seasons():
    year, season, last_month = get_season() 
    start_year = year - 2
    seasons = [get_txt(start_year , season)]
    for i in range(1, 8): 
        season = season + 1
        start_year += int(season / 4 )  
        seasons.append(get_txt(start_year, season%4 ))
        if season > 3:
            season = 0

    return seasons

def get_txt(year, season):
    return str(year)+"年"+str(season+1)+"季度"

class RoomFeeRateView(APIView):
    """
    物业获得房屋的交费费率
    """ 
    def get(self, request):
        result = {
            "status": ERROR
        }
        user = request.user
        # 获取用户是哪些小区的员工
        communityuuids = getUserCommunities(user)
         
        if communityuuids is None:
             # 不是任何小区的员工，无法查看任何物业费账单
            result['msg'] = "非物业员工，无权查看"
            return HttpResponse(json.dumps(result), content_type="application/json") 
        seasons = get_last_seasons() 
        communities = Community.objects.filter(uuid__in = list(communityuuids))  
        communitiesls=[]
        communitynames = []
        for community in communities:
            community_dict = {}
            community_dict['name'] = community.name
            community_dict['type'] = 'line'
            community_dict['stack'] = 'Total'
            communitynames.append(community.name)
            community_dict['data'] = [None] * len(seasons)
            rates = list(FeeRate.objects.filter(community = community).values("rate", "season"))
            for rate in rates:
                try: 
                    index = seasons.index(rate['season']) 
                    community_dict['data'][index] = rate['rate'] 
                except ValueError:
                    pass
            communitiesls.append(community_dict)
        result['status'] = SUCCESS
        result['msg'] = { # 构成前端echarts所需的数据格式
            "series":communitiesls,
            "xAxis":seasons,
            "legend":communitynames
        }
        return HttpResponse(json.dumps(result), content_type='application/json')  
 

class RoomFeeRateCalView(View):
    """
    更新物业费缴费率
    """  
    def post(self, request): 
        result = {
            "status": ERROR
        } 
        communities = Community.objects.all()
        year, season, last_month = get_season()
        season = str(year)+"年"+str(season+1)+"季度"
        for community in communities:
            normal = Room.objects.filter(community = community, fee_status = Room.NORMAL ).count()
            total = Room.objects.filter(community = community  ).count()
            if total == 0:
                rate = None
            else:
                rate = round((normal / total ) * 100 ,2 )
            try:
                feerate = FeeRate.objects.get(community = community, season = season)
                feerate.rate = rate
                feerate.save()
            except FeeRate.DoesNotExist:
                FeeRate.objects.create(community = community, season = season, rate=rate )
           
        return HttpResponse(json.dumps(result), content_type="application/json")

 