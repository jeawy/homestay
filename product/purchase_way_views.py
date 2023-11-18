from product.models import PurchaseWay
import json
import pdb
import datetime
from django.http import HttpResponse


from product.models import Product
from rest_framework.views import APIView
from common.logutils import getLogger
from property.code import ERROR, SUCCESS 
from product.models import PurchaseWay

logger = getLogger(True, 'purchase_way', False)
 
def sing_goods_ways(goods_id):
    # 筛选出单个商品的购买方式
    purchase_ways = list(PurchaseWay.objects.filter(goods__id=goods_id) \
                         .values('goods_id','goods__title', 'goods__content', 'goods__picture',
                        'purchase_way','coin', 'cash','coin_cash', 'qualification_id'))

    purchase_way = purchase_ways[0]
    if purchase_way['qualification_id']:
        # 根据qualification_id筛选出type和ranking
        try:
            rule = QualificationRule.objects.get(id=purchase_way['qualification_id'])
            purchase_way['type'] = rule.type
            purchase_way['ranking'] = rule.ranking
        except:
            purchase_way['qualification_id'] = None
            purchase_way['type'] = None
            purchase_way['ranking'] = None
    else:
        purchase_way['type'] = None
        purchase_way['ranking'] = None
    # 返回json
    return purchase_way

