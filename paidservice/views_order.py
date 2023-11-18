from datetime import datetime 
from common.logutils import getLogger
import pdb
import json
import uuid
from django.db.models import Q
from community.models import Community
from community.comm import getUserCommunities
from rest_framework.views import APIView
from django.http import HttpResponse 
from property.code import ERROR, SUCCESS
from django.db.models import Sum  
from property.billno import get_paidservice_bill_no 
from django.conf import settings 
from property.code import ZHIFUBAO, WEIXIN 
from paidservice.models import PaidOrder, PaidService 
from common.bills import deleteUnpayedBills
from notice.comm import NoticeMgr
from property.entity import EntityType
logger = getLogger(True, 'paid_order', False)
   
 
class PaidOrderView(APIView):

    def get(self, request):
        # 获取 
        #
        content = {
            "status": SUCCESS,
            "msg": []
        }
        kwargs = {}
        user = request.user

        # 自动删除所有超过一天未支付的订单
        deleteUnpayedBills() 
        
        if 'bills' in request.GET:
            if 'totalmoney' in request.GET:
                # 获取这些订单的总金额, 进入支付页面
                bills = json.loads(request.GET['bills'])
                kwargs['billno__in'] = bills
                kwargs['status'] = PaidOrder.NON_PAYMENT
                kwargs['user'] = user
                content['msg'] = PaidOrder.objects.filter(
                    **kwargs).aggregate(Sum("money"))
                # 重新生成交易号，因为如果这次用的订单号与上次批量支付时用的订单号一致，
                # 支付就没有办法唤起
                neworderno = get_paidservice_bill_no(user)
                PaidOrder.objects.filter(
                    **kwargs).update(out_trade_no = neworderno)
                content['neworderno'] = neworderno
                content['status'] = SUCCESS 
                return HttpResponse(json.dumps(content), content_type="application/json")
                
        if 'subject' in request.GET:
            subject = request.GET['subject']
            kwargs['subject__icontains'] = subject

        if 'billno' in request.GET:
            billno = request.GET['billno']
            kwargs['billno__icontains'] = billno

        if 'username' in request.GET:
            username = request.GET['username']
            kwargs['user__username__icontains'] = username

        
        perm = False 
        if 'tag' in request.GET:
            # 获取本人的订单
            kwargs['user'] = user
        else:
            # 物业获取自己管辖的所有订单
            if 'communityuuids' in request.GET:
                # pc端获取等待完成的服务
                communityuuids = getUserCommunities(user)
                if 'status' in request.GET:
                    status = request.GET['status']
                    if int(status) != -1:
                        kwargs['status'] = status  
                else:
                    kwargs['status'] = PaidOrder.PAYED # 默认获取待完成的订单
                perm = True
                kwargs['community__uuid__in'] = communityuuids
                 
            if 'communityuuid' in request.GET:
                # 验证在当前小区是否有权限
                communityuuid = request.GET['communityuuid']
                try:
                    community = Community.objects.get(uuid = communityuuid)
                    perm = user.has_community_perm("paidservice.paidservice.manage_paidservice", community)
                    if not perm:
                        content = {
                            "status": ERROR,
                            "msg": "权限不足"
                        }
                        return HttpResponse(json.dumps(content), content_type="application/json")
                    else:
                        kwargs['community'] = community
                        
                except Community.DoesNotExist:
                    content = {
                        "status": ERROR,
                        "msg": "未找到对应小区"
                    }
                    return HttpResponse(json.dumps(content), content_type="application/json")
        
        if 'status' in request.GET:
            status = request.GET['status']
            if int(status) != -1:
                kwargs['status'] = status   

        page = 0
        pagenum = settings.PAGE_NUM
        if "page" in request.GET and "pagenum" in request.GET:
            # 分页
            pagenum = request.GET['pagenum']
            page = request.GET['page']
            try:
                page = int(page) - 1
                pagenum = int(pagenum)
            except ValueError:
                pass
         
        if 'keyword' in request.GET:
            keyword = request.GET['keyword'].strip()
            if len(keyword) > 0:
                orders = PaidOrder.objects.filter(**kwargs).filter(
                    Q(subject__icontains=keyword) | Q(billno__icontains=keyword))\
                    .order_by("-date")[page*pagenum: (page+1)*pagenum]
                total = PaidOrder.objects.filter(**kwargs).filter(
                    Q(subject__icontains=keyword) | Q(billno__icontains=keyword)).count()
            else:
                orders = PaidOrder.objects.filter(**kwargs)\
                    .order_by("-date")[page*pagenum: (page+1)*pagenum]
                total = PaidOrder.objects.filter(**kwargs).count()
        else:
            orders = PaidOrder.objects.filter(**kwargs)\
                .order_by("-date")[page*pagenum: (page+1)*pagenum]
            total = PaidOrder.objects.filter(**kwargs).count()
        content['msg'] = {
            "total": total,
            "orders": get_paidservice_orders(orders, perm)
        }
        return HttpResponse(json.dumps(content), content_type="application/json")

    def post(self, request):
        """
        生成订单
        """
        result = {
            'status': ERROR
        }
        user = request.user
        data = request.POST

        if 'method' in data:
            method = data['method'].lower().strip()

            if method == 'delete':  # 删除
                return self.delete(request)
            if method == 'put':  # 删除
                return self.put(request)

        if 'items' in data:
            # 支持批量提交
            items = data['items']
            items = json.loads(items)
            bills = []
            totalmoney = 0
            for item in items:
                # 创建
                paiduuid = item['uuid'].strip()
                num = item['number']
                if int(num) > 0:
                    try:
                        paidservice = PaidService.objects.get(uuid=paiduuid)
                         
                        orderno = get_paidservice_bill_no( user, paidservice.community.organize)

                        money = int(num) * paidservice.money
                        totalmoney += money
                        bills.append(orderno)
                        PaidOrder.objects.create(
                            uuid=uuid.uuid4(),
                            community = paidservice.community,
                            subject=paidservice.title,
                            servicenprice=paidservice.money,
                            servicenunit=paidservice.unit,
                            user=user,
                            feerate = paidservice.community.paidservice_commission_rate, # 当时费率
                            billno=orderno,
                            number=int(num),
                            money=money,
                            out_trade_no = bills[0]
                        )
                         
                    except PaidService.DoesNotExist:
                        result['msg'] = "对应服务不存在"
            if len(bills) == 0:
                result['msg'] = "请选择服务及购买数量"
            else:
                result['status'] = SUCCESS
                result['msg'] = {
                    "bills": bills,
                    "totalmoney": totalmoney
                }
        else:
            result['msg'] = "参数错误，请参考API"
        return HttpResponse(json.dumps(result), content_type="application/json")
    
    def put(self, request):
        # 修改

        result = {}
        data = request.POST
        user = request.user 
        if 'uuid' in data and 'communityuuid' in data:
            # 物业结单
            orderuuid = data['uuid']
            communityuuid = data['communityuuid']
            try:
                order = PaidOrder.objects.get(uuid=orderuuid )
                if order.community.uuid == communityuuid:
                    # 社区uuid匹配，多一步验证 
                    order.status = order.CLOSED
                    order.save()
                    result['status'] = SUCCESS
                    result['msg'] = '已结单'

                    # 发消息给申请人
                    title = "您的有偿服务订单已完成"
                    appurl = "/pages/cart/cart?feetype=1&status=2"
                    NoticeMgr.create(
                        title = title,
                        content = order.subject, 
                        user = order.user,
                        appurl = appurl,
                        entity_type = EntityType.PAIDSERVICE
                    ) 
                else:
                    result['status'] = ERROR
                    result['msg'] = '没有操作权限' 
            except PaidOrder.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未能找到对应订单'
        elif 'uuid' in data :
            # 用户评价
            orderuuid = data['uuid']
            try:
                order = PaidOrder.objects.get(uuid=orderuuid, user = user)
                if 'score' in data:
                    score = data['score'].strip()
                    order.score = score
                    order.save()
                result['status'] = SUCCESS
                result['msg'] = '评价成功'
            except PaidOrder.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '未能找到对应订单' 
        else:
            result['status'] = ERROR
            result['msg'] = '参数错误'
        return HttpResponse(json.dumps(result), content_type="application/json")


    def delete(self, request):
        """
        删除:
        只支持业主删除自己未支付的订单，
        不支持物业删除，
        不支持任何人删除已支付的订单
        """
        result = {
            'status': ERROR,
            'msg': '暂时不支持删除'
        }
        data = request.POST
        user = request.user
        if 'uuids' in data:
            uuids = data['uuids']
            PaidOrder.objects.filter(
                uuid__in=uuids.split(","), user=user).delete()
            result['status'] = SUCCESS
            result['msg'] = '已删除'
        else:
            result['msg'] = 'Need ids in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")
