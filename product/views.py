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
from product.models import Product, Specifications, Category 
import uuid
from coupon.models import Coupon
from tags.comm import add 
from product.comm import product_infos_lst, specifications_infos_lst,\
editData, get_single_product, addSpecs, addExtra, setHomestayPrice, homestay_infos_lst,\
get_single_homestay_product  
logger = getLogger(True, 'product', False)
 

class ProductAnonymousView(View): 
    def get(self, request):
        # 查看 
        result = {"status": ERROR}

        date = None
        if 'date' in request.GET:
            date = request.GET['date'].strip()
            try:
                date = datetime.strptime(date, settings.DATEFORMAT).date()
            except ValueError:
                print("日期格式化错误.")

        if 'uuid' in request.GET:
            # 获得单个商品的详细信息
            productuuid = request.GET['uuid'] 
            try:
                product = Product.objects.get(uuid = productuuid) 
                if product.producttype == 0  or product.producttype == 2:
                    msg = get_single_homestay_product(product, date=date, detail=True ) 
                else:
                    msg = get_single_product(product, detail=True)
                result = { 
                    "status":SUCCESS,
                    "msg":msg
                }
            except Product.DoesNotExist:
                result = { 
                    "status":ERROR,
                    "msg":"未找到商品"
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
         

        producttype = 0  
        if 'producttype' in request.GET:
            producttype = request.GET['producttype'].strip()
        producttypes = []
        if 'producttypes' in request.GET:
            producttypes = request.GET['producttypes'].split(",")
            kwargs['producttype__in'] = producttypes
        else: 
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
            products = Product.objects.filter(
                **kwargs).order_by("-date")[page*pagenum: (page+1)*pagenum] 
        else:
            products = Product.objects.filter( Q(**kwargs), qfilter).order_by("-date")[page*pagenum: (page+1)*pagenum]
            
        result['status'] = SUCCESS
        if len(producttypes) > 0:
            # 普通商品
            result['msg'] = product_infos_lst(products, detail= False) 
        elif int(producttype) == 0  or int(producttype) == 2:
            result['msg'] = homestay_infos_lst(products, date=date)
        else:
            result['msg'] = product_infos_lst(products, detail = False)
            
        return HttpResponse(json.dumps(result), content_type="application/json")


class ProductView(APIView):
    """
    商品管理
    """
    def get(self, request):
        #查看商品
        result = {
            
        }
        kwargs = {}
        user = request.user

        if 'count' in request.GET:
            # pc端统计
             
            selling = 0 # 出售中 
            unready =  0  # 未上架
            recommend = 0 # 推荐 
            isbook = 0
            leftcount = 0 # 库存预警
            leftcount = Specifications.objects.filter(
                number__lte = 10, # 少于10个进行库存预警 
                product__ready = 1,
                product__producttype = 1
            ).count()
            isbook = Product.objects.filter(isbook = 1).count()
            recommend = Product.objects.filter(recommend = 1).count()
            unready = Product.objects.filter(ready = 0).count()
            selling = Product.objects.filter(ready = 1).count()
            result['status'] = SUCCESS
            result['msg'] = {
                "unready":unready,
                "selling":selling,
                "recommend":recommend,
                "isbook":isbook, 
                "leftcount":leftcount,
            }
            return HttpResponse(json.dumps(result), content_type='application/json')  

        if 'leftcount' in request.GET:
            # 查询库存较低的商品
            result['msg'] = list(Specifications.objects.filter(
                number__lte = 10, # 少于10个进行库存预警
                product__ready = 1, 
                product__producttype = 1
            ).values("product__uuid", "product__picture", "product__title", "number", "name" ))
            result['status'] = SUCCESS
            return HttpResponse(json.dumps(result), content_type='application/json')  
        
        admin = False # 不是管理员
        if user.is_superuser:
            admin = True


        if 'uuid' in request.GET:
            # 获得单个商品的详细信息
            productuuid = request.GET['uuid'] 
            try:
                product = Product.objects.get(uuid = productuuid) 
                if product.producttype == 0 or product.producttype == 2 :
                    msg = get_single_homestay_product(product, detail=True, admin=admin) 
                else:
                    msg = get_single_product(product, detail= True)
                result = { 
                    "status":SUCCESS,
                    "msg":msg
                  }
            except Product.DoesNotExist:
                result = { 
                    "status":ERROR,
                    "msg":"未找到商品"
                  }
            return HttpResponse(json.dumps(result), content_type="application/json")

 
        if 'user_id' in request.GET:
            user_id = request.GET['user_id']
            try:
                user_id = int(user_id)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = 'user_id参数应该为int类型'
                return HttpResponse(json.dumps(result), content_type="application/json")
            kwargs['user__id'] = user_id

        if 'product_id' in request.GET:
            product_id = request.GET['product_id']
            try:
                product_id = int(product_id)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = 'product_id参数应该为int类型'
                return HttpResponse(json.dumps(result), content_type="application/json")
            kwargs['id'] = product_id

        if 'content' in request.GET:
            content = request.GET['content'].strip()
            kwargs['content__icontains'] = content

        if 'title' in request.GET:
            title = request.GET['title'].strip()
            kwargs['title__icontains'] = title
        
        producttype = 0  
        producttypes = []
        if 'producttype' in request.GET:
            producttype = int(request.GET['producttype'].strip())

        if 'producttypes' in request.GET:
            producttypes = request.GET['producttypes'].split(",")
            kwargs['producttype__in'] = producttypes
        else: 
            kwargs['producttype'] = producttype
         
        
        if 'selling_prodcut' in request.GET:
            # 待销售商品
            selling_prodcut = request.GET['selling_prodcut'].strip()
            if int(selling_prodcut) == 1: 
                kwargs['ready'] = 1
            else:
                kwargs['ready'] = 0

        if 'recommend_prodcut' in request.GET:
            recommend_prodcut = request.GET['recommend_prodcut'].strip()
            if int(recommend_prodcut) == 1: 
                kwargs['recommend'] = 1
        

        sub = []
        qfilter = None
        if 'category' in request.GET:
            categoryid = request.GET['category'].strip() 
            if categoryid != "-1" and int(categoryid) != -1:
                sub = list(Category.objects.filter(parent__id = categoryid).values("name", "id"))
                if len(sub) > 0: 
                    qfilter = Q(category__id = categoryid) | Q(category__parent__id = categoryid)
                else:
                    kwargs['category__id'] = categoryid

 
        if 'mine' in request.GET:
            kwargs['user'] = user
        
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
            products = Product.objects.filter(
                **kwargs).order_by("-date")[page*pagenum: (page+1)*pagenum] 
            total = Product.objects.filter(**kwargs).count()
        else:
            products = Product.objects.filter(
                Q(**kwargs), qfilter).order_by("-date")[page*pagenum: (page+1)*pagenum]
            total =  Product.objects.filter(
                Q(**kwargs), qfilter).count()
            
        
        result_list = []
        if len(producttypes) > 0:
            # 普通商品
            result_list = product_infos_lst(products, detail= False)
        else:
            if producttype == 0 or producttypes == [1, 10]:
                # 民宿列表
                result_list = homestay_infos_lst(products, admin=admin)
            else:
                result_list = product_infos_lst(products, detail= False)

        result['status'] = SUCCESS
        result['msg'] = {
            "list":result_list,
            "total" : total
        }

        return HttpResponse(json.dumps(result), content_type="application/json")

    
    def post(self, request):
        # 添加商品
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

        product = Product() 
        if 'title' in data and  'content' in data   and 'category' in data:
            category = data['category'] 
            try:
                category = Category.objects.get(id= category)
                product.category = category
            except Category.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = "未找到相关类别"
                return HttpResponse(json.dumps(result), content_type="application/json")
            
            title = data['title']
            content = data['content']
              
            product = editData(product, data, request)
            
            product.producttype = category.categorytype 
            product.user = user
            product.content = content
            product.title = title 
            product.uuid=uuid.uuid4()
            product.save()


            if 'tags' in data: # 添加标签
                tags = data['tags'].split(",")
                producttype = 0
                
                 
                if producttype == 1:
                    label = "product"
                elif producttype == 2:
                    label = "car"
                else:
                    label = "homestay"
                for tag in tags:
                    if tag:
                        product.tags.add(add(tag, label))
             
             
            addSpecs(product, data)
            addExtra(product, data)
            if 'pricemode' in data:
                # 价格覆盖模式：0 仅覆盖日历上未设定价格的日期
                #              1 覆盖日历所有价格
                pricemode = int(data['pricemode'].strip())
                setHomestayPrice(product, pricemode)
             
            result['status'] = SUCCESS
            result['msg'] = '发布成功'
        else:
            result['status'] = ERROR
            result['msg'] = 'content,title,category为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")
    
    def put(self,request):
        # 修改商品
        result = {} 
        data = request.POST
        if 'uuid' in data:
            uuid = data['uuid'] 
            try:
                product = Product.objects.get(uuid = uuid)
            except Product.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未能找到该id对应的商品'
                return HttpResponse(json.dumps(result), content_type="application/json")
            
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
                if content:
                    product.content = content
                else:
                    result['status'] = ERROR
                    result['msg'] = 'content参数不能为空'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                
            if 'category' in data:
                category = data['category'] 
                try:
                    category = Category.objects.get(id= category)
                    product.category = category
                except Category.DoesNotExist:
                    result['status'] = ERROR
                    result['msg'] = "未找到相关类别"
                    return HttpResponse(json.dumps(result), content_type="application/json")
            
            product = editData(product, data, request)
            product.producttype = product.category.categorytype 
            product.save()

            if 'tags' in data: # 添加标签
                tags = data['tags'].split(",")
                if product.producttype==1:
                    label = "product"
                else:
                    label = "homestay"
                
                if product.tags:
                    product.tags.all().delete()

                for tag in tags:
                    if tag:
                        product.tags.add(add(tag, label))
            
            addSpecs(product, data) 
            addExtra(product, data)
            if 'pricemode' in data:
                # 价格覆盖模式：0 仅覆盖日历上未设定价格的日期
                #              1 覆盖日历所有价格
                pricemode = int(data['pricemode'].strip())
                setHomestayPrice(product, pricemode)


            if 'couponuuid' in data:
                # 优惠券
                couponuuid =  data['couponuuid'].strip() 
                try:
                    coupon = Coupon.objects.get(uuid = couponuuid)
                    product.coupon = coupon
                    product.save()
                except Coupon.DoesNotExist:
                    result['status'] = ERROR
                    result['msg'] = '商品信息已保存, 但优惠券没有绑定，优惠券不存在'

            if 'removecouponuuid' in data:
                # 移除优惠券
                product.coupon = None
                product.save()
            
 
            result['status'] = SUCCESS
            result['msg'] = '修改成功'
        else:
            result['status'] = ERROR
            result['msg'] = 'id参数为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self,request):
        # 删除商品
        result = {}

        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST

        if 'uuids' in data:
            uuids = data['uuids']
            uuids = uuids.split(',')
 
            for uuiditem in uuids:
                try:
                    product = Product.objects.get(uuid = uuiditem)
                except Product.DoesNotExist:
                    continue
                else:
                    # 删除商品时删除磁盘中对应的图片和轮播图文件
                    picture = product.picture 
                    if product.picture :
                        try: 
                            print(os.path.join(settings.FILEPATH,picture))
                            os.remove(os.path.join(settings.FILEPATH,picture))
                        except IOError:
                            pass
                
                    videopath = product.videopath 
                    if videopath:
                        try:
                            os.remove(os.path.join(settings.FILEPATH,videopath))
                        except IOError:
                            pass

                    if product.turns:
                        turns = product.turns.split(',')
                        for turn in turns:
                            if turn:
                                try:
                                    os.remove(os.path.join(settings.FILEPATH,turn))
                                except IOError:
                                    pass
                    
                    product.delete()
                    
            result['status'] = SUCCESS
            result['msg'] = '删除成功'
        else:
            result['status'] = ERROR
            result['msg'] = '缺少ids参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

class CategoryView(APIView):
    """
    分类管理
    """ 
    def get(self, request):
        #查看分类
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
        for category in  categorys:
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

    
    def put(self,request):
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
                category = Category.objects.get(id = id)
            except Category.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未找到该id对应的分类'
                return HttpResponse(json.dumps(result), content_type="application/json")
            
            if 'name' in data:
                name = data['name'].strip()

                if not check_category_exist(name ,id):
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

    def delete(self,request):
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
                Category.objects.filter(id__in = ids).delete()
            except:
                logger.error(traceback.format_exc())
                pass

            result['status'] = SUCCESS
            result['msg'] = '删除成功'
        else:
            result['status'] = ERROR
            result['msg'] = 'ids为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

class SpecificationsView(APIView):
    """
    商品规格管理
    """ 
    def get(self, request):
        #查看商品规格
        result = {}
        kwargs = {}
        user = request.user

        # 根据规格id进行筛选
        if 'id' in request.GET:
            id = request.GET['id']
            try:
                id = int(id)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = 'id参数应该为int类型'
                return HttpResponse(json.dumps(result), content_type="application/json")
            kwargs['id'] = id
        
        # 根据商品id进行筛选
        elif 'product_id' in request.GET:
            product_id = request.GET['product_id']
            try:
                product_id = int(product_id)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = 'product_id参数应该为int类型'
                return HttpResponse(json.dumps(result), content_type="application/json")
            try:
                product = Product.objects.get(id = product_id)
            except Product.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未找到该product_id参数对应的商品'
                return HttpResponse(json.dumps(result), content_type="application/json")
            specifications = product.product_specifications.all().order_by('-id')
            result['status'] = SUCCESS
            result['msg'] = specifications_infos_lst(specifications)
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = ERROR
            result['msg'] = 'id或product_id为必需参数'
            return HttpResponse(json.dumps(result), content_type="application/json")
            
        specs = Specifications.objects.filter(**kwargs)
        specifications_infos = []
        for spec in specs:
            specifications_infos.append(specifications_infos_lst(spec))
        result['status'] = SUCCESS
        result['msg'] = specifications_infos
        return HttpResponse(json.dumps(result), content_type="application/json")
 
    def post(self, request):
        # 添加商品规格
        result = {}
        kwargs = {}
        user = request.user

         
        data = request.POST

        if not user.is_superuser:
            # 价格修改只能是管理员
            return HttpResponseForbidden()

        if 'method' in data:
            method = data['method'].lower()
            if method == 'put':
                return self.put(request)
            elif method == 'delete':
                return self.delete(request)

        specifications = Specifications()
        if 'productuuid' in data and 'price' in data and 'date' in data:
            productuuid = data['productuuid']
            price = data['price']
            date = data['date']
            try:
                price = float(price)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = 'price格式错误'
                return HttpResponse(json.dumps(result), content_type="application/json")
            
            try:
                date = datetime.strptime(date, settings.DATEFORMAT)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = '日期格式错误,应该是yyyy/mm/dd格式'
                return HttpResponse(json.dumps(result), content_type="application/json")
            
            try:
                product = Product.objects.get(uuid = productuuid)
            except Product.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未找到该product参数对应的商品'
                return HttpResponse(json.dumps(result), content_type="application/json")
            
            purchase_way = Specifications.CASH 
             
            specifications.product = product
            specifications.price = price
            specifications.number = 1
            specifications.name = date.day
            specifications.date = date

            specifications.purchase_way = purchase_way
            specifications.save()
            result['status'] = SUCCESS
            result['msg'] = '添加成功'
         
        elif 'product' in data and 'price' in data and 'number' in data \
            and 'name' in data and 'coin' in data and 'purchase_way' in data:
            # 创建商品规格必需参数：所属商品product，商品单价price，商品数量number，商品名称name，虚拟币价格coin
            product = data['product']
            price = data['price']
            number = data['number']
            name = data['name'].strip()
            coin = data['coin']
            purchase_way = data['purchase_way']

            try:
                product_id = int(product)
                purchase_way = int(purchase_way)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = 'product、purchase_way参数应该为int类型'
                return HttpResponse(json.dumps(result), content_type="application/json")

            try:
                product = Product.objects.get(id = product_id)
            except Product.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未找到该product参数对应的商品'
                return HttpResponse(json.dumps(result), content_type="application/json")

            try:
                price = float(price)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = 'price格式错误'
                return HttpResponse(json.dumps(result), content_type="application/json")

            try:
                number = int(number)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = 'number参数应该为int类型'
                return HttpResponse(json.dumps(result), content_type="application/json")

            if name:
                pass
            else:
                result['status'] = ERROR
                result['msg'] = '商品规格名称name参数不得为空'
                return HttpResponse(json.dumps(result), content_type="application/json")

            try:
                if coin is not None:
                    coin = float(coin)
                else:
                    coin = 0
                               
            except ValueError:
                result['status'] = ERROR
                result['msg'] = 'coin格式错误'
                return HttpResponse(json.dumps(result), content_type="application/json")
            else:
                specifications.coin = coin

            if purchase_way not in Specifications().purchase_way_list():
                result['status'] = ERROR
                result['msg'] = 'purchase_way格式错误'
                return HttpResponse(json.dumps(result), content_type="application/json")
            else:
                specifications.purchase_way = purchase_way

            if 'content' in data:
                content = data['content'].strip()
                if content:
                    specifications.content = content
                else:
                    result['status'] = ERROR
                    result['msg'] = '商品规格说明content参数不得为空'
                    return HttpResponse(json.dumps(result), content_type="application/json")
            
            specifications.product = product
            specifications.price = price
            specifications.number = number
            specifications.name = name
            specifications.save()
            result['status'] = SUCCESS
            result['msg'] = '添加成功'
        else:
            result['status'] = ERROR
            result['msg'] = 'product,price,number,name,coin参数为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

    
    def put(self,request):
        # 修改商品规格
        result = {}

        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST

        if 'id' in data:
            id = data['id']
            try:
                id = int(id)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = 'id参数应该为int类型'
                return HttpResponse(json.dumps(result), content_type="application/json")
            
            try:
                specifications = Specifications.objects.get(id = id)
            except Specifications.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未找到该id参数对应的规格实体'
                return HttpResponse(json.dumps(result), content_type="application/json")

            if 'price' in data:
                price = data['price']
                try:
                    price = float(price)
                except ValueError:
                    result['status'] = ERROR
                    result['msg'] ='规格金额数字格式错误'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                specifications.price = price
            
            if 'date' in data:
                date = data['date']
                try:
                    date = datetime.strptime(date, settings.DATEFORMAT)
                    specifications.date = date
                except ValueError:
                    result['status'] = ERROR
                    result['msg'] = '日期格式错误,应该是yyyy/mm/dd格式'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                

            if 'number' in data:
                number = data['number']
                try:
                    number = int(number)
                except ValueError:
                    result['status'] = ERROR
                    result['msg'] ='number参数应该为int类型'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                specifications.number = number
            
            if 'name' in data:
                name = data['name'].strip()
                if name:
                    specifications.name = name
                else:
                    result['status'] = ERROR
                    result['msg'] ='name参数不能为空'
                    return HttpResponse(json.dumps(result), content_type="application/json")

            if 'coin' in data:
                coin = data['coin']
                try:
                    if coin is not None:
                        coin = float(coin)
                                
                except ValueError:
                    result['status'] = ERROR
                    result['msg'] = 'coin格式错误'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                specifications.coin = coin
            if 'purchase_way' in data:
                purchase_way = data['purchase_way']
                try:
                    purchase_way = int(purchase_way)
                except ValueError:
                    result['status'] = ERROR
                    result['msg'] = 'purchase_way参数应该为int类型'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                if purchase_way not in Specifications().purchase_way_list():
                    result['status'] = ERROR
                    result['msg'] = 'purchase_way格式错误'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                else:
                    specifications.purchase_way = purchase_way

            if 'content' in data:
                content = data['content'].strip()
                if content:
                    specifications.content = content
                else:
                    result['status'] = ERROR
                    result['msg'] = 'content参数不能为空'
                    return HttpResponse(json.dumps(result), content_type="application/json")

            specifications.save()
            result['status'] = SUCCESS
            result['msg'] = '修改成功'
        else:
            result['status'] = ERROR
            result['msg'] = 'id参数为必需参数'  
        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self,request):
        # 删除商品规格
        result = {}

        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST
        return HttpResponse(json.dumps(result), content_type="application/json")

def check_category_exist(name, excluded_id = None):
    if excluded_id:
        return Category.objects.filter(name = name).exclude(id = excluded_id)
    else:
        return Category.objects.filter(name = name)

def get_single_product_dict(product):
    product_dct = {}
    # 商品创建人信息
    product_creator_dct = {}
    product_creator_dct['userid'] = product.user.id
    product_creator_dct['username'] = product.user.username
    product_id = product.id
    # 商品内容描述
    content = product.content
    # 商品图片
    picture = product.picture
    # 商品轮播图
    if product.turns:
        turns = product.turns.split(',')
    else:
        turns = ''
    # 商品标题
    title = product.title
    # 商品类别
    category = product.category.name
    # 商品规格
    specifications = product.product_specifications.all()
    specifications_lst = specifications_infos_lst(specifications)
    product_dct = {
        "id":product_id,
        "creator_info":product_creator_dct,
        "content":content,
        "picture":picture,
        "turns":turns,
        "title":title,
        "category":category,
        "specifications":specifications_lst
    }
    return product_dct
