#! -*- coding:utf-8 -*-
import json, os
import pdb 
from django.http import HttpResponse
from django.conf import settings
from django.views import View
from property.code import * 
from area.models import Area 

def get_area_dict(areas):
    """
     
    """
    area_ls = []
    for area in areas:
        area_dict = {}
        area_dict['name'] = area.NAME
        area_dict['id'] = area.ID 
        area_dict['short_name'] = area.SHORT_NAME
        area_dict['longitude'] = area.LONGITUDE
        area_dict['latitude'] = area.LATITUDE
        area_dict['level'] = area.LEVEL
        area_ls.append(area_dict)

    
    return area_ls
 

class AreaView(View):
    
    
    def get(self, request):

        content = {"status":SUCCESS}
        if 'parentid' in request.GET:
            parentid = request.GET['parentid']
            areas = Area.objects.filter(PARENT_ID__ID =parentid )
            content['msg'] = get_area_dict(areas) 
        else: 
            areas = Area.objects.filter(LEVEL = 1 )
            content['msg'] = get_area_dict(areas)

        return HttpResponse(json.dumps(content), content_type="application/json")

  