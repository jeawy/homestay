#! -*- coding:utf-8 -*-
import pdb
import json

from django.db.models import Sum 
from rest_framework.views import APIView
from django.http import HttpResponse 
from common.logutils import getLogger
from content.models import   *
from property import settings
from property.code import *
from property.entity import EntityType 
from webcoin.comm import cnum_filter, webcoin_info_lst, check_user
from webcoin.models import WebCoin 
from comment.models import Comment 

logger = getLogger(True, 'webcoin', False)

class WebCoinView(APIView): 
    def get(self, request):
        """
        查看积分
        """
        result = {}
        search_dict = {}
        sum = 0
        user = request.user

        if 'mine' in request.GET:
            """
            查看我的积分
            """
            # 用户id
            if 'id' in request.GET:
                id = request.GET['id']
                content = check_user(id)
                if content['status'] == SUCCESS:
                    webcoins = WebCoin.objects.filter(user=content['user'])
                    for webcoin in webcoins:
                        sum += webcoin.action
                    result['msg'] = sum
                else:
                    return HttpResponse(json.dumps(content), content_type="application/json")
            else:
                webcoins = WebCoin.objects.filter(user=user)
                for webcoin in webcoins:
                    sum += webcoin.action
                result['msg'] = sum

        elif 'number' in request.GET and 'tag' in request.GET:
            """
            积分数量筛选
            """
            tag = request.GET['tag']
            # 用户id
            if 'id' in request.GET:
                id = request.GET['id']
                content = check_user(id)
                if content['status'] == SUCCESS:
                    result = cnum_filter(content['user'], tag)
                else:
                    return HttpResponse(json.dumps(content), content_type="application/json")
            else:
                result = cnum_filter(user, tag)
        
        elif "page" in request.GET and "pagenum" in request.GET and "tag" in request.GET:
            # 用户id
            if 'id' in request.GET:
                id = request.GET['id']
                content = check_user(id)
                if content['status'] == SUCCESS:
                    search_dict['user_id'] = content['user'].id
                else:
                    return HttpResponse(json.dumps(content), content_type="application/json")
            else:
                search_dict['user_id'] = user.id
            pagenum = request.GET['pagenum']
            page = request.GET['page']
            try:
                tag = request.GET['tag']
                tag = int(tag)
                if tag == -1:
                    search_dict['action__lt'] = 0
                elif tag == 1:
                    search_dict['action__gte'] = 0
            except ValueError:
                result['status'] = ERROR
                result['msg'] = 'tag不是int'
                return HttpResponse(json.dumps(result), content_type="application/json")
            try:
                page = int(page) - 1
                pagenum = int(pagenum)
            except ValueError:
                page = 0
                pagenum = settings.PAGE_NUM
            num = WebCoin.objects.filter(**search_dict).count()
            result['count'] = num
            if num % pagenum == 0:
                result['page_count'] = int(num / pagenum)
            else:
                result['page_count'] = int(num / pagenum) + 1

            webcoins = WebCoin.objects.filter(**search_dict)[page * pagenum: (page + 1) * pagenum]
            result['msg'] = webcoin_info_lst(webcoins)
        elif "page" in request.GET and "pagenum" in request.GET and "all" in request.GET:
            pagenum = request.GET['pagenum']
            page = request.GET['page']
            try:
                page = int(page) - 1
                pagenum = int(pagenum)
            except ValueError:
                page = 0
                pagenum = settings.PAGE_NUM
            user_ids = []
            if 'name' in request.GET:
                name = request.GET['name'].strip()
                user_ids = list(User.objects.filter(username__icontains=name).values_list('id', flat=True))
                if not user_ids:
                    result['status'] = ERROR
                    result['msg'] = '搜索的人名不存在'
                    return HttpResponse(json.dumps(result), content_type="application/json")
            if user_ids:
                num = WebCoin.objects.values('user').annotate(sum=Sum('action')).\
                                                    filter(user_id__in=user_ids).count()
            else:
                num = WebCoin.objects.values('user').annotate(sum=Sum('action')).count()
            result['count'] = num
            if num % pagenum == 0:
                result['page_count'] = int(num / pagenum)
            else:
                result['page_count'] = int(num / pagenum) + 1
            if user_ids:
                coins = WebCoin.objects.values('user').annotate(sum=Sum('action')).filter(user_id__in=user_ids).\
                            order_by("-sum")[page * pagenum: (page + 1) * pagenum]
            else:
                coins = WebCoin.objects.values('user').annotate(sum=Sum('action')). \
                            order_by("-sum")[page * pagenum: (page + 1) * pagenum]
            user_list = []
            for coin in coins:
                coin_sum = {}
                coin_sum['user_id'] = coin['user']
                try:
                    username = User.objects.get(id=coin['user']).username
                except User.DoesNotExist:
                    username = ''
                coin_sum['user_name'] = username
                coin_sum['sum'] = coin['sum']
                user_list.append(coin_sum)
            result['status'] = SUCCESS
            result['msg'] = user_list
        else:
            result['status'] = ERROR
            result['msg'] = '参数错误'
            return HttpResponse(json.dumps(result), content_type="application/json")

        result['status'] = SUCCESS
        return HttpResponse(json.dumps(result), content_type="application/json")

    
    def post(self, request):
        """
        添加积分
        """
        result = {}
        user = request.user 
        data = request.POST

        if 'method' in request.POST:
            method = request.POST['method'].lower()
            if method == 'put':
                return self.put(request)
            elif method == 'delete':
                return self.delete(request)
        
        if 'instanceuuid' in data and 'entity' in data and 'action' in data:
            instanceuuid = data['instanceuuid'].strip()
            entity = data['entity'].strip()
            action = data['action'].strip()

            try:
                entity = int(entity) 
                action = int(action)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = 'entity,instance,action参数应该为int类型'
                return HttpResponse(json.dumps(result), content_type="application/json")
            
            
            result['status'] = SUCCESS
            result['msg'] = '添加成功'
        else:
            result['status'] = ERROR
            result['msg'] = 'instance,entity,action为必填参数'
        return HttpResponse(json.dumps(result), content_type="application/json")

    
    def put(self, request):
        """
        修改积分
        """
        result = {}
        return HttpResponse(json.dumps(result), content_type="application/json")
    
    
    def delete(self, request):
        """
        删除积分
        """
        result = {}
        return HttpResponse(json.dumps(result), content_type="application/json")
