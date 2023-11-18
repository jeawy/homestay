#! -*- coding:utf-8 -*-
import time

from datetime import datetime

from property import settings


def timeStamp(date):
    ''' 将datetime转换为时间戳'''
    if(date is not None):
        #将date转字符串
        timeChar = date.strftime(settings.DATEFORMAT)
        #将字符串转时间数组
        timeArray = time.strptime(timeChar, settings.DATEFORMAT)
        #将时间数组转时间戳
        timeStamp = int(time.mktime(timeArray))
        #返回时间戳
        return timeStamp
    else:
        return None

def datetimeStamp(date):
    ''' 将datetime转换为时间戳'''
    if(date is not None):
        #将date转字符串
        timeChar = date.strftime(settings.DATETIMEFORMAT)
        #将字符串转时间数组
        timeArray = time.strptime(timeChar, settings.DATETIMEFORMAT)
        #将时间数组转时间戳
        timeStamp = int(time.mktime(timeArray))
        #返回时间戳
        return timeStamp
    else:
        return None