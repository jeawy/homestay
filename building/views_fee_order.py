#! -*- coding:utf-8 -*-
import json
import pdb
import os
import time
from datetime import datetime
from dateutil.relativedelta import SU, relativedelta
from django.http import HttpResponse
from django.conf import settings
from django.views import View
from common.utils import get_final_date
from pay.wxpayV3 import WeixinPay
from property.code import SUCCESS,  ERROR
from building.comm_fee import fixedfee_calculate, \
                             dynamicfee_calculate, \
                             single_dynamicfee_calculate,\
                               get_bill  
from property.code import ZHIFUBAO, WEIXIN
from building.models import Room, RoomFixedFeeDetail, RoomDynamicFeeDetail, RoomFeeOrders
from community.models import Community
from property.billno import get_fee_bill_no
from rest_framework.views import APIView
from common.logutils import getLogger
from community.comm import getUserCommunities
logger = getLogger(True, 'building_fee_order', False)

from pay.views_alipay import get_alipy_url 
from pay.controller import MainController


class RoomFeeOrderOrgView(APIView):
    """
    物业获得房屋的固定性收费（物业费），非固定性收费等
    """ 
    def get(self, request):
        result = {
            "status": ERROR
        }
        user = request.user
        # 获取用户是哪些小区的员工
        communityuuids = getUserCommunities(user)
         
        if communityuuids is None:
             # 不是任何小区的员工，无法查看任何物业费账单
            result['msg'] = "非物业员工，无权查看账单"
            return HttpResponse(json.dumps(result), content_type="application/json") 

        community = None
        kwargs = {}  
        if 'communityuuids' in request.GET :
            # pc 端首页用到 
            if len(communityuuids) > 1: 
                kwargs['community__uuid__in'] = communityuuids
            elif len(communityuuids) == 1: 
                kwargs['community__uuid'] = communityuuids[0]
             
        elif 'communityuuid' in request.GET:
            communityuuid = request.GET['communityuuid']
            if communityuuid not in communityuuids:
                # 不是这个小区的员工，无权查看
                result['msg'] = "无权查看"
                return HttpResponse(json.dumps(result), content_type="application/json") 
            else:
                kwargs['community__uuid'] = communityuuid
        else:
            result['msg'] = "参数错误，缺少小区信息"
            return HttpResponse(json.dumps(result), content_type="application/json")       

        if 'roomuuid' in request.GET:
            # 物业获取房产的详细账单
            roomuuid = request.GET['roomuuid'] 
            try:
                room = Room.objects.get( uuid = roomuuid, 
                        community__uuid__in = communityuuids)
                final_date = get_final_date()
                bill = get_bill(room, final_date)
                result['status'] = SUCCESS
                result['msg'] = bill
            except Room.DoesNotExist:
                result['msg'] = "无权限查看该小区信息"
            return HttpResponse(json.dumps(result), content_type="application/json")       
        if "building" in request.GET:
            building = request.GET['building']
            kwargs['room__unit__building__name__icontains'] = building
        
        if "unit" in request.GET:
            unit = request.GET['unit']
            kwargs['room__unit__name__icontains'] = unit
        
        if "room" in request.GET:
            room = request.GET['room']
            kwargs['room__name__icontains'] = room
        
        if "billno" in request.GET:
            billno = request.GET['billno']
            kwargs['billno__icontains'] = billno

        if "feename" in request.GET:
            feename = request.GET['feename']
            kwargs['feename__icontains'] = feename
        
        if "username" in request.GET:
            username = request.GET['username']
            kwargs['user__username__icontains'] = username
 
        kwargs['status'] = RoomFeeOrders.PAYED 

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

        total = RoomFeeOrders.objects.filter(**kwargs).count() 

        orders = list(RoomFeeOrders.objects.filter(**kwargs).values(
            "uuid",
            "billno",
            "date","money", "payway","paybillno","community__name","community__uuid",
            "room__name", "room__unit__name", "room__unit__building__name",
            "detail", "feetype", "feename", "start_date", "end_date",
            "status", "remark" ,"feerate","user__username","user__phone"
        )[page*pagenum: (page+1)*pagenum])
        for order in orders:
            order['date'] = time.mktime(order['date'].timetuple())
            order['start_date'] = time.mktime(order['start_date'].timetuple())
            order['end_date'] = time.mktime(order['end_date'].timetuple())

        result['status'] = SUCCESS
        result['msg'] = {
                            "total": total,
                            "orders": orders
                        }  
        return HttpResponse(json.dumps(result), content_type='application/json')  
 

