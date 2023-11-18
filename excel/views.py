#! -*- coding:utf-8 -*-
import json
import pdb
import os
import traceback
import datetime
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseForbidden 
from django.utils.translation import ugettext as _ 
from django.http import QueryDict
from django.core import serializers 
from common.customjson import LazyEncoder 
from excel.imageparsing import compenent 
from notice.comm import NoticeMgr 
from django import forms
from django.utils import timezone 


from rest_framework.views import APIView
from appfile.models import Attachment
from common.fileupload import FileUpload
from property.code import  SUCCESS, ERROR
from common.logutils import getLogger
from common.parseimg import parseimg
from property.settings import FILEPATH

from excel.excel import readExcel, readExcel_list
from django.conf import settings 
import xlwt 
logger = getLogger(True, 'excel', False)


class ExcelView(APIView):
    
    
    def post(self, request):  
        """ 
        将excel中的内容解析为列表格式，返回给前端，仅支持xlsx格式的excel
        """  
        # 验证是否有新建资产的权限 
        content = {}
        if 'file' in request.FILES: 
            excel_file = request.FILES['file'] 
            if not excel_file.name.lower().endswith("xlsx"):
                content['status'] = ERROR
                content['msg'] = "仅仅支持xlsx文件格式"
            else:
                time_tag = timezone.now().strftime("%Y%m%d%H%M%S")
                filename = time_tag + excel_file.name
                filepath = FileUpload.upload(excel_file, 'tmp', filename) 
                excel_list = readExcel_list(filepath)
                try:
                    #imagepath = compenent(filepath, os.path.join(os.path.join(FILEPATH, 'excel'),
                    #                                            time_tag))
                    imagepath = os.path.join(settings.FILEPATH, 'excel', time_tag  )
                    
                    images = parseimg(filepath, imagepath)
                    length = len(excel_list)
                    images_list = [0] * length 
                    for image in images: 
                        if length > image[0]['row']:
                            images_list[image[0]['row'] ] = os.path.join(settings.IMAGEROOTPATH,   'excel',  time_tag, image[2])
                        else:
                            break
                   
                    data_list = [] 
                    for  index, excel_item  in enumerate(excel_list): 
                        
                        image_path = ''
                        try: 
                            if images_list[index]:
                                image_path = images_list[index]
                        except TypeError:
                            pass
                        tmp_list = [image_path] + excel_item 
                        data_list.append(tmp_list)
                         
                    content['msg'] = data_list
                except FileNotFoundError:
                    content['msg'] = excel_list
                content['status'] = SUCCESS
              
        return HttpResponse(json.dumps(content), content_type="application/json")

 