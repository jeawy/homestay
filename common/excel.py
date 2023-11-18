import pdb
import os
import traceback 
import json
import datetime
import xlwt
import xlsxwriter
from property.code import  SUCCESS, ERROR 
from excel.imageparsing import compenent
from django.conf import settings 
import time 
from PIL import Image
from common.logutils import getLogger 
logger = getLogger(True, 'excel', False)
 
 
def save_excel(excel_heads,keys,all_msg,data=None):
    """ 
    参数 excel_heads 表头汉字
         keys 键
         all_msg 值
    :return:
    """
    content = {}
    # 按照设置的类型解析为字符串
    datestr = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    # 设置文件的名称 按照项目名称加时间
    suffix = ".xls"
    filename = datestr + suffix
    basedir = BASE_DIR
    relpath = os.path.join('images', 'output', filename)
    if not os.path.isdir(os.path.join(basedir, 'images', 'output')):
        os.makedirs(os.path.join(basedir, 'images', 'output'))
    abspath = os.path.join(basedir, relpath)
    # 创建一个Workbook对象，这就相当于创建了一个Excel文件
    book = xlsxwriter.Workbook(abspath)
    # # 其中的test是这张表的名字,cell_overwrite_ok，表示是否可以覆盖单元格，其实是Worksheet实例化的一个参数，默认值是False
    sheet = book.add_worksheet()

    # 通过字典设置格式
    workfomat = book.add_format({
        'border': 1,  # 单元格边框宽度
        'align': 'center',  # 对齐方式
        'valign': 'vcenter',  # 字体对齐方式
        'top': 1,  # 顶边
        'left': 1,  # 左边
        'right': 1,  # 右边
        'bottom': 1,  # 底边
        'text_wrap': 1  # 自动换行
    })
    # 大标题
    titlefomat = book.add_format({
        'bg_color': '#BBBBBB',  # 单元格背景颜色
        'bold': True,  # 字体加粗
        'border': 1,  # 单元格边框宽度
        'align': 'center',
        'font_size':18,
        'valign': 'vcenter',  # 字体对齐方式
        'text_wrap': True,  # 是否自动换行
    })
    sheet.set_row(0, 40)
    # 表头
    headfomat = book.add_format({
        'bg_color': '#DDDDDD',  # 单元格背景颜色
        'bold': True,  # 字体加粗
        'border': 1,  # 单元格边框宽度
        'align': 'center',
        'valign': 'vcenter',  # 字体对齐方式
        'text_wrap': True,  # 是否自动换行
    })

    # 写表头标题
    if data:
        data = data
    else:
        # 默认表头
        data = "练习生平时成绩"
    # 合并单元格
    sheet.merge_range(0,0,0,len(keys)-1,data,titlefomat)

    # 设置第二行表头的高度
    sheet.set_row(1, 30)
    for single_head in excel_heads:
        # 写表头
        index = excel_heads.index(single_head)
        # 设置镜头号的长度
        sheet.set_column('B:B', width=25)
        # 设置修改意见的长度
        sheet.set_column('D:D',width=30)
        # 设置日期的长度
        sheet.set_column('E:E',width=10)
        # 设置备注日期
        sheet.set_column('F:F',width=20)

        sheet.write(1, index, single_head, headfomat)

    # 第1行为表头，从第2行开始写数据
    outer_row = 2
    # 写数据
    for message in all_msg:
        sheet.set_row(outer_row, 25)
        for key in keys:
            if key=='submit_time':
                if message[key]:
                    # 时间戳转字符串
                    timeArray = time.localtime(message[key])
                    otherStyleTime = time.strftime("%Y/%m/%d", timeArray)
                    sheet.write(outer_row, keys.index(key), otherStyleTime)
                else:
                    sheet.write(outer_row, keys.index(key), '',workfomat)
            else:
                sheet.write(outer_row, keys.index(key), message[key],workfomat)
        # 换行
        outer_row += 1
        # 写内部审批通过的数据
    # 保存表
    # 冻结首行，方便数据和表头对应
    sheet.freeze_panes(1, 0)

    book.close()
    content['status'] = SUCCESS
    content['msg'] = "成功创建excel"
    content['path'] = relpath
    return content