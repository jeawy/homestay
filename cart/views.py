import uuid
import json
from django.shortcuts import render
from rest_framework.views import APIView
from cart.models import Cart
from property.code import SUCCESS, ERROR
from django.http import HttpResponse
from gift.models import Specifications


class CartView(APIView):
    def get(self, request):
        #查看购物车
        result = { } 
        user = request.user
        # 价格小于或者等于0的商品不会进入购物车，防止积分加入购物车
        gifts = list(Cart.objects.filter(user = user,spec__price__gt=0 ).values(
            "spec__gift__picture",
            "spec__gift__uuid",
            "spec__id",
            "spec__name",
            "spec__gift__title",
            "spec__price",
            "spec__coin",
            "spec__id",
            "uuid",
            "number" 
        ) )
        for gift in gifts:
            if gift['spec__price'] is not None:
                gift['spec__price'] = float(gift['spec__price'])
            else:
                gift['spec__price'] = 0
        result = { 
            "status":SUCCESS,
            "msg": gifts
            }
         
        return HttpResponse(json.dumps(result), content_type="application/json")
 
    def post(self, request):
        # 添加购物车
        result = {}
        user = request.user 
        data = request.POST 
        
        if 'method' in data:
            method = data['method'].lower()
            if method == 'put':
                return self.put(request)
            elif method == 'delete':
                return self.delete(request)

        
        if 'number' in data and  'specid' in data  :
            specid = data['specid']
            number = data['number'] 
             
            
            try:
                spec = Specifications.objects.get(id = specid)
                cart, created = Cart.objects.get_or_create(user = user, spec = spec)
                if created:
                    cart.user = user
                    cart.uuid  = str(uuid.uuid4())
                    cart.spec  = spec 
                try:
                    number = int(number)
                    
                    if number < 1:
                        result['status'] = ERROR
                        result['msg'] = "数量必须大于1"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    
                    if created:
                        cart.number = number
                    else:
                        cart.number += number
                except ValueError:
                    result['status'] = ERROR
                    result['msg'] = "数量必须是整数"
                    return HttpResponse(json.dumps(result), content_type="application/json")
    
                cart.save() 
                result['status'] = SUCCESS
                result['msg'] = '购物车添加成功'
            except Specifications.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = "未找到相关类别"
                return HttpResponse(json.dumps(result), content_type="application/json")
        elif 'clear' in data:
            # 清空购物车
            Cart.objects.filter(user = user).delete()
            result['status'] = SUCCESS
            result['msg'] = '已清空' 
        else:
            result['status'] = ERROR
            result['msg'] = 'content,title,picture为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")
    
    def put(self,request):
        # 修改购物车
        result = {} 
        data = request.POST

        if 'uuid' in data:
            uuid = data['uuid'] 
            try:
                cart = Cart.objects.get(uuid = uuid)
            except Cart.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未能找到该id对应的购物车'
                return HttpResponse(json.dumps(result), content_type="application/json")
            if 'number' in data:
                number = data['number']
                try:
                    number = int(number)
                    cart.number = number
                    if number < 1:
                        result['status'] = ERROR
                        result['msg'] = "数量必须大于1"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                except ValueError:
                    result['status'] = ERROR
                    result['msg'] = "数量必须是整数"
                    return HttpResponse(json.dumps(result), content_type="application/json")
        
            cart.save()
            result['status'] = SUCCESS
            result['msg'] = '修改成功'
        else:
            result['status'] = ERROR
            result['msg'] = 'id参数为必需参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self,request):
        # 删除购物车
        result = {}

        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST

        if 'uuids' in data:
            uuids = data['uuids']
            uuids = uuids.split(',') 
            Cart.objects.filter(uuid__in = uuids).delete() 
            result['status'] = SUCCESS
            result['msg'] = '删除成功'
        else:
            result['status'] = ERROR
            result['msg'] = '缺少ids参数'
        return HttpResponse(json.dumps(result), content_type="application/json")
