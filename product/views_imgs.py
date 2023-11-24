#! -*- coding: utf-8 -*- 
import json
import os
import pdb
import traceback
from django.db.models import Q
from common.logutils import getLogger
from datetime import datetime, timedelta
from rest_framework.views import APIView 
from django.views import View
from django.http import HttpResponse, HttpResponseForbidden
from common.fileupload import FileUpload
from property import settings 
from property.code import SUCCESS, ERROR 
from product.models import Product, ProductImagesType, Category, ProductImages
import uuid
from tags.comm import add 
from product.comm import product_infos_lst,  \
editData, get_single_product, addSpecs, setHomestayPrice  
logger = getLogger(True, 'product', False)
 

class ImgAnonymousView(View): 
    def get(self, request):
        # 查看 
        result = {"status": ERROR}
         
        if 'uuid' in request.GET:
            # 获得单个民宿的详细信息
            productuuid = request.GET['uuid'] 
            try:
                product = Product.objects.get(uuid = productuuid) 
                result = { 
                    "status":SUCCESS,
                    "msg":get_single_product(product)
                  }
            except Product.DoesNotExist:
                result = { 
                    "status":ERROR,
                    "msg":"未找到民宿"
                  }
            return HttpResponse(json.dumps(result), content_type="application/json")

        kwargs = {}
        
          
        if 'title' in request.GET:
            title = request.GET['title'].strip()
            kwargs['title__icontains'] = title
        sub = []
        qfilter = None
        if 'categoryid' in request.GET:
            categoryid = request.GET['categoryid'].strip() 
            sub = list(Category.objects.filter(parent__id = categoryid).values("name", "id"))
            if len(sub) > 0: 
                qfilter = Q(category__id = categoryid) | Q(category__parent__id = categoryid)
            else:
                kwargs['category__id'] = categoryid

        if 'recommend' in request.GET: 
            kwargs['recommend'] = 1 # 获取推荐产品
        else:
            kwargs['ready'] = 1
        
        if 'producttype' in request.GET:
            producttype = request.GET['producttype'].strip()
            kwargs['producttype'] = producttype

        
        if 'latest' in request.GET:
            # 获取最新产品
            now =  datetime.today()
            now = now + timedelta(days= -90)
            kwargs['date__gte'] = now # 获取最近90天的产品
 
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
        if qfilter is None:
            gifts = Product.objects.filter(
                **kwargs).order_by("-date")[page*pagenum: (page+1)*pagenum]
            total = Product.objects.filter(**kwargs).count()
        else:
            gifts = Product.objects.filter(
                Q(**kwargs), qfilter).order_by("-date")[page*pagenum: (page+1)*pagenum]
            total = Product.objects.filter(Q(**kwargs), qfilter).count()
        result['status'] = SUCCESS
        result['msg'] = {
            "list": product_infos_lst(gifts),
            "total": total,
            "sub" : sub
        } 
        return HttpResponse(json.dumps(result), content_type="application/json")


