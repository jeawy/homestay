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
from django.http import HttpResponse

from property import settings 
from property.code import SUCCESS, ERROR 
from gift.models import Gift, Specifications, Category 
import uuid
from tags.comm import add 
from gift.comm import gift_infos_lst, specifications_infos_lst, get_single_gift
logger = getLogger(True, 'gift', False)
 

class GiftAnonymousView(View): 
    def get(self, request):
        # 查看，应该限制在小区范围内
        result = {"status": ERROR}
        if 'uuid' in request.GET:
            # 获得单个礼品的详细信息
            giftuuid = request.GET['uuid'] 
            try:
                gift = Gift.objects.get(uuid = giftuuid) 
                result = { 
                    "status":SUCCESS,
                    "msg":get_single_gift(gift)
                  }
            except Gift.DoesNotExist:
                result = { 
                    "status":ERROR,
                    "msg":"未找到礼品"
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
            gifts = Gift.objects.filter(
                **kwargs).order_by("-date")[page*pagenum: (page+1)*pagenum]
            total = Gift.objects.filter(**kwargs).count()
        else:
            gifts = Gift.objects.filter(
                Q(**kwargs), qfilter).order_by("-date")[page*pagenum: (page+1)*pagenum]
            total = Gift.objects.filter(Q(**kwargs), qfilter).count()
        result['status'] = SUCCESS
        result['msg'] = {
            "list": gift_infos_lst(gifts),
            "total": total,
            "sub" : sub
        } 
        return HttpResponse(json.dumps(result), content_type="application/json")


class GiftView(APIView):
    """
    礼品管理
    """
    def get(self, request):
        #查看礼品
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
                gift__ready = 1,
            ).count()
            isbook = Gift.objects.filter(isbook = 1).count()
            recommend = Gift.objects.filter(recommend = 1).count()
            unready = Gift.objects.filter(ready = 0).count()
            selling = Gift.objects.filter(ready = 1).count()
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
                gift__ready = 1, 
            ).values("gift__uuid", "gift__picture", "gift__title", "number", "name" ))
            result['status'] = SUCCESS
            return HttpResponse(json.dumps(result), content_type='application/json')  

        if 'uuid' in request.GET:
            # 获得单个礼品的详细信息
            giftuuid = request.GET['uuid'] 
            try:
                gift = Gift.objects.get(uuid = giftuuid) 
                result = { 
                    "status":SUCCESS,
                    "msg":get_single_gift(gift)
                  }
            except Gift.DoesNotExist:
                result = { 
                    "status":ERROR,
                    "msg":"未找到礼品"
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
 
        if 'category' in request.GET:
            category = request.GET['category'].strip()
            try:
                category = Category.objects.get(name=category)
                kwargs['category'] = category
            except Category.DoesNotExist:
                result['status'] = SUCCESS
                result['msg'] = '礼品分类不存在'
                return HttpResponse(json.dumps(result), content_type="application/json")

        if 'mine' in request.GET:
            kwargs['user'] = user

        products = Gift.objects.filter(**kwargs) 
        result['status'] = SUCCESS
        result['msg'] = gift_infos_lst(products)

        return HttpResponse(json.dumps(result), content_type="application/json")

    
    def post(self, request):
        # 添加礼品
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

        gift = Gift()
        if 'title' in data and  'content' in data and 'picture' in data and 'category' in data:
            category = data['category'] 
            try:
                category = Category.objects.get(id= category)
                gift.category = category
            except Category.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = "未找到相关类别"
                return HttpResponse(json.dumps(result), content_type="application/json")
                 
            title = data['title']
            content = data['content']
            picture = data['picture']

            if title and content and picture:
                pass
            else:
                result['status'] = ERROR
                result['msg'] = 'title,content,picture参数不能为空'
                return HttpResponse(json.dumps(result), content_type="application/json")
            
            if 'isbook' in data:
                isbook = data['isbook'].strip()
                gift.isbook = isbook 
            
            if 'ready' in data:
                ready = data['ready'].strip()
                gift.ready = ready 

            if 'recommend' in data:
                recommend = data['recommend'].strip()
                gift.recommend = recommend 

            if 'turns' in data:
                turns = data['turns'].strip()
                gift.turns = turns 
            
            if 'gifttype' in data:
                gifttype = data['gifttype'].strip()
                gift.gifttype = gifttype 
            
            if 'cardtype' in data:
                cardtype = data['cardtype'].strip()
                gift.cardtype = cardtype 

             
            gift.user = user
            gift.content = content
            gift.title = title
            gift.picture = picture
            gift.uuid=uuid.uuid4()
            gift.save()
            
            
            if 'specifications' in data:
                """
                parms：price 礼品单价
                parms：number 礼品数量
                parms：name 礼品名称
                parms：coin 礼品虚拟币价格
                parms：content 礼品说明
                specifications数据格式：
                [{"price":100.0, "number":100, "name":'大衣', "coin":100.0, "content":'保暖性能好'},
                {"price":120.0, "number":100, "name":'加绒大衣', "coin":200.0, "content":'保暖性能很好'},
                {"price":150.0, "number":100, "name":'貂皮大衣', "coin":300.0, "content":'保暖性能非常好'}]
                """
                specifications = json.loads(data['specifications'])

                for specification in specifications:
                    # 获取单价
                    ceatePramas = {}
                    try:
                        price = specification['price']
                    except Exception:
                        logger.error(traceback.format_exc())
                        continue
                    else:
                        try:
                            if price is not None:
                                price = float(price)
                                ceatePramas['price'] = price
                        except ValueError:
                            logger.error(traceback.format_exc())
                            continue
                    
                    # 获取数量
                    try:
                        number = specification['number']
                    except Exception:
                        logger.error(traceback.format_exc())
                        continue
                    else:
                        try:
                            number = int(number)
                            ceatePramas['number'] = number
                        except ValueError:
                            logger.error(traceback.format_exc())
                            continue
                    
                    # 获取名称
                    try:
                        name = specification['name']
                        ceatePramas['name'] = name
                    except Exception:
                        logger.error(traceback.format_exc())
                        continue
                    
                    # 获取虚拟币单价
                    try:
                        coin = specification['coin']
                    except Exception:
                        logger.error(traceback.format_exc())
                        continue
                    else:
                        try:
                            if coin is not None:
                               coin = float(coin)
                               ceatePramas['coin'] = coin
                        except ValueError:
                            logger.error(traceback.format_exc())
                            continue
                    
                    # 获取说明
                    try:
                        content = specification['content']
                        ceatePramas['content'] = content
                    except Exception:
                        logger.error(traceback.format_exc())
                        pass
                    try:
                        ceatePramas['gift'] = gift
                        Specifications.objects.create( **ceatePramas)
                    except:
                        result['status'] = ERROR
                        result['msg'] = '该商品已经存在规格'
                        return HttpResponse(json.dumps(result),content_type="application/json")

                    
            result['status'] = SUCCESS
            result['msg'] = '发布成功'
        else:
            result['status'] = ERROR
            result['msg'] = 'content,title,picture为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")
    
    def put(self,request):
        # 修改礼品
        result = {} 
        data = request.POST

        if 'uuid' in data:
            uuid = data['uuid'] 
            try:
                gift = Gift.objects.get(uuid = uuid)
            except Gift.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未能找到该id对应的礼品'
                return HttpResponse(json.dumps(result), content_type="application/json")
            
            if 'title' in data:
                title = data['title'].strip()
                if title:
                    gift.title = title
                else:
                    result['status'] = ERROR
                    result['msg'] = 'title参数不能为空'
                    return HttpResponse(json.dumps(result), content_type="application/json")

            if 'content' in data:
                content = data['content'].strip()
                if content:
                    gift.content = content
                else:
                    result['status'] = ERROR
                    result['msg'] = 'content参数不能为空'
                    return HttpResponse(json.dumps(result), content_type="application/json")

            if 'picture' in data:
                picture = data['picture'].strip()
                if picture:
                    # 删除磁盘中原有的图片文件
                    old_picture = gift.picture
                    try:
                        os.remove(os.path.join(settings.BASE_DIR,old_picture).replace('/','\\'))
                    except IOError:
                        pass

                    gift.picture = picture
                else:
                    result['status'] = ERROR
                    result['msg'] = 'picture参数不能为空'
                    return HttpResponse(json.dumps(result), content_type="application/json")
            
            if 'gifttype' in data:
                gifttype = data['gifttype'].strip()
                gift.gifttype = gifttype 
            
            if 'cardtype' in data:
                cardtype = data['cardtype'].strip()
                gift.cardtype = cardtype 

            if 'turns' in data:
                turns = data['turns'].strip()
                 
                # 删除磁盘中原有的轮播图文件
                new_turns = turns.split(",")
                if gift.turns:
                    old_turns = gift.turns.split(',') 
                    for old_turn in old_turns:
                        if old_turn not in new_turns:
                            try:
                                os.remove(os.path.join(settings.BASE_DIR,old_turn).replace('/','\\'))
                            except IOError:
                                pass
                          
                gift.turns = turns
                 
            if 'isbook' in data:
                isbook = data['isbook'].strip()
                gift.isbook = isbook 
            
            if 'ready' in data:
                ready = data['ready'].strip()
                gift.ready = ready 
                

            if 'recommend' in data:
                recommend = data['recommend'].strip()
                gift.recommend = recommend 

            if 'category' in data:
                category = data['category']
                if category:
                    category = Category.objects.get(id = category)
                    gift.category = category
                 

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
                    if tag not in gift.tags.all():
                        gift.tags.add(tag)

            
            
            if 'specifications' in data:
                """
                parms：price 礼品单价
                parms：number 礼品数量
                parms：name 礼品名称
                parms：coin 礼品虚拟币价格
                parms：content 礼品说明
                specifications数据格式：
                [{"price":100.0, "number":100, "name":'大衣', "coin":100.0, "content":'保暖性能好'},
                {"price":120.0, "number":100, "name":'加绒大衣', "coin":200.0, "content":'保暖性能很好'},
                {"price":150.0, "number":100, "name":'貂皮大衣', "coin":300.0, "content":'保暖性能非常好'}]
                """
                gift.gift_specifications.all().delete()

                specifications = json.loads(data['specifications'])

                for specification in specifications:
                    # 获取单价
                    try:
                        price = specification['price']
                    except Exception:
                        logger.error(traceback.format_exc())
                        continue
                    else:
                        try:
                            price = float(price)
                        except ValueError:
                            logger.error(traceback.format_exc())
                            continue
                    
                    # 获取数量
                    try:
                        number = specification['number']
                    except Exception:
                        logger.error(traceback.format_exc())
                        continue
                    else:
                        try:
                            number = int(number)
                        except ValueError:
                            logger.error(traceback.format_exc())
                            continue
                    
                    # 获取名称
                    try:
                        name = specification['name']
                    except Exception:
                        logger.error(traceback.format_exc())
                        continue
                    
                    # 获取虚拟币单价
                    try:
                        coin = specification['coin']
                    except Exception:
                        logger.error(traceback.format_exc())
                        continue
                    else:
                        try:
                            if coin is not None:
                                coin = float(coin) 
                            else:
                                coin = 0
                        except ValueError:
                            logger.error(traceback.format_exc())
                            continue
                    
                    # 获取说明
                    try:
                        content = specification['content']
                    except Exception:
                        logger.error(traceback.format_exc())
                        pass
                     
                    Specifications.objects.create(gift = gift,number = number, \
                        name = name, price = price, coin = coin, content = content)
                     
            gift.save()
            result['status'] = SUCCESS
            result['msg'] = '修改成功'
        else:
            result['status'] = ERROR
            result['msg'] = 'id参数为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self,request):
        # 删除礼品
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
                    gift = Gift.objects.get(uuid = uuiditem)
                except Gift.DoesNotExist:
                    continue
                else:
                    # 删除礼品时删除磁盘中对应的图片和轮播图文件
                    picture = gift.picture 
                    try:
                        os.remove(os.path.join(settings.BASE_DIR,picture).replace('/','\\'))
                    except IOError:
                        pass

                    if gift.turns:
                        turns = gift.turns.split(',')
                        for turn in turns:
                            try:
                                os.remove(os.path.join(settings.BASE_DIR,turn).replace('/','\\'))
                            except IOError:
                                pass
                    
                    gift.delete()
                    
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
    礼品规格管理
    """ 
    def get(self, request):
        #查看礼品规格
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
        
        # 根据礼品id进行筛选
        elif 'product_id' in request.GET:
            product_id = request.GET['product_id']
            try:
                product_id = int(product_id)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = 'product_id参数应该为int类型'
                return HttpResponse(json.dumps(result), content_type="application/json")
            try:
                gift = Gift.objects.get(id = product_id)
            except Gift.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未找到该product_id参数对应的礼品'
                return HttpResponse(json.dumps(result), content_type="application/json")
            specifications = gift.gift_specifications.all().order_by('-id')
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
        # 添加礼品规格
        result = {}
        kwargs = {}
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

        specifications = Specifications()
        # 创建礼品规格必需参数：所属礼品product，礼品单价price，礼品数量number，礼品名称name，虚拟币价格coin
        if 'gift' in data and 'price' in data and 'number' in data \
            and 'name' in data and 'coin' in data and 'purchase_way' in data:
            gift = data['gift']
            price = data['price']
            number = data['number']
            name = data['name'].strip()
            coin = data['coin']
            purchase_way = data['purchase_way']

            try:
                product_id = int(gift)
                purchase_way = int(purchase_way)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = 'product、purchase_way参数应该为int类型'
                return HttpResponse(json.dumps(result), content_type="application/json")

            try:
                gift = Gift.objects.get(id = product_id)
            except Gift.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未找到该product参数对应的礼品'
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
                result['msg'] = '礼品规格名称name参数不得为空'
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
                    result['msg'] = '礼品规格说明content参数不得为空'
                    return HttpResponse(json.dumps(result), content_type="application/json")
            
            specifications.gift = gift
            specifications.price = price
            specifications.number = number
            specifications.name = name
            specifications.save()
            result['status'] = SUCCESS
            result['msg'] = '添加成功'
        else:
            result['status'] = ERROR
            result['msg'] = 'gift,price,number,name,coin参数为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

    
    def put(self,request):
        # 修改礼品规格
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
        # 删除礼品规格
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

def get_single_product_dict(gift):
    product_dct = {}
    # 礼品创建人信息
    product_creator_dct = {}
    product_creator_dct['userid'] = gift.user.id
    product_creator_dct['username'] = gift.user.username
    product_id = gift.id
    # 礼品内容描述
    content = gift.content
    # 礼品图片
    picture = gift.picture
    # 礼品轮播图
    if gift.turns:
        turns = gift.turns.split(',')
    else:
        turns = ''
    # 礼品标题
    title = gift.title
    # 礼品类别
    category = gift.category.name
    # 礼品规格
    specifications = gift.gift_specifications.all()
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
