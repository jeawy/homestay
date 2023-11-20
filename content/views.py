#! -*- coding: utf-8 -*- 
import json
import os
import pdb
import traceback
import uuid
from django.shortcuts import render
from common.logutils import getLogger
from datetime import datetime
from rest_framework.views import APIView
from like.models import Readcount

from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.http import HttpResponse 
from property import settings
from appuser.models import AdaptorUser as User
from property.code import SUCCESS, ERROR
from address.models import Address
from content.models import   TxtContent,  Category
from tags.models import Tags
from tags.comm import add 
from property.entity import EntityType
from content.i18 import   *
from appfile.models import Attachment
from appfile.comm import AppFileMgr 
from content.comm import product_infos_lst, \
                         product_info,  get_product_name
logger = getLogger(True, 'product', False)

from common.express import get_express



class ProductAnonymousView(View):
  
    def get(self, request):
        # 查看，应该限制在小区范围内
        result = {"status": ERROR}
        if 'no' in request.GET:
            get_express(request.GET['no']) 


        if 'uuid' in request.GET:
            productuuid = request.GET['uuid']
            try:
                product = TxtContent.objects.get(uuid=productuuid )
                readcount, created = Readcount.objects.get_or_create(
                    entity_uuid = productuuid,
                    entity_type = EntityType.PRODUCT)
                if not created:
                    readcount.number = readcount.number +1
                    readcount.save()
              
                result['msg'] = product_info(product, detail = True)
                result['status'] = SUCCESS
                return HttpResponse(json.dumps(result), content_type="application/json")
            except TxtContent.DoesNotExist:
                result['msg'] = PRODUCT_NOT_FOUNT
                return HttpResponse(json.dumps(result), content_type="application/json")


        kwargs = {}
         
        if 'content' in request.GET:
            content = request.GET['content'].strip()
            kwargs['content__icontains'] = content

        if 'title' in request.GET:
            title = request.GET['title'].strip()
            kwargs['title__icontains'] = title

        if 'product_type' in request.GET:
            product_type = request.GET['product_type']
            kwargs['product_type'] = product_type

        if 'product_types' in request.GET:
            product_types = request.GET['product_types']
            kwargs['product_type__in'] = product_types.split(",")

        if "page" in request.GET and "pagenum" in request.GET:
            # 分页
            pagenum = request.GET['pagenum']
            page = request.GET['page']
            try:
                page = int(page) - 1
                pagenum = int(pagenum)
            except ValueError:
                page = 0
                pagenum = settings.PAGE_NUM
        else:
            page = 0
            pagenum = settings.PAGE_NUM

        products = TxtContent.objects.filter(
            **kwargs).order_by("-date")[page*pagenum: (page+1)*pagenum]
        total = TxtContent.objects.filter(**kwargs).count()
        result['status'] = SUCCESS
        result['msg'] = {
            "list": product_infos_lst(products),
            "total": total
        }

        return HttpResponse(json.dumps(result), content_type="application/json")


