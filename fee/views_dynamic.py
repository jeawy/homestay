from appuser.models import AdaptorUser as User
from django.conf import settings
from fee.models import FixedFee, DynamicFee, FixedItemFee
from django.contrib.auth.backends import RemoteUserBackend
from common.logutils import getLogger
import pdb
import json
import uuid
from community.models import Community
from rest_framework.views import APIView
from django.http import HttpResponse
from django.views import View
from property.code import ERROR, SUCCESS
from fee.comm import verify_dynamic_data
from fee.comm import verify_dynamic_name_exist, get_dynamic_fees_dict

logger = getLogger(True, 'fee', False)


class DynamicFeeView(APIView):

    def get(self, request):
        # 获取DynamicFees列表
        #
        content = {
            "status": SUCCESS,
            "msg": []
        } 
        if 'communityuuid' in request.GET:
            # 获取详情
            communityuuid = request.GET['communityuuid'] 
            fees = DynamicFee.objects.filter(community__uuid=communityuuid)
            content['msg'] = get_dynamic_fees_dict(fees) 
            content['status'] = SUCCESS 
        else:
            content['msg'] = "缺少community uuid"
 
        return HttpResponse(json.dumps(content), content_type="application/json")

    def post(self, request):
        """
        创建动态收费项目

        """
        result = {
            'status': ERROR
        }
        user = request.user
        
        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST

        community = None
        if 'communityuuid' not in data:
            result['msg'] = "缺少 community uuid"
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            communityuuid = data['communityuuid']
            try:
                community = Community.objects.get(uuid=communityuuid)
                if not user.has_community_perm("fee.fixedfee.manage_fee", community):
                    return HttpResponse('Unauthorized', status=401)
            except Community.DoesNotExist:
                result['msg'] = "Community Not Exist"
                return HttpResponse(json.dumps(result), content_type="application/json")

        if 'method' in data:
            method = data['method'].lower().strip()
            if method == 'put':  # 修改
                return self.put(request, community)
            if method == 'delete':  # 删除
                return self.delete(request, community)

        if 'name' in data and 'money' in data and 'feetype' in data:
            # 创建
            verify_result = verify_dynamic_data(data)
            if verify_result[0] == ERROR:
                # 验证失败
                result['status'] = ERROR
                result['msg'] = verify_result[1]
                return HttpResponse(json.dumps(result), content_type="application/json")
             
            fee = DynamicFee()
            name = data['name'].strip()
            if  verify_dynamic_name_exist(name, community):
                result['msg'] = "收费项名称已存在"
                return HttpResponse(json.dumps(result), content_type="application/json")
            money = data['money'].strip()
            feetype = data['feetype'].strip()
            fee.name = name
            fee.money = money
            fee.community = community
            fee.feetype = feetype
            fee.uuid = uuid.uuid4()
  
            fee.save()
            result['status'] = SUCCESS
            result['msg'] =  str(fee.uuid)

            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = ERROR
            result['msg'] = "缺少参数name, money, feetype"
        return HttpResponse(json.dumps(result), content_type="application/json")

    def put(self, request, community):
        """
        编辑 
        """
        result = {
            'status': ERROR,
            'msg': ''
        }
        # 处理前端发送数据
        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST
        verify_result = verify_dynamic_data(data)
        if verify_result[0] == ERROR:
            # 验证失败 
            result['msg'] = verify_result[1]
            return HttpResponse(json.dumps(result), content_type="application/json")

        if 'uuid' in data:
            feeuuid = data['uuid'].strip()
            try:
                fee = DynamicFee.objects.get(uuid=feeuuid)

                if 'name' in data:
                    name = data['name'].strip()
                    if verify_dynamic_name_exist(name, community, feeuuid):
                        result['msg'] = "收费项名称已存在"
                        return HttpResponse(json.dumps(result), content_type="application/json")

                    fee.name = name

                if 'money' in data: 
                    try:
                        money = float(data['money'].strip())
                        fee.money = money
                    except ValueError:
                        pass
                if 'feetype' in data:
                    feetype = data['feetype'].strip()
                    fee.feetype = feetype
 
                fee.save()
                result['status'] = SUCCESS
                result['msg'] = "修改成功" 
            except DynamicFee.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = "未找到对应收费项"

        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self, request, community):
        """
        删除
        """
        result = {
            'status': ERROR,
            'msg': '暂时不支持删除'
        }
        data = request.POST
        if 'uuid' in data:
            feeuuid = data['uuid']
            DynamicFee.objects.filter(uuid=feeuuid, community=community).delete()
            result['status'] = SUCCESS
            result['msg'] = '已删除'
        else:
            result['msg'] = 'Need uuids,  community uuid in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")
