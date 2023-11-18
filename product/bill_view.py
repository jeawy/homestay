#! -*- coding:utf-8 -*-
import json
import pdb
import time
from django.http import HttpResponse 
from datetime import datetime, timedelta
from address.models import Address

from rest_framework.views import APIView
from common.logutils import getLogger 
from property import settings
from property.code import ERROR, SUCCESS
from product.comm import get_bill_dict, check_number, check_express_company
from product.models import Bill, Product, Specifications
from product.models import PurchaseWay
from product.comm import update_bill_closed
import pandas as pd
logger = getLogger(True, 'product', False)



class BillView(APIView):
    """
    订单功能
    """
    
    def get(self, request):
        """获取订单详情"""
        content = {}
        user = request.user
        search_dict = {}
        page_num = settings.PAGE_NUM
        page = 1

        if 'id' in request.GET:
            id = request.GET['id']
            try:
                id = int(id)
            except ValueError:
                content['status'] = ERROR
                content['msg'] = 'id not int'
                return HttpResponse(json.dumps(content), content_type="application/json")

            try:
                bill = Bill.objects.get(id=id)
                bills = []
                bills.append(bill)
                update_bill_closed(bills)
                content['status'] = SUCCESS
                content['msg'] = get_bill_dict(bill, tag=1)
            except Bill.DoesNotExist:
                content['status'] = ERROR
                content['msg'] = '404 Not found the id'

        elif 'status_num' in request.GET:
            # 查询各个状态订单的数量
            if 'all' in request.GET:
                bills_status = list(Bill.objects.all().values('status'))
            else:
                bills_status = list(Bill.objects.filter(user=user).values('status'))
            if bills_status:
                df = pd.DataFrame(bills_status)
                result = {"0":0,
                          "1":0,
                          "2":0,
                          "3":0,
                          "4":0,
                          }
                for status,group in df.groupby('status'):
                    result[str(status)] = len(group)
                content['status'] = SUCCESS
                content['msg'] = result
                return HttpResponse(json.dumps(content),content_type="application/json")

        elif 'page' in request.GET and 'pagenum' in request.GET:
            if 'page' in request.GET and 'pagenum' in request.GET:
                pass
            
            if 'status_id' in request.GET:
                status_id = request.GET['status_id']
                try:
                    status_id = int(status_id)
                    if status_id not in Bill().get_status_list():
                        content['status'] = ERROR
                        content['msg'] = 'status_id必须为0，1，2，3，4'
                        return HttpResponse(json.dumps(content), content_type="application/json")
                    search_dict['status'] = status_id
                except ValueError:
                    content['status'] = ERROR
                    content['msg'] = 'status_id不是int类型'
                    return HttpResponse(json.dumps(content), content_type="application/json")
            # 按照相关的订单筛选
            if 'all' not in request.GET:
                search_dict['user'] = user
            if 'order_number' in request.GET:
                order_number = request.GET['order_number'].strip()
                search_dict['order_number__icontains'] = order_number
            if 'user' in request.GET:
                user = request.GET['user'].strip()
                search_dict['user__username__icontains'] = user
            # 商品内容筛选
            if 'content' in request.GET:
                spe_content = request.GET['content'].strip()
                search_dict['specifications__content__icontains'] = spe_content
            # 根据开始日期进行筛选
            if 'start' in request.GET:
                start = request.GET['start'].strip()
                start_date = datetime.strptime(start, settings.DATEFORMAT).date()
                search_dict['date__gte'] = start_date
            # 根据结束日期进行筛选
            if 'end' in request.GET:
                end = request.GET['end'].strip()
                end_date = (datetime.strptime(end , settings.DATEFORMAT) + timedelta(days=1)).date()
                search_dict['date__lte'] = end_date
            
            try:
                page = int(page) - 1
                pagenum = int(pagenum)
            except ValueError:
                page = 0
                pagenum = settings.PAGE_NUM
            num = Bill.objects.filter(**search_dict).count()
            content['count'] = num
            if num % pagenum == 0:
                content['page_count'] = int(num / pagenum)
            else:
                content['page_count'] = int(num / pagenum) + 1
            bills = Bill.objects.filter(**search_dict). \
                        order_by("-date")[page * pagenum: (page + 1) * pagenum]
            content['status'] = SUCCESS
            content['msg'] = get_bill_dict(bills,tag=0)
            return HttpResponse(json.dumps(content), content_type="application/json")

        # 返回我的所有订单
        else:
            bills = Bill.objects.filter(user=user)
            # 筛选出我的订单中未支付中的订单计算时间是否过期
            uncloesd_bills = bills.filter(status=Bill.NON_PAYMENT)
            if uncloesd_bills:
                update_bill_closed(uncloesd_bills)
            content['status'] = SUCCESS
            content['msg'] = get_bill_dict(bills, tag=0)

        return HttpResponse(json.dumps(content), content_type="application/json")

    
    def post(self, request):
        """
        创建
        """
        result = {}
        user = request.user
        bill = Bill()
        if len(request.POST) == 0:
            request.POST = request.data
        if 'method' in request.POST:
            method = request.POST['method'].lower()
            if method == 'put':  # 修改
                return self.put(request)
            elif method == 'delete':  # 删除
                return self.delete(request)

        # 新建
        if 'goods_id' in request.POST and 'number' in request.POST \
             and 'address_id' in request.POST and 'purchase_way' in request.POST:
            # 数量
            number = request.POST['number'].strip()
            # 商品规格id
            goods_id = request.POST['goods_id'].strip()
            # 收货地址
            address_id = request.POST['address_id'].strip()
            # 购买方式
            purchase_way = request.POST['purchase_way'].strip()

            # 下订单前先扫描一遍订单表 看有那些事未支付需要修改为 关闭
            bills = Bill.objects.filter(status = Bill.NON_PAYMENT)
            update_bill_closed(bills)

            # 购买的数量和方式
            try:
                number = int(number)
                purchase_way = int(purchase_way)
            except ValueError:
                result['status'] = ERROR
                result['msg'] ='purchase_way、number格式错误'
                return HttpResponse(json.dumps(result), content_type="application/json")
            else:
                bill.number = number


            try:
                specifications_id = int(goods_id)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = 'specifications_id应该为int类型'
                return HttpResponse(json.dumps(result), content_type="application/json")

            try:
                spec = Specifications.objects.get(id=goods_id)
            except Specifications.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未找到该specifications_id参数对应的礼品规格'
                return HttpResponse(json.dumps(result), content_type="application/json")
            else:
                bill.specifications = spec

            # 礼品数量判断
            if number <= int(spec.number):
                # 订单数量会影响礼品表中的库存，因为现在定时没有做，所以说库存现在有些问题
                spec.number = spec.number - number
                spec.save()
                bill.number = number
            else:
                result['status'] = ERROR
                result['msg'] = '订单数量超过礼品数量'
                return HttpResponse(json.dumps(result), content_type="application/json")

            try:
                address_id = int(address_id)
                address = Address.objects.get(id=address_id)
                bill.address = address
            except Address.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '找不到收货地址id'
                return HttpResponse(json.dumps(result), content_type="application/json")
            else:
                bill.address = address

            # # 金额 = 商品单价*数量
            # money = spec.price*number
            # bill.money = money

            # PurchaseWay.objects. \
            #     filter(goods_id=spec.product). \
            #     values('purchase_way', 'coin', 'cash', 'coin_cash')
            if purchase_way not in Specifications().purchase_way_list():
                result['status'] = ERROR
                result['msg'] = 'purchase_way购买方式不支持'
                return HttpResponse(json.dumps(result), content_type="application/json")

            # 现金
            if purchase_way == Specifications.CASH:
                bill.money = spec.price * number
            # 积分
            if purchase_way == Specifications.COIN:
                bill.coin = spec.coin * number
            # 积分+现金
            if purchase_way == Specifications.CASH_AND_COIN:
                if 'coin_cash' in request.POST:
                    coin_cash = request.POST['coin_cash']
                    coin_cash_list = coin_cash.split(',')
                    try:
                        coin = coin_cash_list[0]
                        cash = coin_cash_list[1]
                    except:
                        result['status'] = ERROR
                        result['msg'] = "需要传递现金和积分，中间按照，隔开"
                        return HttpResponse(json.dumps(result), content_type="application/json")

                    # 验证现金
                    try:
                        cash = float(cash)
                    except ValueError:
                        result['status'] = ERROR
                        result['msg'] = '现金必须为float类型'
                        return HttpResponse(json.dumps(result), content_type="application/json")

                    # 验证积分
                    try:
                        coin = int(coin)
                    except ValueError:
                        result['status'] = ERROR
                        result['msg'] = '积分必须为int类型'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    coin_int = int(coin) * number
                    cash_float = float(cash) * number
                    bill.coin_money = str(coin_int) + ',' + str(cash_float)
                else:
                    result['status'] = ERROR
                    result['msg'] = '订单数量超过礼品数量'
                    return HttpResponse(json.dumps(result), content_type="application/json")


            # 订单号--时间+用户+商品id
            now = datetime.now()
            DATETIMEFORMAT = "%Y%m%d%H%M%S"        #datetime转str后的格式
            now_str = now.strftime(DATETIMEFORMAT)
            order_num = now_str + str(user.id) + str(specifications_id)
            bill.order_number = order_num

            bill.user = user
            bill.save()

            result['status'] = SUCCESS
            result['msg'] = '创建成功'
            result['bill_id'] = bill.id
        else:
            result['status'] = ERROR
            result['msg'] = 'Need goods_id, number, address_id in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")

    # 定时更新；快递信息收集方式？
    def put(self, request):
        """
        更新快递信息
        """
        result = {}
        user = request.user

        data = request.POST
        if 'id' in data:
            id = data['id']
            try:
                bill = Bill.objects.get(id=id)
                # 快递单号
                if 'express_number' in data:
                    express_number = data['express_number'].strip()
                    result = check_number(express_number)
                    if result['status'] != SUCCESS:
                        result['status'] = ERROR
                        result['msg'] = 'express_number长度错误'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    bill.express_number = express_number

                # 快递公司
                if 'express_company' in data:
                    express_company = data['express_company'].strip()
                    result = check_express_company(express_company)
                    if result['status'] != SUCCESS:
                        result['status'] = ERROR
                        result['msg'] = 'express_company长度错误'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    bill.express_company = express_company

                # 将订单状态改为待收货
                bill.status = Bill.DELIVERING
                bill.save()

                result['status'] = SUCCESS
                result['msg'] ='更新成功'
            except Bill.DoesNotExist:
                result['status'] = ERROR
                result['msg'] ='找不到订单id'
        else:
            result['status'] = ERROR
            result['msg'] ='需要订单id'

        return HttpResponse(json.dumps(result), content_type="application/json")

    # 删除订单
    def delete(self,request):
        result = {}
        data = request.POST
        if 'bill_ids' in data:
            bill_ids = data['bill_ids']
            bill_ids = bill_ids.split(',')
            bill = Bill.objects.filter(id__in = bill_ids)
            if bill:
                bill.delete()
                result['status'] = SUCCESS
                result['msg'] = "删除订单成功"
            else:
                result['status'] = ERROR
                result['msg'] = '没有找到要删除的订单'
            return HttpResponse(json.dumps(result),content_type="application/json")