class ProductView(APIView):
    """
    管理
    """

    def get(self, request):
        # 查看，应该限制在小区范围内
        result = {"status": ERROR}
        if 'uuid' in request.GET:
            productuuid = request.GET['uuid']
            try:
                product = TxtContent.objects.get(uuid=productuuid )
                readcount, created = Readcount.objects.get_or_create(
                    entity_uuid = productuuid,
                    entity_type = EntityType.PRODUCT)
                if not created:
                    readcount.number = readcount.number +1
                    readcount.save() 
                result['msg'] = product_info(product, detail = True)
                result['status'] = SUCCESS
                return HttpResponse(json.dumps(result), content_type="application/json")
            except TxtContent.DoesNotExist:
                result['msg'] = PRODUCT_NOT_FOUNT
                return HttpResponse(json.dumps(result), content_type="application/json")

        kwargs = {}
         
        user = request.user
        
        
        if 'content' in request.GET:
            content = request.GET['content'].strip()
            kwargs['content__icontains'] = content
        
        if 'status' in request.GET:
            status = request.GET['status'].strip()
            if status != "-1" and status != -1:
               kwargs['status'] = status
 
        if 'title' in request.GET:
            title = request.GET['title'].strip()
            kwargs['title__icontains'] = title

        if 'mine' in request.GET:
            kwargs['user'] = user

        if 'product_type' in request.GET:
            product_type = request.GET['product_type'] 
            kwargs['product_type'] = product_type

        if 'product_types' in request.GET:
            product_types = request.GET['product_types']
            kwargs['product_type__in'] = product_types.split(",")

        if "page" in request.GET and "pagenum" in request.GET:
            # 分页
            pagenum = request.GET['pagenum']
            page = request.GET['page']
            try:
                page = int(page) - 1
                pagenum = int(pagenum)
            except ValueError:
                page = 0
                pagenum = settings.PAGE_NUM
        else:
            page = 0
            pagenum = settings.PAGE_NUM

        products = TxtContent.objects.filter(
            **kwargs).order_by("-date")[page*pagenum: (page+1)*pagenum]
        total = TxtContent.objects.filter(**kwargs).count()
        result['status'] = SUCCESS
        result['msg'] = {
            "list": product_infos_lst(products),
            "total": total
        }

        return HttpResponse(json.dumps(result), content_type="application/json")

    def post(self, request):
        # 添加
        # 小区的IT技术支持，小区的管理，工作人员，都可以修改这个
        result = {
            'status':ERROR
        }
        user = request.user 
        data = request.POST
         

        if not user.is_superuser :
            return HttpResponse('Unauthorized', status=401)

        if 'method' in data:
            method = data['method'].lower()
            if method == 'put':
                return self.put(request)
            elif method == 'delete':
                return self.delete(request)

        product = TxtContent()
        if 'title' in data and 'content' in data :
            title = data['title'].strip()
            content = data['content'].strip()
            
            if 'detail' in data:
                detail = data['detail']
                detail = detail.replace('\n','<br/>') 
                product.detail = detail
            if 'product_type' in data:
                product_type = data['product_type']
                product.product_type = product_type
            
            if 'picture' in data:
                picture = data['picture']
                product.picture = picture
            
            if 'allow_comment' in data:
                allow_comment = data['allow_comment']
                product.allow_comment = allow_comment
            
            if 'status' in data:
                status = data['status']
                product.status = status
 
            if 'category' in data:
                category = data['category']
                if category:
                    obj, created = Category.objects.get_or_create(
                        name=category)
                    product.category = obj
                else:
                    result['status'] = ERROR
                    result['msg'] = 'categorys参数不能为空'
             
            product.uuid = uuid.uuid4()
            product.user = user
            product.content = content
            product.title = title
             
            product.save()

            # 发送消息
            title = "{0}：{1}".format(get_product_name(product.product_type), title)
            if product.product_type == product.INFORMATION:
                appurl = "/pages/usefulinfo/detail?uuid="+str(product.uuid)
            elif product.product_type in [ product.NOTIFICATION, product.ANNOUNCEMENT ]:
                appurl = "/pages/notice/detail?uuid="+str(product.uuid)
            elif product.product_type == product.NEWS:
                appurl = "/pages/news/detail?uuid="+str(product.uuid)
            
            entity_type = EntityType.PRODUCT
            entity_uuid = product.uuid
            # 这里应该发送的是APP推送通知，而不是系统内部通知

            result['status'] = SUCCESS
            result['msg'] = PRODUCT_ADD_SUCCESS 
            result['uuid'] = str(product.uuid)
        else:
            result['status'] = ERROR
            result['msg'] = 'content,title为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

    def put(self, request):
        # 修改
        # 小区的IT技术支持，小区的管理，工作人员，都可以修改这个

        result = {} 
        data = request.POST

        if 'uuid' in data  : 
            productuuid = data['uuid']
            try:
                product = TxtContent.objects.get(uuid=productuuid )
            except TxtContent.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未能找到该id对应的信息'
                return HttpResponse(json.dumps(result), content_type="application/json")
            if 'product_type' in data:
                product_type = data['product_type']
                product.product_type = product_type

            if 'picture' in data:
                picture = data['picture']
                product.picture = picture

            if 'status' in data:
                status = data['status']
                product.status = status
 
            if 'allow_comment' in data:
                allow_comment = data['allow_comment']
                product.allow_comment = allow_comment
                
            if 'title' in data:
                title = data['title'].strip()
                if title:
                    product.title = title
                else:
                    result['status'] = ERROR
                    result['msg'] = 'title参数不能为空'
                    return HttpResponse(json.dumps(result), content_type="application/json")

            if 'content' in data:
                content = data['content'].strip() 
                product.content = content
                 
            if 'detail' in data:
                detail = data['detail']
                detail = detail.replace('\n','<br/>') 
                product.detail = detail

            
            if len(request.FILES) : 
                # 移动端发通知的时候，上传的图片
                for image in request.FILES:
                    # 获取附件对象  
                    imagefile = request.FILES[image]
                    pre = datetime.now().strftime("%Y%m%d%H%M%S%f")
                    file_name, file_extension = os.path.splitext(imagefile.name)
                    filename = pre+file_extension
                    filepath = settings.APPFILEPATH
                    file_result = AppFileMgr.upload(imagefile, filepath, filename, Attachment.TEMP, 1 )
                    
                    fullpath = os.path.join(settings.PAYHOST, settings.IMAGEROOTPATH, 'appfile', filename)
                    if product.detail:
                        product.detail += '<img style="max-width:100%" src="'+fullpath+'"  />'
                    else:
                        product.detail = '<img style="max-width:100%" src="'+fullpath+'"  />'
                      
            if 'addtags' in data:
                # 添加标签
                # [{'name':'新', 'label':'new'},{'name':'新1', 'label':'new1'}]
                #
                #

                addtags = data['addtags']
                if isinstance(addtags, str):
                    addtags = json.loads(addtags)
                for addtag in addtags:
                    status, tag = add(addtag['name'], addtag['label'])
                    if tag not in product.tags.all():
                        product.tags.add(tag)

            if 'deltags' in data:
                # 删除标签
                deltags = data['deltags']
                if deltags:
                    tags = Tags.objects.filter(id__in=deltags.split(","))
                    for tag in tags:
                        product.tags.remove(tag)

            product.save()
            result['status'] = SUCCESS
            result['msg'] = '修改成功'
        else:
            result['status'] = ERROR
            result['msg'] = 'uuid参数为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self, request):
        # 删除
        result = {}

        
        data = request.POST

        if 'uuids' in data  :
            uuids = data['uuids'] 
            uuids_ls = uuids.split(',')
            # 这边正常应该还需要限制范围在小区内部
            TxtContent.objects.filter(uuid__in=uuids_ls ).delete()

            result['status'] = SUCCESS
            result['msg'] = '删除成功'
        else:
            result['status'] = ERROR
            result['msg'] = '缺少uuids参数'
        return HttpResponse(json.dumps(result), content_type="application/json")


