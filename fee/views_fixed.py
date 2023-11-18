from datetime import datetime
from appuser.models import AdaptorUser as User
from django.conf import settings
from building.models import Room
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
from fee.comm import verify_fixed_data, get_fixed_fees_dict
from fee.comm import verify_fixed_name_exist, get_fixed_fee_detail

logger = getLogger(True, 'fee', False)


class FixedFeeView(APIView):

    def get(self, request):
        # 获取FixedFee列表
        #
        content = {
            "status": SUCCESS,
            "msg": []
        } 
        if 'communityuuid' in request.GET:
            # 获取详情
            communityuuid = request.GET['communityuuid'] 
            if 'uuid' in request.GET:
                feeuuid = request.GET['uuid']
                try:
                    fee = FixedFee.objects.get(community__uuid=communityuuid, uuid = feeuuid)
                    content['msg'] = get_fixed_fee_detail(fee) 
                    content['status'] = SUCCESS 
                except FixedFee.DoesNotExist:
                    content['msg'] = "未找到相关记录"
            else: 
                fees = FixedFee.objects.filter(community__uuid=communityuuid)
                content['msg'] = get_fixed_fees_dict(fees) 
                content['status'] = SUCCESS 
        else:
            content['msg'] = "缺少community uuid"
 
        return HttpResponse(json.dumps(content), content_type="application/json")

    def post(self, request):
        """
        创建固定收费项目

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

        if 'name' in data  :
            # 创建
            verify_result = verify_fixed_data(data)
            if verify_result[0] == ERROR:
                # 验证失败
                result['status'] = ERROR
                result['msg'] = verify_result[1]
                return HttpResponse(json.dumps(result), content_type="application/json")
             
            fee = FixedFee()
            name = data['name'].strip()
            if  verify_fixed_name_exist(name, community):
                result['msg'] = "收费制名称已存在"
                return HttpResponse(json.dumps(result), content_type="application/json")
            
            fee.name = name 
            fee.community = community 
            fee.uuid = uuid.uuid4()
            fee.save()
            if 'items' in data:
                items = json.loads(data['items'].strip())
                
                for item in items :
                    itemname = item['name'].strip()
                    try:
                        money = float(item['money'] )
                        feetype = item['feetype']
                        FixedItemFee.objects.create(uuid = uuid.uuid4(),
                                    name = itemname,
                                    money = money,
                                    fixedfee = fee,
                                    feetype = feetype)
                    except ValueError as e:
                        print (e)
                        continue
                     
            
            result['status'] = SUCCESS
            result['msg'] = "创建成功"

            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['status'] = ERROR
            result['msg'] = "缺少参数name"
         
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
        verify_result = verify_fixed_data(data)
        if verify_result[0] == ERROR:
            # 验证失败 
            result['msg'] = verify_result[1]
            return HttpResponse(json.dumps(result), content_type="application/json")

        if 'uuid' in data:
            feeuuid = data['uuid'].strip()
            try:
                fee = FixedFee.objects.get(uuid=feeuuid)

                if 'name' in data:
                    name = data['name'].strip()
                    if verify_fixed_name_exist(name, community, feeuuid):
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

                if 'items' in data:
                    # 删除原来所有的，重新建
                    FixedItemFee.objects.filter(fixedfee = fee).delete()
                    items = json.loads(data['items'].strip())
                    for item in items :
                        itemname = item['name'].strip()
                        try:
                            money = float(item['money'] )
                            feetype = item['feetype']
                            FixedItemFee.objects.create(uuid = uuid.uuid4(),
                                        name = itemname,
                                        money = money,
                                        fixedfee = fee,
                                        feetype = feetype)
                        except ValueError:
                            continue
                fee.save()
                result['status'] = SUCCESS
                result['msg'] = "修改成功" 
            except DynamicFee.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = "未找到对应收费项"
        elif 'assets' in data and 'fixedfee' in data:
            # 批量设置收费制
            assets = json.loads(data['assets'])
            fixedfee = data['fixedfee']
            if len(assets) > 0:
                if len(fixedfee) > 0:
                    try:
                        fixedfee_instance = FixedFee.objects.get(uuid = fixedfee, community = community)
                        
                        print(datetime.now())
                        if 'room' in data: 
                            # 直接更新房号
                            Room.objects.filter(uuid = assets[0] ).update(fixed_fee= fixedfee_instance)
                        else:
                            unit_uuids = [asset[1] for asset in assets]
                            Room.objects.filter(unit__uuid__in = unit_uuids ).update(fixed_fee= fixedfee_instance)
                        print(datetime.now())
                        result['status'] = SUCCESS
                        result['msg'] = "设置成功"
                    except FixedFee.DoesNotExist:
                        result['msg'] = "未找到相关收费制，请刷新重试"
                else:
                    result['msg'] = "请选择物业收费制"
            else:
                result['msg'] = "请选择楼号、单元号"
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
        if 'uuids' in data:
            uuids = data['uuids']
            FixedFee.objects.filter(uuid__in=uuids.split(","), community=community).delete()
            result['status'] = SUCCESS
            result['msg'] = '已删除'
        else:
            result['msg'] = 'Need uuids、community uuid in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")