class RoomFeeOrderView(APIView):
    """
    获得房屋的固定性收费（物业费），非固定性收费等
    """ 
    def get(self, request):
        # 业主获取自己的账单
        result = {
            "status": ERROR
        }
        user = request.user
        community = None
        if 'communityuuid' in request.GET:
            communityuuid = request.GET['communityuuid']
            try:
                community = Community.objects.get(uuid=communityuuid)
            except Community.DoesNotExist:
                result['msg'] = "未找到小区信息"
                return HttpResponse(json.dumps(result), content_type="application/json")

            if 'billno' in request.GET:
                # 获取订单总金额
                billno = request.GET['billno']
                try:
                    bill = RoomFeeOrders.objects.get(billno=billno)
                    result['status'] = SUCCESS
                    result['msg'] = bill.money
                except RoomFeeOrders.DoesNotExist:
                    result['msg'] = "未找到订单信息"
                return HttpResponse(json.dumps(result), content_type="application/json")
 
            unpayedbills = True # 获取未支付账单
            if 'status' in request.GET:
                status = request.GET['status']
                if int(status) == 2:
                    # 获取历史缴费账单
                    unpayedbills = False # 
             
            rooms = Room.objects.filter(
                community=community,
                owner=user
            ) 
            if unpayedbills:
                # 只获取自己的账单，一个业主在同一个小区可能有多个房产，同时获取
                 
                final_date = get_final_date()
                roomorders = []
                for room in rooms:
                    roomorders.append(get_bill(room, final_date))
                result['status'] = SUCCESS
                result['msg'] = roomorders
            else:
                # 获取历史缴费账单
                kwargs = {} 
                # 业主查看
                kwargs['room__in'] = rooms
                if 'keyword' in request.GET:
                    keyword = request.GET['keyword'].strip()
                    if len(keyword) > 0:
                        kwargs['billno__icontains'] = keyword

                kwargs['status'] = RoomFeeOrders.PAYED 

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

                total = RoomFeeOrders.objects.filter(**kwargs).count() 

                orders = list(RoomFeeOrders.objects.filter(**kwargs).values(
                    "uuid",
                    "billno",
                    "date","money", "payway","paybillno",
                    "room__name", "room__unit__name", "room__unit__building__name",
                    "detail", "feetype", "feename", "start_date", "end_date",
                    "status", "remark" ,"feerate","user__username","user__phone"
                )[page*pagenum: (page+1)*pagenum])
                for order in orders:
                    order['date'] = time.mktime(order['date'].timetuple())
                    order['start_date'] = time.mktime(order['start_date'].timetuple())
                    order['end_date'] = time.mktime(order['end_date'].timetuple())

                result['status'] = SUCCESS
                result['msg'] = {
                                    "total": total,
                                    "orders": orders
                                }  
                return HttpResponse(json.dumps(result), content_type='application/json')  

        else:
            result['msg'] = "缺少community uuid"
        return HttpResponse(json.dumps(result), content_type="application/json")

    def post(self, request):
        """
        预付物业费、非固定费率时，传递final date，重新计算费用
        """
        result = {
            "status": ERROR
        }
        user = request.user
        data  = request.POST
        if 'roomuuid' in data and 'final_date' in data:
            # 将物业费计费周期更新到final_date
            roomuuid = data['roomuuid']
            
            final_date = data['final_date']  # 时间戳
            final_date = datetime.fromtimestamp(int(final_date)).date()
            try:
                if 'communityuuids' in data:
                    # 物业更新账单
                    communityuuids = getUserCommunities(user)
                    room = Room.objects.get(uuid=roomuuid, community__uuid__in=list(communityuuids))
                else:
                    room = Room.objects.get(owner=user, uuid=roomuuid)
                status, msg = fixedfee_calculate(room, final_date)
                result['status'] = status
                result['msg'] = msg
            except Room.DoesNotExist:
                result['msg'] = "房屋信息不存在"
        elif 'dynamicfeeuuid' in data and 'final_date' in data:
            # 更新物业费非固定费率
            dynamicfeeuuid = data['dynamicfeeuuid']
            final_date = data['final_date']  # 时间戳
            final_date = datetime.fromtimestamp(int(final_date)).date()
            try:
                if 'communityuuids' in data:
                    # 物业更新账单
                    communityuuids = getUserCommunities(user)
                    dynamicdetail = RoomDynamicFeeDetail.objects.get(
                        room__community__uuid__in = list(communityuuids),
                        uuid=dynamicfeeuuid) 
                else: 
                    dynamicdetail = RoomDynamicFeeDetail.objects.get(
                        room__owner = user,
                        uuid=dynamicfeeuuid)
                status, msg = single_dynamicfee_calculate(
                    dynamicdetail, final_date, user)
                result['status'] = status
                result['msg'] = msg
            except Room.DoesNotExist:
                result['msg'] = "房屋信息不存在"
        elif 'roomuuid' in data:
            # 提交物业费订单
            roomuuid = data['roomuuid']
            communityuuid = data['communityuuid']
            try:
                room = Room.objects.get(uuid=roomuuid)
                if room.arrearage_start_date is None:
                    result['msg'] = "起始计费日期未设置"
                    return HttpResponse(json.dumps(result), content_type="application/json")

                if room.arrearage_end_date is None:
                    result['msg'] = "结束计费日期未设置"
                    return HttpResponse(json.dumps(result), content_type="application/json")

                community = room.unit.building.community
                org = community.organize
                detail = room.arrearage_start_date.strftime(
                    settings.DATEFORMAT)
                detail += "至" + \
                    room.arrearage_end_date.strftime(settings.DATEFORMAT)
                detail += "物业费：" + str(room.money) + "元"
                subject = "【{0}】{1}{2}{3}物业费".format(org.alias, room.unit.building.name,
                                                     room.unit.name, room.name)
                billno = get_fee_bill_no(org, user, "F")  # F for 固定性收费
                money = room.arrearage

            except Room.DoesNotExist:
                result['msg'] = "未找到对应房屋信息"
        elif 'dynamicfeeuuid' in data:
            # 提交非固定收费订单 
            result['msg'] = "参数错误"
        elif 'webpay' in data  \
            and 'orderuuid' in data and 'auth_code' in data:
            # auth_code 扫码字符串
            # 物业网页版支付 
            orderuuid = data['orderuuid']
            # 微信支付码规则：18位纯数字，以10、11、12、13、14、15开头 
            # 支付宝支付码规则：25 - 30开头的长度为16~24位的数字，实际字符串长度以开发者获取的付款码长度为准
            auth_code = data['auth_code']
            payway = int(auth_code[:2])

            if payway > 9 and payway < 16:
                payway = WEIXIN
            elif payway <= 30 and payway >= 25:
                payway = ZHIFUBAO
            else:
                result['msg'] = "不支持的付款类型"
                result['status'] = ERROR 
                return HttpResponse(json.dumps(result), content_type="application/json")

            try:
                order = RoomFeeOrders.objects.get(uuid = orderuuid, 
                        status = RoomFeeOrders.NON_PAYMENT)
                if int(payway) == ZHIFUBAO:
                    url = get_alipy_url(order.billno, order.money, order.subject)
                    result['msg'] = { 
                        "payway":payway,
                        "orderno":order.billno
                    } 
                else:
                    # 微信支付
                    """
                    kwargs = {}
                    kwargs["order_id"] = order.billno
                    kwargs["goodsName"] = order.subject
                    kwargs['goodsPrice'] = order.money
                    # 二维码地址
                    # weixinpay_ctl = MainController() 
                    # url = weixinpay_ctl.getWeChatQRCode( **kwargs)
                    """
                    # 直接支付到子商户中
                    kwargs = {}
                    kwargs["order_id"] = order.billno 
                    kwargs['amount'] = order.money
                    kwargs["desc"] = order.subject
                    kwargs['auth_code'] = auth_code
                    sub_mch_id = order.community.wx_sub_mch_id
                    wxpay = WeixinPay(sub_mch_id = sub_mch_id)
                    payresult = wxpay.native_order( **kwargs)
                    logger.debug(str(payresult))
                    
                    result['msg'] = { 
                        "payway":payway, 
                        "orderno":order.billno,
                        "sub_mch_id":sub_mch_id
                    }  
                result['status'] = SUCCESS

            except RoomFeeOrders.DoesNotExist:
                result['msg'] = "未找到该订单"
            
        return HttpResponse(json.dumps(result), content_type="application/json")


class RoomFeeCalculateView(View):

    def post(self, request):
        """
        物业费计算：
        每个季度前5天重置cal_fee_status字段为NOT_CALCALATED未更新
        每个季度5号之后，更新cal_fee_status字段值为未更新的记录

        # 不计算非固定收费， 固定费率手动计算
        """
        result = {
            "status": ERROR
        }
        now = datetime.now()
        CAL_DAY = 5
       

        if now.month == 1 or now.month == 4 or now.month == 7 or now.month == 10:
            if now.day < CAL_DAY:
                # 固定费率每季度更新
                # 重置Room的cal_fee_status为NOT_CALCALATED
                Room.objects.all().update(cal_fee_status=Room.NOT_CALCALATED)
        else:
            # 5天之后，更新收费金额, 每次更新1000条
            rooms = Room.objects.filter(cal_fee_status=Room.NOT_CALCALATED,
                                        area__isnull=False,
                                        fixed_fee__isnull=False,
                                        arrearage_start_date__isnull=False
                                        )[:1000]
            for room in rooms:
                fixedfee_calculate(room)
                dynamicfee_calculate(room)

        return HttpResponse(json.dumps(result), content_type="application/json")
