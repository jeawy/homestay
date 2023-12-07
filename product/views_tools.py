#! -*- coding: utf-8 -*- 
import json
import os 
import pdb
import time 
import calendar
from datetime import datetime, timedelta
from rest_framework.views import APIView 
from django.views import View
from django.http import HttpResponse
from common.holiday import check_holiday, get_holidays
from property import settings 
from property.code import SUCCESS, ERROR 
from product.models import Product, Specifications 
 


class ToolsView(View): 
    def get(self, request):
        # 产品管理工具类 
        result = {"status": ERROR}
        
        if 'year' in request.GET and 'month' in request.GET:
            # 获取当前月份的日期，以及节假日信息
            """
            返回格式： 
                 [ 
                   {
                        "weekday" : 0, # 周日
                        "lastmonth":1, # 1 表示上个月的日期， 0 表示本月的日期
                        "day":1727625600, # 日期时间戳
                        "price":null, # 当前日期标注的价格
                        "holiday": "" #  是否是节假日，节假日会显示节假日名称，如国庆节
                   }, 
                   {
                        "weekday" : 1, # 周一
                        "lastmonth":1, # 1 表示上个月的日期， 0 表示本月的日期
                        "day":1727625600, # 日期时间戳
                        "price":null, # 当前日期标注的价格
                        "holiday": "" #  是否是节假日，节假日会显示节假日名称，如国庆节
                   }
               ] 
            """
            specs = []
            if 'productuuid' in  request.GET:
                # 查询民宿在某一天的价格
                productuuid = request.GET['productuuid'] 
                
                specs = Specifications.objects.filter(product__uuid = productuuid).\
                    values("id", "date", "price").order_by("date") 
                

            data = []
            year = request.GET['year'].strip()
            month = request.GET['month'].strip()
            startday = datetime.strptime(year+"/" +month + "/" + "01", settings.DATEFORMAT)
            
            firstweekday = startday.weekday() 
            holidays = get_holidays() # 获取节假日信息
             
            if firstweekday > 0:
                lastmonth = startday - timedelta(days = 1)  # 上个月最后一天 
                for i in range(firstweekday):
                    lastday = lastmonth - timedelta(days =  i)
                    lastday = lastday.date()
                    weekday = lastday.weekday()
                     
                    item = {
                        "weekday":lastday.weekday(),
                        "lastmonth" : 1, #上个月数据
                        "day" : time.mktime (lastday.timetuple()),
                        "price" : None
                    }
                    holiday = check_holiday(lastday, holidays) 
                    item['holiday'] = holiday
                    for spec in specs:  
                        if lastday == spec['date']: 
                            item['price'] = float(spec['price'])
                            item['id'] =  spec['id'] 
                            break

                    data.append(item)


            lastday = calendar.monthrange(int(year), int(month))[1]
            for i in range(lastday ):
                day = startday + timedelta(i)
                daydate = day.date()
                weekday = daydate.weekday()
                item = {
                    "weekday":daydate.weekday(),
                    "lastmonth" : 0, #本月数据
                    "day" : time.mktime(daydate.timetuple()),
                    "price" : None
                }
                holiday = check_holiday(daydate, holidays) 
                item['holiday'] = holiday
                for spec in specs: 
                    if daydate == spec['date']: 
                        item['price'] = float(spec['price'])
                        item['id'] =  spec['id'] 
                        break
                    
                data.append(item)
            data =  sorted(data, key=lambda d:d['day']) #dict(sorted(data.items()))  
            result['msg'] = data
            result['status'] = SUCCESS
        else:
            # 获取全部节假日
            holidays = get_holidays() # 获取节假日信息
            msg = []
            for holiday in holidays:
                
                for day in holiday['days']:
                    item = {
                        "holidayname" : holiday['holidayname'],
                        "day": time.mktime(day.timetuple())
                    }
                    msg.append(item)
            
            result['msg'] = msg
            result['status'] = SUCCESS

 
        return HttpResponse(json.dumps(result), content_type="application/json")

         