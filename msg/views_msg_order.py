from datetime import datetime
from django.contrib.auth.backends import RemoteUserBackend
from common.logutils import getLogger
import pdb
import json
import uuid  
from rest_framework.views import APIView 
from django.http import HttpResponse
from django.views import View
from property.code import ERROR, SUCCESS
from msg.comm_msg import get_orders
from organize.comm import verify_data, get_organize_dict, getUserOrganize
from organize.i18 import *
from organize.models import Organize
from msg.models import MsgOrders, Msg,MsgSpecifications
from community.models import Community
from django.conf import settings 
from property.code import ZHIFUBAO, WEIXIN
from pay.views_alipay import get_alipy_url
from property.billno import get_msg_bill_no
from pay.controller import MainController 
logger = getLogger(True, 'msg_order', False)
 
      
class MsgOrderView(APIView): 

    def get(self, request):
        # 获取短信充值订单列表列表
        # 
        content={
            "status":SUCCESS,
            "msg" : []
        }
        kwargs = {}
        user = request.user
        if not user.is_superuser:  
            print(datetime.now())
            organizeuuids = getUserOrganize(user)
            print(datetime.now())
            kwargs['org__uuid__in'] = organizeuuids
 
        if 'status' in request.GET:
            status = request.GET['status']
            kwargs['status'] = status
        if 'billno' in request.GET:
            billno = request.GET['billno']
            kwargs['billno__icontains'] = billno
        
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
        orders = MsgOrders.objects.filter(**kwargs)\
            .order_by("-date")[page*pagenum : (page+1)*pagenum]
        total =  MsgOrders.objects.filter(**kwargs).count()
        content['msg'] = {
            "total" :total,
            "orders":get_orders(orders)
            } 
        return HttpResponse(json.dumps(content), content_type="application/json") 
    

    def post(self, request):
        """
        订单支付
        """
        result = {
            'status': ERROR
        }
        user = request.user 
        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST
         
        if 'method' in data: 
            method = data['method'].lower().strip()
             
            if method == 'delete':  # 删除
                return self.delete(request)
         
        if 'specificationid' in data and 'dates' in data and\
             'communityuuid' in data and 'num' in data and 'payway' in data:
            # 创建 
            specificationid = data['specificationid'].strip()  
            dates = data['dates'].strip() 
            communityuuid = data['communityuuid'].strip()
            num = data['num'].strip() 
            payway = data['payway'].strip() 
            
            try:
                spc = MsgSpecifications.objects.get(id = specificationid) 
                try:
                    community = Community.objects.get(uuid = communityuuid)
                    # 生成订单号
                    orderno = get_msg_bill_no(community, dates, spc)
                    subject = "【{0}】短信充值订单".format(community.name)
                    MsgOrders.objects.create(
                        org = community.organize,
                        community = community,
                        billno = orderno,
                        total = spc.number * int(num),
                        user = user,
                        payway = payway,
                        number = int(num),
                        spc= spc,
                        money = int(num) * spc.price,
                        subject = subject
                    )
                    # 调用支付宝或者微信，生成跳转连接
                    if int(payway) == ZHIFUBAO:
                        url = get_alipy_url(orderno, int(num) * spc.price, subject)
                    else:
                        # 微信支付 
                        kwargs = {}
                        kwargs["order_id"] = orderno
                        kwargs["goodsName"] = subject
                        kwargs['goodsPrice'] = int(num) * spc.price
                        # 二维码地址
                        weixinpay_ctl = MainController() 
                        url = weixinpay_ctl.getWeChatQRCode( **kwargs)
                    result['status'] = SUCCESS
                    result['msg'] ={
                        "payurl":url,
                        "orderno":orderno
                    }  
                except Community.DoesNotExist:
                    result['msg'] = "对应物业不存在，请刷新后重试" 
            except MsgSpecifications.DoesNotExist:
                result['msg'] = "未找到相关套餐，请刷新后重试"
        else:
            result['msg'] = "参数错误，请参考API" 
        return HttpResponse(json.dumps(result), content_type="application/json")
      
     
    def delete(self, request):
        """
        删除
        """
        result = {
            'status': ERROR,
            'msg': '暂时不支持删除'
        }
        data = request.POST
        user = request.user 
        if 'billnos' in data  :
            billnos = data['billnos']  
            if not user.is_superuser:   
                organizeuuids = getUserOrganize(user)
                MsgOrders.objects.filter(billno__in = billnos.split(","), org__uuid__in = organizeuuids).delete() 
            else:
                MsgOrders.objects.filter(billno__in = billnos.split(",")).delete() 

            result['status'] = SUCCESS
            result['msg'] ='已删除'
        else: 
            result['msg'] ='Need ids in POST'
        
        
        return HttpResponse(json.dumps(result), content_type="application/json")
        