class CategoryView(APIView):
    """
    分类管理
    """ 
    def get(self, request):
        # 查看分类
        result = {}
        kwargs = {}
        category_lst = []
        user = request.user

        if 'id' in request.GET:
            id = request.GET['id']
            kwargs['id'] = id

        if 'name' in request.GET:
            name = request.GET['name'].strip()
            kwargs['name__icontains'] = name

        categorys = Category.objects.filter(**kwargs)
        for category in categorys:
            category_lst.append(category.name)

        result['status'] = SUCCESS
        result['msg'] = category_lst
        return HttpResponse(json.dumps(result), content_type="application/json")

    def post(self, request):
        # 添加分类
        result = {}
        user = request.user

        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST

        if 'method' in data:
            method = data['method'].lower()
            if method == 'put':
                return self.put(request)
            elif method == 'delete':
                return self.delete(request)

        categry = Category()

        if 'name' in data:
            name = data['name'].strip()

            if name:
                if not check_category_exist(name):
                    categry.name = name
                    categry.save()

                    result['status'] = SUCCESS
                    result['msg'] = '创建成功'
                else:
                    result['status'] = ERROR
                    result['msg'] = '该分类名称已被使用'
            else:
                result['status'] = ERROR
                result['msg'] = 'name参数不能为空'
        else:
            result['status'] = ERROR
            result['msg'] = 'name参数为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

    def put(self, request):
        # 修改分类
        result = {}

        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST

        if 'id' in data:
            id = data['id'].strip()

            try:
                id = int(id)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = 'id参数应该为int类型'
                return HttpResponse(json.dumps(result), content_type="application/json")

            try:
                category = Category.objects.get(id=id)
            except Category.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未找到该id对应的分类'
                return HttpResponse(json.dumps(result), content_type="application/json")

            if 'name' in data:
                name = data['name'].strip()

                if not check_category_exist(name, id):
                    category.name = name
                    category.save()

                    result['status'] = SUCCESS
                    result['msg'] = '修改成功'
                else:
                    result['status'] = ERROR
                    result['msg'] = '该分类名称已被使用'
                return HttpResponse(json.dumps(result), content_type="application/json")

            result['status'] = SUCCESS
            result['msg'] = '修改成功'
        else:
            result['status'] = ERROR
            result['msg'] = 'id为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self, request):
        # 删除分类
        result = {}

        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST

        if 'ids' in data:
            ids = data['ids'].strip()
            ids = ids.split(',')

            try:
                Category.objects.filter(id__in=ids).delete()
            except:
                logger.error(traceback.format_exc())
                pass

            result['status'] = SUCCESS
            result['msg'] = '删除成功'
        else:
            result['status'] = ERROR
            result['msg'] = 'ids为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

 

def check_category_exist(name, excluded_id=None):
    if excluded_id:
        return Category.objects.filter(name=name).exclude(id=excluded_id)
    else:
        return Category.objects.filter(name=name)

 