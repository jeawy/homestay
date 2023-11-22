from datetime import datetime, timedelta
import os 
from django.conf import settings
import pdb

def get_holidays( ):
    # 获取节假日
    """
    返回格式：
    [{'holidayname': '元旦', 'days': [datetime.date(2023, 12, 30)]}, 
    {'holidayname': '春节', 'days': [datetime.date(2024, 2, 10), datetime.date(2024, 2, 11)]} , 
    {'holidayname': '清明节', 'days': [datetime.date(2024, 4, 4), datetime.date(2024, 4, 5)]},
    {'holidayname': '劳动节', 'days': [datetime.date(2024, 5, 1), datetime.date(2024, 5, 2)},    
    {'holidayname': '端午节', 'days': [datetime.date(2024, 6, 8), datetime.date(2024, 6, 9)  ]},  
    """ 
    holidaypath = os.path.join(settings.BASE_DIR, "holiday.txt")
    result = []
    with open(holidaypath, encoding="utf-8") as holidayfile:
        holidays = holidayfile.readlines()
        for holiday in holidays:
            holiday = holiday.replace(" ", "")
            holiday = holiday.replace("\n", "")
            if holiday:
                holidayls = holiday.split("/")
                if len(holidayls) == 2:
                    
                    holidayname = holidayls[0]
                    resultitem = {
                        "holidayname" : holidayname
                    }
                    holidayls[1] = holidayls[1].replace("月", "/")
                    holidayls[1] = holidayls[1].replace("年", "/")
                    holidayls[1] = holidayls[1].replace("日", "")
                    holidayls[1] = holidayls[1].replace("号", "")
                    holidays = holidayls[1].split("-")
                    startday =   holidays[0]
                    endday =   holidays[1]
                     
                    startday = datetime.strptime(startday, "%Y/%m/%d").date()
                    endday = datetime.strptime(endday, "%Y/%m/%d").date() 
                    delta = endday - startday   # returns timedelta 
                    dayls = []
                    for i in range(delta.days + 1):
                        day = startday + timedelta(days=i)
                        dayls.append(day)
                    resultitem['days'] = dayls
                    result.append(resultitem)
               
    return result

def check_holiday(day, holidays):
    # 检查day是不是一个节日，如果是，返回节日名称，否则返回None
 
    for holiday in holidays: 
        if day in holiday['days']:
            return holiday['holidayname']
    
    return ""
