#! -*- coding:utf-8 -*-
import traceback
import json

from django.shortcuts import render
from area.models import Area
from rest_framework.views import APIView 
from django.views.decorators.csrf import csrf_exempt
from common.logutils import getLogger
from django.http import HttpResponse 
from property.code import SUCCESS,ERROR
from common.utils  import verify_phone
from appuser.models import AdaptorUser as User
from .models import Address
from area.comm import get_parent

def address_detail(address):
    address_dct = {}
    address_dct['id'] = address.id
    address_dct['address'] = address.address
    address_dct['detail'] = address.detail
    address_dct['default'] = address.default
    address_dct['phone'] = address.phone
    address_dct['receiver'] = address.receiver 

    user_dct = {}
    user_dct['id'] = address.user.id
    user_dct['name'] = address.user.username
    address_dct['user'] = user_dct
    address_dct['slide_x'] = 0 # 方便前端使用字段
    return address_dct


def address_info_lst(addresses):
    # 获取用户收件地址信息
    address_lst = []
    for address in addresses: 
        address_lst.append(address_detail(address))

    return address_lst


def check_address_default(user, excludedid = None):
    """
    验证默认地址是否存在
    存在返回true
    """
    if excludedid:
        return Address.objects.filter(user = user, default = Address.YES).exclude(id = excludedid)
    else:
        return Address.objects.filter(user = user, default = Address.YES)

logger = getLogger(True, 'address', False)


class AddressView(APIView): 
    def get(self, request):
        """
        查看收货地址
        """
        result = {}
        kwargs = {}
        user = request.user

        if 'id' in request.GET:
            id = request.GET['id'].strip()
            try:
                id = int(id)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = 'id参数应该为int类型'
                return HttpResponse(json.dumps(result), content_type="application/json")
            kwargs['id'] = id
        if 'default' in request.GET:
            # 获取默认地址
            addresses = Address.objects.filter(default=1,user= user) 
            result['status'] = SUCCESS
            if len(addresses ) >0: 
                result['msg'] = address_detail(addresses[0])
            else:
                result['msg'] = {}
            return HttpResponse(json.dumps(result), content_type="application/json")

        kwargs['user'] = user
        addresses = Address.objects.filter(**kwargs).order_by('-default')
        address_lst = address_info_lst(addresses)
        result['status'] = SUCCESS
        result['msg'] = address_lst
        return HttpResponse(json.dumps(result), content_type="application/json")

    def post(self, request):
        """
        创建地址
        """
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

        # 创建Address实例
        address_instance = Address()
        
        # 新建收货地址
        if 'address' in data and 'phone' in data and \
            'receiver' in data and 'detail' in data:
            address = data['address'].strip()
            phone = data['phone'].strip()
            receiver = data['receiver'].strip()
            detail = data['detail'].strip() 
             

            # 验证地址是否为空
            if len(address) == 0:
                result['status'] = ERROR
                result['msg'] = 'address参数不能为空'
                return HttpResponse(json.dumps(result), content_type="application/json")
            else:
                address_instance.address = address

            # 验证手机号码格式
            if verify_phone(phone):
                address_instance.phone = phone
            else:
                result['status'] = ERROR
                result['msg'] = '手机号码格式错误'
                return HttpResponse(json.dumps(result), content_type="application/json")

            # 收件人名称不能为空
            if not receiver:
                result['status'] = ERROR
                result['msg'] = '收件人名称不能为空'
                return HttpResponse(json.dumps(result), content_type="application/json")

            # 若存在默认地址则创建其他地址时自动设置为非默认
            if Address.objects.filter(user = user):
                address_instance.default = Address.NO
            
            if 'default' in data:
                default = data['default']
                try:
                    if int(default) == 1:
                        Address.objects.filter(user = user).update(default = 0)
                    address_instance.default = default
                except ValueError:
                    pass

            address_instance.receiver = receiver
            address_instance.user = user
            address_instance.detail = detail
            address_instance.save()
            
            result['status'] = SUCCESS
            result['msg'] = '保存成功'
        else:
            result['status'] = ERROR
            result['msg'] = 'address与phone为必填参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

    def put(self, request):
        """
        修改收货地址
        """
        result = {}

        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST

        user = request.user

        if 'id' in data:
            id = data['id']
            try:
                id = int(id)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = 'id参数应该为int类型'
                return HttpResponse(json.dumps(result), content_type="application/json")
            try:
                address_instance = Address.objects.get(id = id)
            except Address.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未找到该id对应的地址'
                return HttpResponse(json.dumps(result), content_type="application/json")
            

            if 'address' in data:
                address = data['address'].strip()
                address_instance.address = address
            
            if 'detail' in data:
                detail = data['detail'].strip()
                address_instance.detail = detail 
            
            if 'default' in data:
                default = data['default']
                try:
                    if int(default) == 1:
                        Address.objects.filter(user = user).update(default = 0)
                    address_instance.default = default
                except ValueError:
                    pass

            # 修改收货人
            if 'receiver' in data:
                receiver = data['receiver'].strip()
                if receiver:
                    address_instance.receiver = receiver
                else:
                    result['status'] = ERROR
                    result['msg'] = '收货人名称不能为空'
                    return HttpResponse(json.dumps(result), content_type="application/json")

            if 'phone' in data:
                phone = data['phone'].strip()
                if verify_phone(phone):
                    address_instance.phone = phone
                else:
                    result['status'] = ERROR
                    result['msg'] = '手机号码格式错误'
                    return HttpResponse(json.dumps(result), content_type="application/json")

            if 'default' in data:
                default = data['default'].strip()
                try:
                    default = int(default)
                except ValueError:
                    result['status'] = ERROR
                    result['msg'] = 'default参数应该为int类型'

                if default not in [Address.YES,Address.NO]:
                    result['status'] = ERROR
                    result['msg'] = 'default参数只能为0或1'
                    return HttpResponse(json.dumps(result), content_type="application/json")
                else:
                    # 该用户只有一条收货地址则不可将地址改为非默认
                    if default == Address.NO:
                        address_instance.default = Address.NO
                    else:
                        if check_address_default(user, id):
                            default_address = Address.objects.get(user=user,default=Address.YES)
                            default_address.default = Address.NO
                            default_address.save()

                        address_instance.default = Address.YES
            address_instance.save()
            result['status'] = SUCCESS
            result['msg'] = '修改成功'
        else:
            result['status'] = ERROR
            result['msg'] = '缺少地址id参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self, request):
        """
        删除收货地址
        """
        result = {}
        
        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST
        
        user = request.user

        if 'ids' in data:
            ids = data['ids'].strip()
            ids = ids.split(',')

            try:
                Address.objects.filter(id__in = ids, user = user).delete()
            except:
                logger.error(traceback.format_exc())
                 

            result['status'] = SUCCESS
            result['msg'] = '删除成功'
        else:
            result['status'] = ERROR
            result['msg'] = '缺少ids参数'
        return HttpResponse(json.dumps(result), content_type="application/json")
