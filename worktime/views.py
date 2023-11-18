#! -*- coding:utf-8 -*-
import pdb
from datetime import datetime, timezone
import json
import xlrd

from django.http import HttpResponse
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden


from rest_framework.views import APIView
from xlrd import xldate_as_tuple
from common.fileupload import FileUpload

from excel.excel import readExcel_list, readExcel
from property import settings
from property.code import ERROR, SUCCESS
from worktime.models import WorkTime
from common.utils import format_all_dates


class HolidaysView(APIView):

    
    def get(self, request):
       
        user = request.user 

        result = {}
        fes_li = [] 
        result['auth'] = {
            # 节假日管理权限的权限
            "can_manage_wktime_state": user.has_role_perm('worktime.worktime.can_manage_wktime_state')
        }
        """
        if 'auth' in request.GET:
            # 获取当前用户是否有节假日管理权限
            result['auth'] = {
                "can_manage_wktime_state": auth
            }
        """
        sum = 0
        # 标志节假日或调休
        FESTIVAL = 0
        LEAVEOFF = 1
        leaveoff_li = []
        content = {}
        if 'start' in request.GET:
            if 'end' in request.GET:
                try:
                    start_date =request.GET['start'].strip()
                    end_date =request.GET['end'].strip()
                    start_date = datetime.strptime(start_date, settings.DATEFORMAT)
                    end_date = datetime.strptime(end_date, settings.DATEFORMAT)
                except ValueError:
                    result['status'] = ERROR
                    result['msg'] = '输入时间格式错误'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                if start_date < end_date:
                    # festival_sum = WorkTime.objects.filter(festivalday__gte = start_date, festivalday__lte = end_date, state=FESTIVAL).count()
                    festivals = WorkTime.objects.filter(festivalday__gte = start_date, festivalday__lte = end_date)
                    """
                    content['sum'] = festival_sum
                    content['leaveoff'] = leaveoff_li
                    result['stauts'] = SUCCESS
                    result['msg'] = content
                    """
                else:
                    result['status'] = ERROR
                    result['msg'] = '起始时间晚于结束时间'
                 
            else:
                result['status'] = ERROR
                result['msg'] = '请输入结束日期'
                return HttpResponse(json.dumps(result), content_type="application/json")
        else:  
            if 'year' in request.GET:
                year = request.GET['year'].strip()
                try:
                    year = int(year)
                except ValueError:
                    result['status'] = ERROR
                    result['msg'] = '请输入正确的年份'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                festivals = WorkTime.objects.filter(festivalday__year =  year )   
            else:
                festivals = WorkTime.objects.filter(state = FESTIVAL)

        for festival in festivals:
            fes_dic = {}
            fes_dic['name'] = festival.festivalname
            fes_dic['date'] = datetime.strptime(str(festival.festivalday), '%Y-%m-%d').timestamp()
            fes_li.append(fes_dic)
        result['msg'] = fes_li    
        result['stauts'] = SUCCESS     
        return HttpResponse(json.dumps(result), content_type="application/json")

    
    def post(self, request):
        """
        {"keys": [ "festivalname","festivalday"， “state”],
        "values": ["国庆节", "2019/10/01"，“”], ["国庆节", "2019/10/02"],["国庆节", "2019/10/02",  ],["", "2019/09/30", "调休“]
            }
        """
        user = request.user
        result = {}
        # 验证权限
        if not user.has_role_perm('worktime.worktime.can_manage_wktime_state'):
            return HttpResponse('Forbidden', status=403)
        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST

        if 'method' in data:
            method = request.POST['method'].lower().strip()
            if method == 'put':
                return self.put(request)
            if method == 'delete':
                return self.delete(request)
        """
        if 'file' in request.FILES:
            excel_file = request.FILES['file']
            if not excel_file.name.lower().endswith("xlsx"):
                result['status'] = ERROR
                result['msg'] = "仅仅支持xlsx文件格式"
            else:
                filename = excel_file.name
                filepath = FileUpload.upload(excel_file, 'tmp', filename)
                excel_list = readExcel_list(filepath)
                data_list = []
                success_num = 0
                n = 0
                for excel_item in excel_list:
                    n += 1
                    try:
                        festivalname = str(excel_item[0])
                        festivalday = xlrd.xldate.xldate_as_datetime((excel_item[1]), 0).__format__(settings.DATEFORMAT)
                        festivalday = datetime.strptime(festivalday, settings.DATEFORMAT)
                    except Exception:
                        continue

                    if check_festivalday_exist(festivalday):
                            data_list.append('第{0}条数据日期与已有节日重复'.format(n))
                            continue
                    else:
                        newfestival = WorkTime()
                        newfestival.festivalname = festivalname
                        newfestival.festivalday = festivalday
                        newfestival.save()
                        success_num += 1
                        data_list.append('第{0}条数据导入成功'.format(n))
                result['msg'] = data_list
            return HttpResponse(json.dumps(result), content_type="application/json")
        """
        # 失败数量
        failure_num = 0
         
        # 成功数量
        success_num = 0 
        worktime = data['worktime']
        worktime_values = worktime["values"]
        worktime_keys = worktime["keys"]
        for worktime_value in worktime_values:
            newfestival = WorkTime()
            
            try: 
                festivalday_index = worktime_keys.index('festivalday')
                festivalday = worktime_value[festivalday_index]
                festivalday = format_all_dates(festivalday) 
                if festivalday:
                    newfestival, created = WorkTime.objects.get_or_create(festivalday = festivalday)
                else:
                    # 日期格式错误
                    failure_num = failure_num + 1
                    continue 
            except ValueError:
                failure_num = failure_num + 1
                continue

            try: 
                festivalname_index = worktime_keys.index('festivalname')
                festivalname = worktime_value[festivalname_index]
                newfestival.festivalname = festivalname
            except ValueError:
                failure_num = failure_num + 1
                continue
            
            try: 
                state_index = worktime_keys.index('state') 
                state = worktime_value[state_index] 
                if  state:
                    if state.strip() == '调休':
                         newfestival.state = newfestival.LEAVEOFF
                         if newfestival.festivalname is None:
                             newfestival.festivalname = '调休'

            except ValueError:
                failure_num = failure_num + 1
                continue
            if newfestival.festivalname is not None:
                newfestival.save()
                success_num = success_num + 1
            else:
                failure_num = failure_num + 1
            
        result = {
            "status": SUCCESS,
            "msg": "导入完成",
            "success_num": success_num,
            "failure_num": failure_num
        }
        return HttpResponse(json.dumps(result), content_type="application/json")

       

def check_festivalday_exist(date):
    return WorkTime.objects.filter(festivalday = date).exists()

