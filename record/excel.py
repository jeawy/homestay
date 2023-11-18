import pdb
import os
import traceback 
import json
import datetime
import xlwt
import xlsxwriter
from property.code import  SUCCESS, ERROR  
from django.conf import settings  
 
 
def save_record_excel(record):
    """ 
    参数 excel_heads 表头汉字
         keys 键
         all_msg 值
    :return:
    """
    content = {}
    # 按照设置的类型解析为字符串
    datestr = record.date.strftime("%Y %m %d %H:%M:%S")
    # 设置文件的名称 按照项目名称加时间
    suffix = ".xlsx"
    filename = record.uuid + suffix
    basedir = settings.FILEPATH 
    relpath = os.path.join( 'excel', filename)
    if not os.path.isdir(os.path.join(basedir,  'excel')):
        os.makedirs(os.path.join(basedir,  'excel'))
    abspath = os.path.join(basedir, relpath)
    if os.path.isfile(abspath):
        try:
            os.remove(abspath) # 删除旧文件
        except PermissionError:
            content['status'] = ERROR
            content['msg'] = "请稍后重试" 
            return content

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

    contentfomat = book.add_format({
        'border': 1,  # 单元格边框宽度
        'align': 'left',  # 对齐方式
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
    
    extra_json = json.loads( record.extra)
    extra_ls = [] 
    if extra_json:
        for extra_item in extra_json:
            extra_ls.append(extra_item['label'])
    keys = excel_heads = extra_ls
    minwidth = 9
    if len(keys) > minwidth:
        minwidth = len(keys) -1
    else:
        for index in range(0, minwidth - len(keys) + 1):
            keys.append("") # 为了好看，加空表头
    # 写表头标题 
    # 合并单元格
    sheet.merge_range(0,0,0,minwidth,record.title,titlefomat)
    if record.content:
        # 设置content内容
        sheet.merge_range(1,0,2,minwidth,record.content,contentfomat)
        sheet.set_row(3, 30)
        outer_row = 3
    else:
        # 设置第二行表头的高度
        sheet.set_row(1, 30) 
        outer_row = 2

    for index, single_head in enumerate(excel_heads):
        # 写表头 
        sheet.write(outer_row, index, single_head, headfomat)
    outer_row = outer_row +1 
    userinfos = [] 
    users = record.userrecord.all()
    for user in users:
        user_dict = {} 
        if user.values: 
            values = user.values.split(",")
        else:
            values = []
        for index in range(0, minwidth - len(values) + 1):
            values.append("") # 为了好看，加空数据
        user_dict['values'] = values
        userinfos.append(user_dict)
      
    # 写数据
    for user in userinfos:
        sheet.set_row(outer_row, 25)
        for index, value  in enumerate(user['values']): 
            sheet.write(outer_row, index, value,workfomat)
        # 换行
        outer_row += 1
        # 写内部审批通过的数据
    # 保存表
    # 冻结首行，方便数据和表头对应
    sheet.freeze_panes(1, 0)

    book.close()
    content['status'] = SUCCESS
    content['msg'] = "成功创建excel"
    content['path'] = os.path.join("images",relpath)
    return content