#! -*- coding:utf-8 -*-
import json
import pdb 
from django.http import HttpResponse, HttpResponseForbidden 
from django.utils.translation import ugettext as _
from category.models import Category 
from appuser.models import AdaptorUser as User 
from rest_framework.views import APIView
from property.code import * 
 
from common.logutils import getLogger
logger = getLogger(True, 'category', False)
 
def check_name_exist(name, ):
    """检查名称是否已经存在，如果存在返回True，否则返回False"""
    return Category.objects.filter(name = name).exists()


class CategoryRestView(APIView):
     
    def get(self, request): 
        content = {} 
        categories = list(Category.objects.filter(level=1).values(
            "id","name", "icon", "visible", "categorytype"
        ))
        for category in categories:
            category['sub'] = list(Category.objects.filter(parent__id = category['id']).values(
                                "id","name", "icon", "visible", "categorytype"
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
         
        if 'name' in request.POST and 'icon' in request.POST :
            name = request.POST['name'].strip()
            icon = request.POST['icon'].strip()
            parentid = request.POST.get('parentid') 
           
            if len(name) > 1024 :
                result['status'] = DEPT_ARGUMENT_ERROR_NAME_TOO_LONG
                result['msg'] ='name too long.'
                return HttpResponse(json.dumps(result), content_type="application/json") 
            elif len(name) == 0:
                result['status'] = DEPT_ARGUMENT_ERROR_NAME_EMPTY
                result['msg'] ='name is empty.'
                return HttpResponse(json.dumps(result), content_type="application/json")
            elif check_name_exist(name):
                # 名称已经存在
                result['status'] = DEPT_DUPLICATED_NAME
                result['msg'] ='name duplicated.'
                return HttpResponse(json.dumps(result), content_type="application/json")
            visible = 1
            if 'visible' in request.POST:
                visible = int(request.POST['visible'])
            
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
                    category.categorytype = categorytype 
                    category.save()
                    result['id'] = category.id
                    result['status'] = SUCCESS
                    result['msg'] ='已完成'
                except Category.DoesNotExist:
                    result['status'] = DEPT_PARENTID_NOTFOUND
                    result['msg'] = [parentid] #'404 Parent Dept not found ID:{}'.format(parentid) 
            else:
                # 创建顶级类别
                category = Category.objects.create(name=name)
                category.icon = icon 
                category.visible = visible 
                category.categorytype = categorytype 
                category.save()
                result['id'] = category.id
                result['status'] = SUCCESS
                result['msg'] ='已完成'
        else:
            result['status'] = DEPT_ARGUMENT_ERROR_NEED_NAME
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
                 
                if 'icon' in data:
                    icon = data['icon']
                    category.icon = icon 
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
            deptid = data['id'] 
            try:
                dept = Category.objects.get(id=deptid) 
                logger.warning("user:{0} has deleted dept(id:{1}, name:{2}".format(user.username, dept.id, dept.name))
                dept.delete() 
                result['status'] =SUCCESS
                result['msg'] ='已完成'
            except Category.DoesNotExist:
                result['status'] = DEPT_NOTFOUND
                result['msg'] ='404 Not found the id' 
        elif 'ids' in data:
            ids = data['ids'] 
            try:
                Category.objects.filter(id__in=ids.split(",")).delete() 
                  
                result['status'] =SUCCESS
                result['msg'] ='已完成'
            except Category.DoesNotExist:
                result['status'] = DEPT_NOTFOUND
                result['msg'] ='404 Not found the id' 
        else:
            result['status'] = DEPT_ARGUMENT_ERROR_NEED_ID
            result['msg'] ='Need id in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")

