#-*- encoding:utf-8 -*-
import json
import os
import pdb
from datetime import datetime
from django.utils import timezone
from excel.imageparsing import compenent
from property.settings import FILEPATH
import xlrd
from django.conf import settings


def readExcel(excel_path):
    """
    将excel中的数据解析为json串
    excel_path: 文件路径
    """
    # 打开Excel文件读取数据
    excel = xlrd.open_workbook(excel_path)

    # 得到第一张表单
    sheet1 = excel.sheets()[0]
    # 获得行数和列数
    nrows = sheet1.nrows #行数
    ncols = sheet1.ncols #列数

    # 创建一个数组用来存储excel中的数据
    totalArray=[]
    # 标题
    title=[]

    # 取出标题
    for i in range(0,ncols):
        title.append(sheet1.cell(0,i).value)
    # 
    for rowindex in range(1,nrows):
        dic={}
        for colindex in range(0,ncols):
            # 
            # 获取表格的值
            valuetype = str(sheet1.cell(rowindex,colindex))
            value = sheet1.cell(rowindex,colindex).value 
            if 'xldate' in valuetype:
                # 日期格式
                value = xlrd.xldate_as_datetime(value, 0).strftime(settings.DATETIMEFORMAT)
             
            """
            if colindex == 2:
                
                s = os.path.join(BASE_DIR, 'excel_image')
            """
             
            dic[title[colindex]]= str(value  )
        totalArray.append(dic)
    compenent(excel_path, os.path.join(FILEPATH, 'excel'))
    print(totalArray)
      
    return json.dumps(totalArray,ensure_ascii=False)



def readExcel_list(excel_path):
    """
    将excel中的数据解析为json串
    excel_path: 文件路径
    与readExcel不同的是，这个函数返回的是list of list 而不是dict of list
    返回list列表
    """
    # 打开Excel文件读取数据
    excel = xlrd.open_workbook(excel_path)

    # 得到第一张表单
    sheet1 = excel.sheets()[0]
    # 获得行数和列数
    nrows = sheet1.nrows #行数
    ncols = sheet1.ncols #列数

    # 创建一个数组用来存储excel中的数据
    totalArray=[]
    # 标题
    title=[]

    # 取出标题
    for i in range(0,ncols):
        title.append(sheet1.cell(0,i).value)
    # 
    for rowindex in range(0, nrows):
        dic= []
        for colindex in range(0,ncols):
            # 
            # 获取表格的值 
            valuetype = str(sheet1.cell(rowindex,colindex))
            value = sheet1.cell(rowindex,colindex).value 
            if 'xldate' in valuetype:
                # 日期格式
                value = xlrd.xldate_as_datetime(value, 0).strftime(settings.DATETIMEFORMAT)
              
            dic.append(value)
        totalArray.append(dic)

    return totalArray