class ProductImgView(APIView):
    """
    民宿图片管理
    """
    def get(self, request):
        #查看民宿
        result = { }  
        if 'uuid' in request.GET:
            # 获得单个民宿的详细信息
            productuuid = request.GET['uuid']  
            img_types = list(ProductImagesType.objects.filter(product__uuid = productuuid).values(
                    "id", "name", "sort"
                ))
            for img_type in  img_types:
                imgs = list(ProductImages.objects.filter(imgtype__id = img_type['id']).values(
                    "id", "img",
                ))
                img_type['imgs'] = imgs
            result = { 
                "status":SUCCESS,
                "msg":img_types
                } 
        else:
            result = { 
                    "status":ERROR,
                    "msg":"参数错误"
            } 

        return HttpResponse(json.dumps(result), content_type="application/json")

    
    def post(self, request):
        # 添加图库
        result = {}
        user = request.user 
        data = request.POST 
        if not user.is_superuser:
            result['status'] = ERROR
            result['msg'] = "无管理权限"
            return HttpResponse(json.dumps(result), content_type="application/json")

        if 'method' in data:
            method = data['method'].lower()
            if method == 'put':
                return self.put(request)
            elif method == 'delete':
                return self.delete(request)

        
        if 'sort' in data and  'name' in data   and 'productuuid' in data:
            name = data['name'].strip()
            sort = data['sort'].strip()
            productuuid = data['productuuid'].strip()
            try:
                product = Product.objects.get(uuid = productuuid) 
                imgtype, created = ProductImagesType.objects.get_or_create(
                    product = product, name = name)
                imgtype.sort = sort
                imgtype.save()
                # 上传图片 
                for filekey in request.FILES: 
                    print(filekey)
                    imagefile = request.FILES[filekey]
                    pre = datetime.now().strftime("%Y%m%d%H%M%S%f")
                    file_name, file_extension = os.path.splitext(
                        imagefile.name)
                    filename = pre+file_extension
                    FileUpload.upload(imagefile,
                            os.path.join('product', str(user.id)),
                            filename)
                    filepath = os.path.join('product', str(user.id), filename  )
                    ProductImages.objects.create(
                        imgtype = imgtype,
                        img = filepath
                    )

                result['status'] = SUCCESS
                result['msg'] = '发布成功'
            except Product.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '民宿信息不存在'
               
        else:
            result['status'] = ERROR
            result['msg'] = 'sort,name,productuuid为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")
    
    def put(self,request):
        # 修改民宿图库
        result = {} 
        data = request.POST
        user = request.user
        if 'imgid' in data:
            imgid = data['imgid'] 
            try:
                imgtype = ProductImagesType.objects.get(id = imgid)
            except ProductImagesType.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未能找到该id对应的相册'
                return HttpResponse(json.dumps(result), content_type="application/json")
            
            if 'name' in data:
                name = data['name'].strip()
                
                if name:
                    imgtype.name = name
                    exist = ProductImagesType.objects.filter(
                        name = name, product = imgtype.product
                    ).exclude(id = imgid).exists()
                    if exist:
                        result['status'] = ERROR
                        result['msg'] = '相册名称重复'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                else:
                    result['status'] = ERROR
                    result['msg'] = '相册名称不能为空'
                    return HttpResponse(json.dumps(result), content_type="application/json")

            if 'sort' in data:
                sort = data['sort'].strip() 
                imgtype.sort = sort
                   

            imgtype.save()

            # 上传图片 
            for filekey in request.FILES:  
                imagefile = request.FILES[filekey]
                pre = datetime.now().strftime("%Y%m%d%H%M%S%f")
                file_name, file_extension = os.path.splitext(
                    imagefile.name)
                filename = pre+file_extension
                FileUpload.upload(imagefile,
                        os.path.join('product', str(user.id)),
                        filename)
                filepath = os.path.join('product', str(user.id), filename  )
                ProductImages.objects.create(
                    imgtype = imgtype,
                    img = filepath
                )        
            
            result['status'] = SUCCESS
            result['msg'] = '修改成功'
        else:
            result['status'] = ERROR
            result['msg'] = 'imgid参数为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self,request):
        # 删除图片或者相册
        result = {} 
        data = request.POST
        
        if 'imgid' in data:
            imgid = data['imgid']
            try:
                p_img = ProductImages.objects.get(id = imgid)
                if p_img.img :
                    try:  
                        os.remove(os.path.join(settings.FILEPATH, p_img.img))
                    except IOError:
                        pass
                p_img.delete()
                result['status'] = SUCCESS
                result['msg'] = '删除成功'
            except ProductImages.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '图片不存在' 
        elif 'typeid' in data:
            typeid = data['typeid']
               
            try:
                imgtype = ProductImagesType.objects.get(id = typeid)
                imgs = ProductImages.objects.filter(imgtype = imgtype)
                for p_img in imgs:
                    if p_img.img :
                        try:  
                            os.remove(os.path.join(settings.FILEPATH, p_img.img))
                        except IOError:
                            pass
                    
                    p_img.delete()
                
                imgtype.delete()
                result['status'] = SUCCESS
                result['msg'] = '删除成功'
            except ProductImagesType.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '相册不存在' 
        else:
            result['status'] = ERROR
            result['msg'] = '缺少ids参数'
        return HttpResponse(json.dumps(result), content_type="application/json")
  
 