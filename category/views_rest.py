#! -*- coding:utf-8 -*-
import json
import pdb 
from django.http import HttpResponse, HttpResponseForbidden 
from django.utils.translation import ugettext as _
from category.models import Category 
from appuser.models import AdaptorUser as User 
from datetime import datetime
from rest_framework.views import APIView
from django.conf import settings
from property.code import * 
import os
from common.fileupload import FileUpload
 
from common.logutils import getLogger
logger = getLogger(True, 'category', False)
 
def check_name_exist(name, ):
    """检查名称是否已经存在，如果存在返回True，否则返回False"""
    return Category.objects.filter(name = name).exists()


class CategoryRestView(APIView):
     
    def get(self, request): 
        content = {} 
        categories = list(Category.objects.filter(level=1).values(
            "id","name", "icon", "visible", "categorytype", "sort"
        ))
        for category in categories:
            category['sub'] = list(Category.objects.filter(parent__id = category['id']).values(
                                "id","name", "icon", "visible", "categorytype", "sort"
                            ))
        content['msg'] = categories
        content['status'] = SUCCESS

        return HttpResponse(json.dumps(content), content_type="application/json")
 
    def post(self, request):
        """
        新建
        """
        result = {} 
        user = request.user
        # 新建
        if not user.is_superuser:
            # 无权限
            return HttpResponse('Unauthorized', status=401)


        if 'method' in request.POST:
            method = request.POST['method'].lower()
            if method == 'put':  # 修改
                return self.put(request)
            elif method == 'delete':  # 删除
                return self.delete(request)
 
        # 新建 分类
        # name字段是必须的；如果提供了parentid，则新的为parent的子
         
        if 'name' in request.POST   :
            name = request.POST['name'].strip()
           
            parentid = request.POST.get('parentid') 
           
            if len(name) > 1024 :
                result['status'] = ERROR
                result['msg'] ='name too long.'
                return HttpResponse(json.dumps(result), content_type="application/json") 
            elif len(name) == 0:
                result['status'] = ERROR
                result['msg'] ='name is empty.'
                return HttpResponse(json.dumps(result), content_type="application/json")
            elif check_name_exist(name):
                # 名称已经存在
                result['status'] = ERROR
                result['msg'] ='name duplicated.'
                return HttpResponse(json.dumps(result), content_type="application/json")
            visible = 1
            if 'visible' in request.POST:
                visible = int(request.POST['visible'])
            
            if 'sort' in request.POST:
                sort = int(request.POST['sort'])
            else:
                sort = 1
            
            if 'icon' in request.FILES:
                # 获取主图
                imagefile = request.FILES['icon']
                pre = datetime.now().strftime("%Y%m%d%H%M%S%f")
                file_name, file_extension = os.path.splitext(
                    imagefile.name)
                filename = pre+file_extension
                FileUpload.upload(imagefile,
                                    os.path.join('category', str(user.id)),
                                    filename)
                icon = os.path.join('images', 'category', str(user.id), filename  )
            else:
                icon = ""     
                  
            categorytype = 0
            if 'categorytype' in request.POST:
                categorytype = int(request.POST['categorytype'])

            if parentid: 
                # 创建顶级子类别
                try:
                    category = Category.objects.get(id=parentid) 
                    level = category.level
                    category = Category.objects.create(name=name, level=level+1, 
                         parent=category) 
                    category.icon = icon 
                    category.visible = visible 
                    category.sort = sort 
                    category.categorytype = categorytype 
                    category.save()
                    result['id'] = category.id
                    result['status'] = SUCCESS
                    result['msg'] ='已完成'
                except Category.DoesNotExist:
                    result['status'] = ERROR
                    result['msg'] = [parentid] #'404 Parent category not found ID:{}'.format(parentid) 
            else:
                # 创建顶级类别
                category = Category.objects.create(name=name)
                category.icon = icon 
                category.visible = visible 
                category.sort = sort 
                category.categorytype = categorytype 
                category.save()
                result['id'] = category.id
                result['status'] = SUCCESS
                result['msg'] ='已完成'
        else:
            result['status'] = ERROR
            result['msg'] ='Need name in POST'
   
        return HttpResponse(json.dumps(result), content_type="application/json")


    def put(self, request):
        """
        修改
        """
        result = {}
        user = request.user 
        data = request.POST
        if 'id' in data:
            categoryid = data['id']
            try:
                category = Category.objects.get(id=categoryid)
                if 'name' in data:
                    name = data['name']
                    category.name = name
                 
                if 'sort' in request.POST:
                    sort = int(request.POST['sort'])
                    category.sort = sort 
                  
                if 'icon' in request.FILES:
                    # 获取主图
                    imagefile = request.FILES['icon']
                    pre = datetime.now().strftime("%Y%m%d%H%M%S%f")
                    file_name, file_extension = os.path.splitext(
                        imagefile.name)
                    filename = pre+file_extension
                    FileUpload.upload(imagefile,
                                        os.path.join('category', str(user.id)),
                                        filename)
                    filepath = os.path.join('images', 'category', str(user.id), filename  )
                    if category.icon:
                        # 删除旧的缩略图
                        imgpath = os.path.join(settings.BASE_DIR, category.icon )
                        if os.path.isfile(imgpath): 
                            os.remove(imgpath)
                    category.icon = filepath

                if 'visible' in data:
                    visible = int(data['visible'])
                    category.visible = visible
                
                if 'categorytype' in data:
                    categorytype = int(data['categorytype'])
                    category.categorytype = categorytype
                    
                     
                category.save()
             
                result['status'] = SUCCESS
                result['msg'] ='已完成'
            except Category.DoesNotExist:
                result['status'] = CATEGORY_NOTFOUND
                result['msg'] ='404 Not found the id'
     
        else:
            result['status'] = CATEGORY_ARGUMENT_ERROR_NEED_NAME_ID
            result['msg'] ='Need name and id  in POST'


        return HttpResponse(json.dumps(result), content_type="application/json")


    def delete(self, request):
        """
        删除
        """
        result = {}
        user = request.user
        data = request.POST
        if 'id' in data:
            categoryid = data['id'] 
            try:
                category = Category.objects.get(id=categoryid) 
                 
                if category.icon:
                    # 删除旧的缩略图
                    imgpath = os.path.join(settings.BASE_DIR, category.icon )
                    print(imgpath)
                    if os.path.isfile(imgpath): 
                        os.remove(imgpath)
              
                category.delete() 
                result['status'] =SUCCESS
                result['msg'] ='已完成'
            except Category.DoesNotExist:
                result['status'] = ERROR
                result['msg'] ='404 Not found the id' 
        elif 'ids' in data:
            ids = data['ids'] 
            try:
                categories = Category.objects.filter(id__in=ids.split(","))  
                for category in categories:
                    if category.icon:
                        # 删除旧的缩略图
                        imgpath = os.path.join(settings.BASE_DIR, category.icon )
                        print(imgpath)
                        if os.path.isfile(imgpath): 
                            os.remove(imgpath)
                
                    category.delete() 

                result['status'] =SUCCESS
                result['msg'] ='已完成'
            except Category.DoesNotExist:
                result['status'] = ERROR
                result['msg'] ='404 Not found the id' 
        else:
            result['status'] = ERROR
            result['msg'] ='Need id in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")