# class BillCoinView(APIView):
#     # 通过积分下订单
#     def post(self,request):
#         result = {}
#         data = request.POST
#         bill = Bill()
#         # 新建订单
#         if 'address_id' in data \
#                 in data and 'goods_id' in data:
#             # 数量
#             number = data['number'].strip()
#             # 商品id
#             goods_id = data['goods_id'].strip()
#             # 收货地址
#             address_id = data['address_id'].strip()
#
#             # 购买的数量
#             try:
#                 number = int(number)
#             except ValueError:
#                 result['status'] = ERROR
#                 result['msg'] = 'number格式错误'
#                 return HttpResponse(json.dumps(result), content_type="application/json")
#             else:
#                 bill.number = number
#
#             try:
#                 specifications_id = int(goods_id)
#             except ValueError:
#                 result['status'] = ERROR
#                 result['msg'] = 'specifications_id应该为int类型'
#                 return HttpResponse(json.dumps(result), content_type="application/json")
#
#             try:
#                 # 礼品表
#                 product = Product.objects.get(id=goods_id)
#             except Product.DoesNotExist:
#                 result['status'] = ERROR
#                 result['msg'] = '未找到该specifications_id参数对应的礼品规格'
#                 return HttpResponse(json.dumps(result), content_type="application/json")
#             else:
#                 bill.Product = spec
#
#             # 礼品数量判断
#             if number <= int(spec.number):
#                 # 订单数量会影响礼品表中的库存，因为现在定时没有做，所以说库存现在有些问题
#                 spec.number = spec.number - number
#                 spec.save()
#                 bill.number = number
#             else:
#                 result['status'] = ERROR
#                 result['msg'] = '订单数量超过礼品数量'
#                 return HttpResponse(json.dumps(result), content_type="application/json")
#
#             try:
#                 address_id = int(address_id)
#                 address = Address.objects.get(id=address_id)
#                 bill.address = address
#             except Address.DoesNotExist:
#                 result['status'] = ERROR
#                 result['msg'] = '找不到收货地址id'
#                 return HttpResponse(json.dumps(result), content_type="application/json")
#             else:
#                 bill.address = address
#
#             # 金额 = 商品单价*数量
#             money = spec.price * number
#             bill.money = money
#
#             # 订单号--时间+用户+商品id
#             now = datetime.datetime.now()
#             DATETIMEFORMAT = "%Y%m%d%H%M%S"  # datetime转str后的格式
#             now_str = now.strftime(DATETIMEFORMAT)
#             order_num = now_str + str(user.id) + str(specifications_id)
#             bill.order_number = order_num
#
#             bill.user = user
#             bill.save()
#
#             result['status'] = SUCCESS
#             result['msg'] = '创建成功'
#             result['bill_id'] = bill.id
#         else:
#             result['status'] = ERROR
#             result['msg'] = 'Need product_id, number, money, way and order_number address_id in POST'
#
#         return HttpResponse(json.dumps(result), content_type="application/json")
#
#     def delete(self,request):
#         # 删除订单
#         pass