class PurchaseWayView(APIView):
    """商品的购买方式管理"""

    def post(self,request):
        """创建商品的购买方式"""

        result = {}
        content = {}
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

        if 'goods_id' in data and 'purchase_way' in data:

            goods_id = data['goods_id']
            purchase_way = data['purchase_way']
            try:
                goods_id = int(goods_id)
                goods = Product.objects.get(id = goods_id)
                content['goods'] = goods
            except:
                result['status'] = ERROR
                result['msg'] = "通过goods_id没有找到商品"
                return HttpResponse(json.dumps(result),content_type="application/json")

            purchase_way_list = purchase_way.split(',')  #['1','2']
            ways = PurchaseWay().purchase_way_list()
            ret = set(purchase_way_list).issubset(set(ways))
            if not ret:
                result['status'] = ERROR
                result['msg'] = "购买方式必须是积分，现金，积分加现金，资格中的一种或多种"
                return HttpResponse(json.dumps(result),content_type="application/json")
            else:
                content['purchase_way'] = purchase_way
            # 创建积分的购买方式
            if str(PurchaseWay.COIN) in purchase_way:
                if 'coin' in data  :
                    coin = data['coin']
                    try:
                        coin = int(coin)
                    except:
                        result['status'] = ERROR
                        result['msg'] = '积分必须为int类型'
                        return HttpResponse(json.dumps(result),content_type="application/json")
                    else:
                        content['coin'] = coin
                else:
                    result['status'] = ERROR
                    result['msg'] = "创建了该商品可以积分支付，但是没有说明多少积分能够购买"
                    return HttpResponse(json.dumps(result),content_type="application/json")


            # 创建现金的购买方式
            if str(PurchaseWay.CASH) in purchase_way:
                if 'cash' in data  :
                    cash = data['cash']
                    try:
                        cash = float(cash)
                    except:
                        result['status'] = ERROR
                        result['msg'] = '现金必须为float类型'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    else:
                        content['cash'] = cash
                else:
                    result['status'] = ERROR
                    result['msg'] = "创建了该商品可以现金支付，但是没有说明多少现金能够购买"
                    return HttpResponse(json.dumps(result),content_type="application/json")

            # 创建现金+积分的购买方式
            if str(PurchaseWay.CASH_AND_COIN) in purchase_way:
                if 'coin_cash' in data :
                    coin_cash = data['coin_cash']
                    coin_cash_list = coin_cash.split(',')
                    try:
                        coin = coin_cash_list[0]
                        cash = coin_cash_list[1]
                    except:
                        result['status'] = ERROR
                        result['msg'] = "需要传递现金和积分，中间按照，隔开"
                        return HttpResponse(json.dumps(result),content_type="application/json")

                    # 验证现金
                    try:
                        cash = float(cash)
                    except:
                        result['status'] = ERROR
                        result['msg'] = '现金必须为float类型'
                        return HttpResponse(json.dumps(result), content_type="application/json")

                    # 验证积分
                    try:
                        coin = float(coin)
                    except:
                        result['status'] = ERROR
                        result['msg'] = '积分必须为int类型'
                        return HttpResponse(json.dumps(result), content_type="application/json")

                    content['coin_cash'] = coin_cash
                else:
                    result['status'] = ERROR
                    result['msg'] = "创建了该商品可以积分+现金支付，但是没有说明多少积分+现金能够购买"
                    return HttpResponse(json.dumps(result), content_type="application/json")

            # 创建资格的购买方式
            if str(PurchaseWay.QUALIFICATION) in purchase_way:
                if 'qualification_id' in data:
                    qualification_id = data['qualification_id']
                    try:
                        qualification_id = int(qualification_id)
                        qualification = QualificationRule.objects.get(id = qualification_id)
                    except:
                        result['status'] = ERROR
                        result['msg'] = '资格id未找到'
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    else:
                        content['qualification_id'] = qualification_id
                else:
                    result['status'] = ERROR
                    result['msg'] = "创建了该商品可以资格购买，但是没有说明什么资格能够购买"
                    return HttpResponse(json.dumps(result), content_type="application/json")

            # 所有验证完都没有问题，创建一条记录
            # 因为每天商品只有一个购买方式，如果之前有这条记录删除
            PurchaseWay.objects.filter(goods = goods).delete()
            PurchaseWay.objects.create(**content)
            result['status'] = SUCCESS
            result['msg'] = "成功创建一条商品的购买方式记录"
            return HttpResponse(json.dumps(result),content_type="application/json")
        else:
            result['status'] = ERROR
            result['msg'] = "请提供商品id和购买方式"
            return HttpResponse(json.dumps(result),content_type="application/json")


    def get(self,request):
        """查询商品的购买方式"""

        result = {}

        if 'goods_id' in request.GET:
            goods_id = request.GET['goods_id']
            try:
                goods_id = int(goods_id)
                goods = Product.objects.get(id = goods_id)
            except:
                result['status'] = ERROR
                result['msg'] = "没有找到该商品"
                return HttpResponse(json.dumps(result),content_type="application/json")
            purchase_way = sing_goods_ways(goods_id)


            result['status'] = SUCCESS
            result['msg'] = purchase_way
            return HttpResponse(json.dumps(result),content_type="application/json")

        else:
            # 返回所有的商品的购买方式
            purchase_ways = list(PurchaseWay.objects.all().values('goods_id','goods__title', 'goods__content',
                            'goods__picture', 'purchase_way','coin',
                            'cash', 'coin_cash','qualification_id'))
            for purchase_way in purchase_ways:
                # 如果资格不为空
                qualification_id = purchase_way['qualification_id']
                if qualification_id:
                    # 查询该资格对应的资格的type和ranking
                    try:
                        # 根绝规则id 找规则
                        rule = QualificationRule.objects.get(id = qualification_id)
                        purchase_way['type'] =rule.type
                        purchase_way['ranking'] = rule.ranking
                    except:
                        purchase_way['type'] = None
                        purchase_way['ranking'] = None
                else:
                    purchase_way['type'] = None
                    purchase_way['ranking'] = None

            result['status'] = SUCCESS
            result['msg'] = purchase_ways
            return HttpResponse(json.dumps(result),content_type="application/json")


    def put(self,request):
        """修改商品的购买方式"""
        result = {}
        # 修改和创建可以用同一个接口

    def delete(self,request):
        """删除商品的购买方式"""
        result = {}
        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST
        if 'goods_id' in data:
            goods_id = data['goods_id']
            try:
                goods_id = int(goods_id)
                product = Product.objects.get(id = goods_id)
            except:
                result['status'] = ERROR
                result['msg'] = "请提供正确的要删除的商品id"
                return HttpResponse(json.dumps(result),content_type="application/json")
            PurchaseWay.objects.filter(goods_id = goods_id).delete()
            result['status'] = SUCCESS
            result['msg'] = "删除成功"
            return HttpResponse(json.dumps(result),content_type="application/json")
