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
from property.code import SUCCESS, ERROR, CLIENT, SYSSECTION,\
            CLIENTSERVER, SERVERHOST, SERVERPORT, OUTSOURCING, TRAINING_WORKTIME,\
            OFFICIAL_WORKTIME_ON, OFFICIAL_WORKTIME_OFF, OFFICIAL_WORKTIME_LONG,\
                TRAINING_RANGE, ATTENDANCE, SCORE, RANGE, SUBMIT_TIME,\
                  TRAINING_WORKTIME_ON,   TRAINING_WORKTIME_OFF, TRAINING_WORKTIME_LONG,\
                      OFFICIAL_WORKTIME


class SysConfigView(APIView):
    
    
    def get(self, request):

    
        config = configparser.ConfigParser()
        config.read(settings.SYSCONFIG_PATH)
        content = {}
        try:
            client = config.get(SYSSECTION, CLIENT)
        except configparser.NoOptionError:
            client = None
        except configparser.NoSectionError:
            client = None

        try: # 
            outsourcing = config.get(SYSSECTION, OUTSOURCING)
        except configparser.NoOptionError:
            outsourcing = None
        except configparser.NoSectionError:
            outsourcing = None

        try: # 
            training_work_on = config.get(TRAINING_WORKTIME, TRAINING_WORKTIME_ON)
        except configparser.NoOptionError:
            training_work_on = None
        except configparser.NoSectionError:
            training_work_on = None

        try: # 
            training_work_off = config.get(TRAINING_WORKTIME, TRAINING_WORKTIME_OFF)
        except configparser.NoOptionError:
            training_work_off = None
        except configparser.NoSectionError:
            training_work_off = None

        try: # 
            training_work_long = config.get(TRAINING_WORKTIME, TRAINING_WORKTIME_LONG)
        except configparser.NoOptionError:
            training_work_long = None
        except configparser.NoSectionError:
            training_work_long = None
        

        try: # 
            official_work_on = config.get(OFFICIAL_WORKTIME, OFFICIAL_WORKTIME_ON)
        except configparser.NoOptionError:
            official_work_on = None
        except configparser.NoSectionError:
            official_work_on = None

        try: # 
            official_work_off = config.get(OFFICIAL_WORKTIME, OFFICIAL_WORKTIME_OFF)
        except configparser.NoOptionError:
            official_work_off = None
        except configparser.NoSectionError:
            official_work_off = None

        try: # 
            official_work_long = config.get(OFFICIAL_WORKTIME, OFFICIAL_WORKTIME_LONG)
        except configparser.NoOptionError:
            official_work_long = None
        except configparser.NoSectionError:
            official_work_long = None
        
        content['client'] = client
        content['outsourcing'] = outsourcing
        content['training'] = {
            "training_work_on" : training_work_on,
            "training_work_off" : training_work_off,
            "training_work_long" : training_work_long
        }
        content['official'] = {
            "official_work_on" : official_work_on,
            "official_work_off" : official_work_off,
            "official_work_long" : official_work_long
        }
        return HttpResponse(json.dumps(content), content_type="application/json") 


    
    def post(self, request):
        """
        修改系统配置
        """
        result = {} 
        user = request.user
        # 只有超级管理员才可以修改系统配置
        if not user.has_role_perm('appuser.baseuser.super_user'):
            return HttpResponse('Forbidden', status=403)
        
        config = configparser.RawConfigParser()
        config.read(settings.SYSCONFIG_PATH)
        if request.POST: 
            data = request.POST
        else:
            data = request.data 
        
        if CLIENT in data  :
            dept = data[CLIENT]
            # 绑定客户部门
            if not config.has_section(SYSSECTION):
                config.add_section(SYSSECTION)
            config.set(SYSSECTION, CLIENT, dept)
        
        if OUTSOURCING in data  :
            outsourcing = data[OUTSOURCING]
            # 绑定外包部门
            if not config.has_section(SYSSECTION):
                config.add_section(SYSSECTION)
            config.set(SYSSECTION, OUTSOURCING, outsourcing)
    
        if TRAINING_WORKTIME in data  :
            # 实训成员的上下班、工时计算配置 
            if not config.has_section(TRAINING_WORKTIME):
                config.add_section(TRAINING_WORKTIME)
            if TRAINING_WORKTIME_ON in data:
                training_worktime_on = data[TRAINING_WORKTIME_ON]
                config.set(TRAINING_WORKTIME, TRAINING_WORKTIME_ON, training_worktime_on)
            if TRAINING_WORKTIME_OFF in data:
                training_worktime_off = data[TRAINING_WORKTIME_OFF]
                config.set(TRAINING_WORKTIME, TRAINING_WORKTIME_OFF, training_worktime_off)
            if TRAINING_WORKTIME_LONG in data:
                training_worktime_long = data[TRAINING_WORKTIME_LONG]
                config.set(TRAINING_WORKTIME, TRAINING_WORKTIME_LONG, training_worktime_long)
        
        if OFFICIAL_WORKTIME in data  :
            # 正式成员的上下班、工时计算配置 
            if not config.has_section(OFFICIAL_WORKTIME):
                config.add_section(OFFICIAL_WORKTIME)
            if OFFICIAL_WORKTIME_ON in data:
                official_worktime_on = data[OFFICIAL_WORKTIME_ON]
                config.set(OFFICIAL_WORKTIME, OFFICIAL_WORKTIME_ON, official_worktime_on)
            if OFFICIAL_WORKTIME_OFF in data:
                official_worktime_off = data[OFFICIAL_WORKTIME_OFF]
                config.set(OFFICIAL_WORKTIME, OFFICIAL_WORKTIME_OFF, official_worktime_off)
            if OFFICIAL_WORKTIME_LONG in data:
                official_worktime_long = data[OFFICIAL_WORKTIME_LONG]
                config.set(OFFICIAL_WORKTIME, OFFICIAL_WORKTIME_LONG, official_worktime_long)
        
        if TRAINING_RANGE in data :
            # 实训排名计算权重 
            if not config.has_section(TRAINING_RANGE):
                config.add_section(TRAINING_RANGE)
            if ATTENDANCE in data:
                attendance = data[ATTENDANCE]
                config.set(TRAINING_RANGE, ATTENDANCE, attendance)
            if SCORE in data:
                score = data[SCORE]
                config.set(TRAINING_RANGE, SCORE, score)
            if RANGE in data:
                total_range = data[RANGE]
                config.set(TRAINING_RANGE, RANGE, total_range)
            if SUBMIT_TIME in data:
                submit_time = data[SUBMIT_TIME]
                config.set(TRAINING_RANGE, SUBMIT_TIME, submit_time)

        with open(settings.SYSCONFIG_PATH, 'w') as configfile:
            config.write(configfile)
       
        result['status'] = SUCCESS
        result['msg'] ='已完成'
        
        return HttpResponse(json.dumps(result), content_type="application/json")


