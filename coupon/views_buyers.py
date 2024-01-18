import time
import pdb
import json
from django.views import View
from datetime import datetime
from rest_framework.views import APIView
from coupon.models import Coupon
from property.code import SUCCESS, ERROR
from django.http import HttpResponse
from category.models import Category
from coupon.comm import get_dict


class CouponBuyerView(APIView):
    def get(self, request):
        #我的优惠券
        user = request.user  
        coupons = Coupon.objects.filter(status = Coupon.PUBLISHED, buyers = user) 
        coupons_ls = []
        for coupon in coupons:
            coupons_ls.append(get_dict(coupon))
        result = {
            "status" :SUCCESS,
            "msg" : coupons_ls
        }
        return HttpResponse(json.dumps(result), content_type="application/json")

    def post(self, request):
        # 领取优惠券
        data = request.POST
        user = request.user 
        result = {
            "status" :ERROR
        } 
        
        # 领取优惠券
        if 'uuid' in data  : 
            couponuuid = data['uuid']
            try:
                coupon = Coupon.objects.get( uuid = couponuuid, status =Coupon.PUBLISHED ) 
                limit = Coupon.objects.filter( uuid = couponuuid, buyers = user).count()
                
                if coupon.limit > limit: # 没有超过领取的上限
                    coupon.buyers.add(user)
                    result['status'] = SUCCESS
                    result['msg'] = "领取成功"
                else:
                    result['msg'] = "最多领取"+ str(coupon.limit) + "张"
            except Coupon.DoesNotExist:  
                result['msg'] = "优惠券不存在"
        else:
            result['msg'] = "参数错误"
        return HttpResponse(json.dumps(result), content_type="application/json")
 

 
class CoupinAnonynousView(View):
    def get(self, request):
        # 匿名获取优惠券
        kwargs = {
            "status" : Coupon.PUBLISHED
        }
        if 'categoryid' in request.GET:
            # 按品类查询优惠券
            categoryid = request.GET['categoryid']
            categories = list(Category.objects.filter(parent__id = categoryid).values(   "id"   ))
            categoryid_ls = set([item['id'] for item in categories])
            categoryid_ls.add(categoryid)
            kwargs['categories__id__in'] = categoryid_ls
        
        print(kwargs)
        coupons = Coupon.objects.filter( **kwargs ).distinct("uuid") 
  
        coupons_ls = []
        for coupon in coupons:
            coupons_ls.append(get_dict(coupon))  

        result = {
            "status" :SUCCESS,
            "msg" : coupons_ls
        }
        return HttpResponse(json.dumps(result), content_type="application/json")


 