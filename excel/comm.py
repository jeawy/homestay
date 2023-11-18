import pdb
import os
import traceback
import property.settings
import json
import datetime
import xlwt
import xlsxwriter
from property.code import  SUCCESS, ERROR
from django.http import HttpResponse, HttpResponseForbidden 
from excel.imageparsing import compenent
from django.conf import settings
from appuser.models import AdaptorUser as User
from dept.models import Dept
import time 
from PIL import Image
from common.logutils import getLogger 
logger = getLogger(True, 'excel', False)
 "

def save_excel(entity_json):

    """
    将数据转为excel

     post发送的json请求
    {"keys": ["category", "image", "path", "name", "creator", "team",
                           "inner_version", "outer_version", "priority", "level",
                           "project", "session", "frame", "episode"],
                  "values":
                      [["4", "", "aa", "资产1", "1", "3", "inner_version", "outer_version", "0", "1", "", "1", "5",
                        "22"],
                       ["", "b", "bb", "资产2", "5", "", "", "", "1", "2", "", "11", "25", ""],
                       ["", "c", "cc", "资产3", "9", "", "", "", "0", "3", "", "", "", ""]],
                  "project_id":1}

    """

    # 验证是否有新建资产的权限
    content = {}
    task_list_dict = []
    data = entity_json

    date = datetime.datetime.now()
    # 按照设置的类型解析为字符串
    datestr = date.strftime("%Y_%m_%d_%H_%M_%S")
    # 设置文件的名称 按照项目名称加时间
    suffix = ".xlsx"
    filename = datestr + suffix
    basedir = settings.BASE_DIR
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
        'top':1,        #顶边
        'left':1,       #左边
        'right':1,      #右边
        'bottom':1,      #底边
        'text_wrap':1          #自动换行
    })

    try:
        key_list = data["keys"] 
        header = data['header']  #中文英文对应表头
        all_dic = data['all_dic']   #类型[{"sub_task":[{"sub_task":[{}]}]}]
        tag = data['tag']
    except:
        content['status'] = ERROR
        content['msg'] = 'JSON错误'
        return content
     
    # 设置表头
    i = 0
    keys = []
    for k in key_list:
        k_index = key_list.index(k)
        # 设置宽度
        if k == 'name' or k == 'content' or k == 'inner_version' or k == 'remark':
            sheet.set_column(k_index, k_index, width=40)
        # 设置宽度
        if k == 'frame_range' or k == 'total_date_end' \
                or k == 'create_date' or k == 'start_date' or k == 'end_date':
            sheet.set_column(k_index, k_index, width=30)
        # 设置图片的宽度
        if k == 'image':
            sheet.set_column(k_index, k_index, width=25)
        try:
            if(k == "link"):
                sheet.write(0, i, "工种",workfomat)
                i = i + 1
                keys.append("link_dept")
                sheet.write(0, i, "环节截止日期",workfomat)
                i = i + 1
                keys.append("link_date_end")
            else:
                header_value = header[k]       #表头按照keys换成中文
                sheet.write(0, i, header_value,workfomat) #按照规定的格式写表头
                keys.append(k)
                i = i + 1
        except:
            continue
    # 保存表值
    row = 1
    for value in all_dic:
        #print(value)
        for key in keys:
            # 字典转列表
            try:
                key_index = keys.index(key)
                if key == "link_dept":

                    dept_name = ""
                    for single_link in value['link']:
                        dept_name = dept_name + single_link["name"] + "\n"
                    value_content = dept_name
                elif key == "link_date_end":
                    link_date_end = ""
                    for single_link in value['link']:
                        try:
                            # 先将时间戳转为datetime
                            time_stamp = datetime.datetime.fromtimestamp(int(single_link["date_end"]))
                            # 将datetime转为字符串
                            date = time_stamp.strftime(settings.DATEFORMAT)
                        except:
                            date = "-"
                        link_date_end = link_date_end +date + "\n"
                    value_content = link_date_end

                else:
                    value_content = value[key]
                if tag == "task":
                    if key == 'asset':
                        value_content = value_content["name"]

                    if key == "executor":
                        executor = ""
                        for content in value_content:
                            executor = executor + content["name"]
                        value_content = executor

                    if key == 'creator':
                        value_content = value_content["name"]
                    if key == 'grade':
                        grade = int(value_content)
                        if grade == 0:
                            value_content = "简单"
                        if grade == 1:
                            value_content = "标准"
                        if grade == 2:
                            value_content = "难"
                    if key == 'status':
                        status = int(value_content)
                        if status == 0:
                            value_content = "暂停"
                        if status == 1:
                            value_content = "未开始"
                        if status == 2:
                            value_content = "进行中"
                        if status == 3:
                            value_content = "审核中"
                        if status == 4:
                            value_content = "完成"
                        if status == 5:
                            value_content = "超时"
                    if key == 'priority':
                        priority = int(value_content)
                        if priority == 0:
                            value_content = "低级"
                        if priority == 1:
                            value_content = "中级"
                        if priority == 2:
                            value_content = "高级"

                if tag == "asset":
                    if key == 'total_date_end':
                        if value_content:
                            time_stamp = value_content
                            timeArray = time.localtime(time_stamp)
                            value_content = time.strftime("%Y/%m/%d", timeArray)
                        else:
                            # 没有计划结束日期的时候默认为空串
                            value_content = ""
                    if key == 'status':
                        status = int(value_content)
                        if status == 0:
                            value_content = "暂停"
                        if status == 1:
                            value_content = "未开始"
                        if status == 2:
                            value_content = "进行中"
                        if status == 3:
                            value_content = "审核中"
                        if status == 4:
                            value_content = "完成"
                     
                    # 将priority转字符
                    if key == 'priority':
                        priority = int(value_content)
                        if priority == 0:
                            value_content = "正常"
                        if priority == 1:
                            value_content = "优先"
                    # 将imgage转图片
                    if key == 'image':
                        # 设置宽 高
                        sheet.set_column(key_index,key_index,width=25) # 设置宽
                        sheet.set_row(row, 100)  #设置高
                        if value_content:
                            # 相对路径
                            image_path = value_content
                            # 绝对路径
                            basedir = settings.BASE_DIR
                            # 得到绝对路径去查找有没有文件
                            abspath = os.path.join(basedir, image_path)
                            # 判断一个image是否存在
                            if os.path.exists(abspath):
                                img_format = {
                                    'x_offset': 1,  # 水平偏移
                                    'y_offset': 1,  # 垂直偏移
                                    #'x_scale': 0.1,  # 水平缩放
                                    #'y_scale': 0.1,  # 垂直缩放
                                    'url': None,
                                    'tip': None,
                                    'image_data': None,
                                    'positioning': 1
                                }
                                im = Image.open(abspath)
                                (x, y) = im.size  # read image size
                                x_s = 180  # define standard width
                                y_s = 130 # calc height based on standard width
                                out = im.resize((x_s, y_s), Image.ANTIALIAS)  # resize image with high-quality
                                # 相对路径设定
                                if "excel" in abspath:
                                    adjust_abs_path = abspath.replace("excel","adjust")

                                if "appfile" in abspath:
                                    adjust_abs_path = abspath.replace("appile","adjust")
                                #new_filename = os.path.basename(adjust_abs_path)
                                #尺寸裁剪后的路径
                                new_dir = os.path.dirname(adjust_abs_path)
                                if not os.path.isdir(new_dir):
                                    os.makedirs(new_dir)
                                out.save(adjust_abs_path)
                                sheet.insert_image(row,key_index,adjust_abs_path,img_format)

                    # if key == 'link_dept':
                    #     pass
                    #
                    # if key == 'link_date_end':
                    #     pass

                #时间戳转字符串
                if key == 'create_date' or key == 'start_date' or key == 'end_date' \
                        or key == "create_time" :
                    try:
                        # 先将时间戳转为datetime
                        value_content = datetime.datetime.fromtimestamp(int(value_content))
                        # 将datetime转为字符串
                        value_content = value_content.strftime(settings.DATEFORMAT)
                    except:
                        value_content = value_content
                # 遍历出所有的sub_task

                if key == 'sub_task':
                    pass
 
                # 将datetime.date转字符串
                # if type(value_content) == datetime.datetime:
                #     value_content = value_content.strftime(settings.DATETIMEFORMAT)
                # if type(value_content) == datetime.date:
                #     value_content = value_content.strftime(settings.DATEFORMAT)
                # 将人的id转name
                # if key == 'user':
                #     value_content = User.objects.get(id = int(value_content)).username
                # 将status转字符




                # if key == 'dept':
                #     dept = int(value_content)
                #     value_content = Dept.objects.get(id = dept).name

                # if key == "image":
                #     try:
                #         image = bytes(value_content, encoding="utf8")
                #         # 将base64转图像
                #         value_content = value_content.b64decode(image)
                #     except:
                #         content['status'] = ERROR
                #         content['msg'] = 'base64转换图片不成功'
                #         return content

                if key !="image"  :
                    sheet.write(row, key_index, value_content,workfomat)  # 参数'1-行, 1-列'指定表中的单元，'value'是向该单元写入的内容

            except ValueError:
                pass
        row = row + 1
    
    book.close()
    content['status'] = SUCCESS
    content['msg'] = "成功创建excel"
    content['path'] = relpath
    return content
   