class ExtranetBindView(APIView):
    """
    外网ip和端口的配置管理
    """

    
    def get(self, request):
        config = configparser.ConfigParser()
        config.read(settings.SYSCONFIG_PATH)
        content = {}
        try:
            serverhost = config.get(CLIENTSERVER, SERVERHOST)
        except configparser.NoOptionError:
            serverhost = None
        except configparser.NoSectionError:
            serverhost = None
        
        try:
            serverport = config.get(CLIENTSERVER, SERVERPORT)
        except configparser.NoOptionError:
            serverport = None
        except configparser.NoSectionError:
            serverport = None
        
        content['host'] = serverhost
        content['port'] = serverport
        return HttpResponse(json.dumps(content), content_type="application/json")

    
    def post(self, request):
        """
        修改系统配置
        """
        result = {}
        user = request.user
        # 只有超级管理员才可以修改系统配置
        if not user.has_role_perm('appuser.baseuser.super_user'):
            return HttpResponse('Forbidden', status=403)

        config = configparser.RawConfigParser()
        config.read(settings.SYSCONFIG_PATH)
        if request.POST:
            data = request.POST
        else:
            data = request.data

        # 修改外网ip配置
        if SERVERHOST in data:
            server = data[SERVERHOST]
            if not config.has_section(CLIENTSERVER):
                config.add_section(CLIENTSERVER)
            config.set(CLIENTSERVER, SERVERHOST, server)

        # 修改端口配置
        if SERVERPORT in data:
            port = data[SERVERPORT]
            if not config.has_section(CLIENTSERVER):
                config.add_section(CLIENTSERVER)
            config.set(CLIENTSERVER, SERVERPORT, port)
        
       
        with open(settings.SYSCONFIG_PATH, 'w') as configfile:
            config.write(configfile)

        result['status'] = SUCCESS
        result['msg'] = '已完成'

        return HttpResponse(json.dumps(result), content_type="application/json")

 