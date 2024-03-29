import uuid
from datetime import datetime
import pdb
import time
import json
from category.models import Category
from django.conf import settings
from coupon.comm import get_dict
from django.http import HttpResponse
from django.views import View
from rest_framework.views import APIView
from coupon.models import Coupon
from property.code import SUCCESS, ERROR
from coupon.comm import get_content

 
class CouponAdminView(APIView):
    """
    商户或者平台管理员管理优惠券
    """
    def get(self, request):
        kwargs = {}
        result = {}
        user = request.user

        if not user.is_superuser:
            kwargs['user'] = user
        if 'uuid' in  request.GET:
            couponuuid = request.GET['uuid']
            try:
                coupon = Coupon.objects.get(user = user, uuid = couponuuid) 
                result['status'] = SUCCESS 
                result['msg'] =  get_dict(coupon) 
            except Coupon.DoesNotExist:
                result['msg'] = "优惠券不存在"
                result['status'] = ERROR
            return HttpResponse(json.dumps(result), content_type='application/json')  

        if "name" in request.GET:
            name = request.GET['name']
            kwargs['name__icontains'] = name
          
          
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

        total = Coupon.objects.filter(**kwargs).count() 

        coupons = Coupon.objects.filter(**kwargs) [page*pagenum: (page+1)*pagenum] 
        coupons_ls = []
        for coupon in coupons:
            coupons_ls.append(get_dict(coupon))

        result = {}
        result['status'] = SUCCESS
        result['msg'] = {
                            "total": total,
                            "coupons": coupons_ls
                        }  
        return HttpResponse(json.dumps(result), content_type='application/json')  
    

    def post(self, request):
        data = request.POST
        user = request.user 
        result = {
            "status" :ERROR
        }
        if 'method' in data:
            method = data['method']
            if method == "delete":
                return self.delete(request)
            if method == "put":
                return self.put(request)
        print(data)
        # 创建优惠券
        if 'name' in data and 'coupontype' in data  :
            name = data['name'].strip()
            if len(name) > 56:
                result['msg'] = "标题不能超过28个字"
                return HttpResponse(json.dumps(result), content_type="application/json")
            
            coupontype = data['coupontype']
            if 'time' in data:
                timedata = data['time']
                timedata = timedata.split(",")
                if len(timedata) == 2:
                    print(timedata)
                    start = time.localtime(int(timedata[0])/1000)
                    start = time.strftime("%Y/%m/%d", start)
                    end = time.localtime(int(timedata[1])/1000)
                    end = time.strftime("%Y/%m/%d", end)
                    
                    start = datetime.strptime(start, settings.DATEFORMAT)
                    end = datetime.strptime(end, settings.DATEFORMAT)

                    if end < start:
                        result['msg'] = "截止日期不能小于起始日期"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                else:
                    result['msg'] = "有效期格式错误"
                    return HttpResponse(json.dumps(result), content_type="application/json")
            else:
                result['msg'] = "缺少有效期"
                return HttpResponse(json.dumps(result), content_type="application/json")
            coupon = Coupon()
            coupon.uuid = str(uuid.uuid4())
            coupon.coupontype = coupontype

            coupon.name = name
            coupon.start = start
            coupon.end = end
            coupon.user = user

            if int(coupontype) == Coupon.DISCOUNT:
                # 折扣券
                if 'discount' in data:
                    discount = data['discount']
                    try:
                        if float(discount) < 1 or float(discount) > 9.99:
                            result['msg'] = "折扣量不能小于1或者大于9.99"
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        else:
                            coupon.discount = discount
                    except ValueError:
                        result['msg'] = "折扣量格式错误"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                else:
                    result['msg'] = "请输入折扣量"
                    return HttpResponse(json.dumps(result), content_type="application/json")
            elif int(coupontype) == Coupon.REDUCTION:
                # 满减券
                if 'top_money' in data and 'reduce_money' in data:
                    top_money = data['top_money']
                    reduce_money = data['reduce_money']
                    try:
                        if float(top_money) < float(reduce_money) :
                            result['msg'] = "减免金额过大"
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        else:
                            coupon.top_money = top_money
                            coupon.reduce_money = reduce_money
                    except ValueError:
                        result['msg'] = "满、减金额格式错误"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                else:
                    result['msg'] = "请输入满、减金额"
                    return HttpResponse(json.dumps(result), content_type="application/json")

            
            if 'rules' in data:
                rules = data['rules']
                coupon.rules = rules
            
            if 'limit' in data:
                limit = data['limit']
                coupon.limit = limit
            
            
 
            if 'extras' in data:
                extras = data['extras']
                coupon.extras = extras
            
            if 'status' in data:
                status = data['status']
                coupon.status = status
            
            coupon.save()

            if 'categoryids' in data:
                categoryids = data['categoryids'].split(",")
                for categoryid in categoryids:
                    print(categoryid)
                    if categoryid:
                        try:
                            category = Category.objects.get(id = categoryid)
                            coupon.categories.add(category)
                        except Category.DoesNotExist:
                            pass
                

            result['status'] = SUCCESS
            result['msg'] = "创建成功"
        else:
            result['msg'] = "参数错误"
        return HttpResponse(json.dumps(result), content_type="application/json")
 
    def put(self, request):
        # 修改优惠券，如果已经有购买记录了，那就不支持用户自己修改，只能是超级管理员修改
        data = request.POST
        user = request.user 
        result = {
            "status" : ERROR
        }
        if 'uuid' in data:
            try:
                coupon = Coupon.objects.get(uuid = data['uuid'])
                if not user.is_superuser and coupon.user != user:
                    # 不是自己的优惠券，并且不是超级管理员，则不能修改
                    result['msg'] = "无修改权限" 
                else:
                    if coupon.buyers.count() > 0 and coupon.user == user:
                        # 已有购买用户，不支持自己修改
                        result['msg'] = "已有购买用户，不支持自己修改"
                    else:
                        # 开始修改
                        if 'time' in data:
                            timedata = data['time']
                            timedata = timedata.split(",")
                            if len(timedata) == 2:
                                print(timedata)
                                start = time.localtime(int(timedata[0])/1000)
                                start = time.strftime("%Y/%m/%d", start)
                                end = time.localtime(int(timedata[1])/1000)
                                end = time.strftime("%Y/%m/%d", end)
                                
                                start = datetime.strptime(start, settings.DATEFORMAT)
                                end = datetime.strptime(end, settings.DATEFORMAT)

                                if end < start:
                                    result['msg'] = "截止日期不能小于起始日期"
                                    return HttpResponse(json.dumps(result), content_type="application/json")
                                coupon.start = start
                                coupon.end = end
                            else:
                                result['msg'] = "有效期格式错误"
                                return HttpResponse(json.dumps(result), content_type="application/json")
                        else:
                            result['msg'] = "缺少有效期"
                            return HttpResponse(json.dumps(result), content_type="application/json")

                        if coupon.end < coupon.start:
                            result['msg'] = "截止日期不能小于起始日期"
                            return HttpResponse(json.dumps(result), content_type="application/json")
                        
                        if 'name' in data:
                            name = data['name']
                            coupon.name = name
                            
                        if 'limit' in data:
                            limit = data['limit']
                            coupon.limit = limit
                        
                        if 'status' in data:
                            status = data['status']
                            coupon.status = status

                        if 'categoryids' in data:
                            categoryids = data['categoryids'].split(",")
                            coupon.categories.clear() 
                            for categoryid in categoryids:
                                
                                if categoryid:
                                    print(categoryid)
                                    try:
                                        category = Category.objects.get(id = categoryid)
                                        print(category)
                                        coupon.categories.add(category)
                                    except Category.DoesNotExist:
                                        print(888)
                        if len(name) > 56:
                            result['msg'] = "标题不能超过28个字"
                            return HttpResponse(json.dumps(result), content_type="application/json")
                         
                        if 'coupontype' in data:
                            coupontype = data['coupontype']
                            coupon.coupontype = coupontype
                        
                        if int(coupontype) == Coupon.DISCOUNT:
                            # 折扣券
                            if 'discount' in data:
                                discount = data['discount']
                                try:
                                    if float(discount) < 1 or float(discount) > 9.99:
                                        result['msg'] = "折扣量不能小于1或者大于9.99"
                                        return HttpResponse(json.dumps(result), content_type="application/json")
                                    else:
                                        coupon.discount = discount
                                except ValueError:
                                    result['msg'] = "折扣量格式错误"
                                    return HttpResponse(json.dumps(result), content_type="application/json")
                            
                        elif int(coupontype) == Coupon.REDUCTION:
                            # 满减券
                            if 'top_money' in data and 'reduce_money' in data:
                                top_money = data['top_money']
                                reduce_money = data['reduce_money']
                                try:
                                    if float(top_money) < float(reduce_money) :
                                        result['msg'] = "减免金额过大"
                                        return HttpResponse(json.dumps(result), content_type="application/json")
                                    else:
                                        coupon.top_money = top_money
                                        coupon.reduce_money = reduce_money
                                except ValueError:
                                    result['msg'] = "满、减金额格式错误"
                                    return HttpResponse(json.dumps(result), content_type="application/json")
                              
                        if 'rules' in data:
                            rules = data['rules']
                            coupon.rules = rules
                        
                        if 'extras' in data:
                            extras = data['extras']
                            coupon.extras = extras
                            
                        coupon.save()
                        result['msg'] = "修改成功"
                        result['status'] = SUCCESS
            except Coupon.DoesNotExist:
                result['msg'] = "优惠券不存在"
        else:
            result['msg'] = "缺少必要参数"
        return HttpResponse(json.dumps(result), content_type="application/json")
    
    def delete(self, request):
        # 只能删除自己创建的优惠券，并且只能删除没有任何购买记录的优惠券
        data = request.POST
        user = request.user 
        result = {
            "status" : ERROR
        }
        if 'uuid' in data:
            try:
                coupon = Coupon.objects.get(uuid = data['uuid'])
                if coupon.user == user :
                    if coupon.buyers.count() > 0:
                        # 已经有购买记录，不支持删除
                        result['msg'] = "已经有购买记录，不支持删除"
                    else:
                        coupon.delete()
                        result['status'] = SUCCESS
                        result['msg'] = "删除成功"
                else:
                    # 不能删除别人的优惠券
                    result['msg'] = "无删除权限"
            except Coupon.DoesNotExist:
                result['msg'] = "优惠券不存在"
        else:
            result['msg'] = "缺少必要参数"
        return HttpResponse(json.dumps(result), content_type="application/json")
 