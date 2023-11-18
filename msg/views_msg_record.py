 
from common.logutils import getLogger
import pdb
import json
import uuid
from rest_framework.views import APIView
from django.http import HttpResponse 
from django.db.models import Sum
from property.code import ERROR, SUCCESS
from organize.comm import verify_data, get_organize_dict, get_organize_detail, getUserOrganize
from organize.i18 import *
from organize.models import Organize 
from msg.models import MsgOrders
from django.conf import settings 

logger = getLogger(True, 'msg', False)
 
class OrganizeRecordView(APIView):

    def get(self, request): 
        #
        content = {
            "status": SUCCESS,
            "msg": []
        }
        kwargs = {}
        user = request.user
        if 'count' in request.GET:
            # 获取各个小区短信剩余数量
            if user.is_superuser:
                msgCount = MsgOrders.objects.filter(status=MsgOrders.PAYED).values("org__uuid").annotate(tatol_count=Sum("left"))
            else:
                orguuids = getUserOrganize(user)
                msgCount = MsgOrders.objects.filter(org__uuid__in=orguuids,
                                                    status=MsgOrders.PAYED).values("org__uuid").annotate(tatol_count=Sum("left"))
            msgCount_ls = []
            for item in msgCount:
                item_dict = {}
                item_dict['uuid'] = item['org__uuid']
                item_dict['tatol_count'] = item['tatol_count']
                msgCount_ls.append(item_dict)
            content['msg'] = msgCount_ls
            return HttpResponse(json.dumps(content), content_type="application/json")
        if 'name' in request.GET:
            name = request.GET['name']
            kwargs['name__icontains'] = name

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
        organizes = Organize.objects.filter(**kwargs)\
            .order_by("-date")[page*pagenum: (page+1)*pagenum]
        total = Organize.objects.filter(**kwargs).count()
        content['msg'] = {
            "total": total,
            "organizes": get_organize_dict(organizes)
        }
        return HttpResponse(json.dumps(content), content_type="application/json")

    def post(self, request):
        """ 
        发送短信
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
            if method == 'put':  # 修改
                return self.put(request)
            if method == 'delete':  # 删除
                return self.delete(request)
         
        if 'name' in data:
            # 创建
            pass
        else:
            result['status'] = ERROR
            result['msg'] = "确实name字段"
        return HttpResponse(json.dumps(result), content_type="application/json")

     
