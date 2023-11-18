#! -*- coding:utf-8 -*-
import json
import pdb
import os  
import configparser
from django.views.decorators.csrf import csrf_exempt 
from django.http import HttpResponse, HttpResponseForbidden    
from appuser.models import AdaptorUser as User 
from django.utils import timezone 


from rest_framework.views import APIView 
from property import settings
from property.code import SUCCESS, ERROR 
from menu.models import Menu


class ConfigMenuView(APIView):
    
    
    def get(self, request):
 
        content = {}
        if 'menu_type' in request.GET:
            user = request.user
            menu_type = request.GET['menu_type']
            content['status'] = SUCCESS
            try:
                menu_instance = Menu.objects.get(user = user, menu_type=menu_type)
                content['msg'] = menu_instance.menu_list.split(',')
            except Menu.DoesNotExist:
                content['msg'] = [] 
        else:
            content['msg'] = '需要菜单类型menu_type'
            content['status'] = ERROR
         
        return HttpResponse(json.dumps(content), content_type="application/json") 


    
    def post(self, request):
        """
        修改系统配置
        """
        result = {} 
        user = request.user
        if 'menu_type' in request.POST and 'menu_list' in request.POST:
            user = request.user
            menu_type = request.POST['menu_type'] 
            menu_list = request.POST['menu_list'] 
            menu_instance, create = Menu.objects.get_or_create(user = user, 
                                        menu_type=menu_type)
            menu_instance.menu_list = menu_list
            menu_instance.save()
            result['status'] = SUCCESS
            result['msg'] ='已完成' 
        else:
            result['msg'] = '需要菜单类型menu_type和menu_list'
            result['status'] = ERROR   
        
        return HttpResponse(json.dumps(result), content_type="application/json")

 