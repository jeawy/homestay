import time
import pdb
import json
from django.views import View
from datetime import datetime
from rest_framework.views import APIView
from coupon.models import Coupon
from property.code import SUCCESS, ERROR
from django.http import HttpResponse


class CouponBuyerView(APIView):
    def get(self, request):
        #我的优惠券
        user = request.user  
        coupons = Coupon.objects.filter(status = Coupon.PUBLISHED, buyers = user).values(
            "uuid", "name", "coupontype", "start", "end", "rules", "discount", 
            "top_money", "reduce_money", "limit"
        )
        for coupon in coupons:
            if coupon['start']:
                coupon['start'] =  time.mktime(coupon['start'].timetuple())
            
            if coupon['end']:
                coupon['end'] =  time.mktime(coupon['end'].timetuple())
        result = {
            "status" :SUCCESS,
            "msg" : list(coupons)
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
        
        coupons = Coupon.objects.filter(status = Coupon.PUBLISHED).values(
            "uuid", "name", "coupontype", "start", "end", "rules", "discount", 
            "top_money", "reduce_money", "limit"
        )
        for coupon in coupons:
            if coupon['start']:
                coupon['start'] =  time.mktime(coupon['start'].timetuple())
            
            if coupon['end']:
                coupon['end'] =  time.mktime(coupon['end'].timetuple())
        result = {
            "status" :SUCCESS,
            "msg" : list(coupons)
        }
        return HttpResponse(json.dumps(result), content_type="application/json")


 