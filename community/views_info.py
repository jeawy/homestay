from django.contrib.auth.backends import RemoteUserBackend
from common.logutils import getLogger
import pdb
import json
import uuid  
from rest_framework.views import APIView 
from django.http import HttpResponse
from django.views import View
from property.code import ERROR, SUCCESS
from community.comm import verify_data 
from community.i18 import *
from community.models import Community
from django.conf import settings 
from appuser.models import AdaptorUser as User
from organize.models import Organize
from community.comm import getUserCommunities
logger = getLogger(True, 'community', False)
    
class CommunityInfoView(APIView):  
    def post(self, request):
        """
        物业编辑公示信息 
        """
        result = {
            'status': ERROR
        }
        user = request.user
          
        data = request.POST
        if 'uuid' in data:
            communityuuid = data['uuid'].strip()
            try:
                # 这里后面还要加限制，只能是这个社区里的物业工作人员修改
                # 仅仅通过uuid和修改权限就允许修改，有安全隐患
                community = Community.objects.get(uuid = communityuuid)
                communities = getUserCommunities(user)
                perm  = user.has_community_perm("community.community.manage_community", community) 
                if not perm and communityuuid not in communities: 
                    # 没有编辑权限，返回权限错误
                    result['msg'] = COMMUNITY_AUTH_ERROR
                    return HttpResponse(json.dumps(result), content_type="application/json")
                    
                verify_result = verify_data(data)
                if verify_result[0] == ERROR:
                    # 验证失败
                    result['status'] = ERROR
                    result['msg'] = verify_result[1]
                    return HttpResponse(json.dumps(result), content_type="application/json")
                else:
                    data = verify_result[1]
                if 'service_level' in data:
                    service_level = data['service_level'].strip()
                    community.service_level = service_level
                
                if 'tel' in data:
                    tel = data['tel'].strip()
                    community.tel = tel
                     
                if 'fee_level' in data:
                    fee_level = data['fee_level'].strip()
                    community.fee_level = fee_level
                    
                if 'fee_standand' in data:
                    fee_standand = data['fee_standand'].strip()
                    community.fee_standand = fee_standand
                     
                if 'fee_way' in data:
                    fee_way = data['fee_way'].strip()
                    community.fee_way = fee_way
                    
                if 'manager_name' in data:
                    manager_name = data['manager_name'].strip()
                    community.manager_name = manager_name
                     
                if 'manager_position' in data:
                    manager_position = data['manager_position'].strip()
                    community.manager_position = manager_position
                    

                if 'manager_phone' in data:
                    manager_phone = data['manager_phone'].strip()
                    community.manager_phone = manager_phone
            
                if 'manager_photo' in data:
                    manager_photo = data['manager_photo'].strip()
                    community.manager_photo = manager_photo


                if 'signet' in data:
                    signet = data['signet'].strip()
                    community.signet = signet
                
                if 'weibao_license' in data:
                    weibao_license = data['weibao_license'].strip()
                    community.weibao_license = weibao_license

                if 'extra_content' in data:
                    extra_content = data['extra_content'].strip()
                    community.extra_content = extra_content
                
                if 'contract' in data: 
                    contract = data['contract'].strip()
                    logger.debug(contract)
                    community.contract = contract
                if 'total_area' in data:
                    total_area = data['total_area'].strip()
                    community.total_area = total_area 
                if 'total_rooms' in data:
                    total_rooms = data['total_rooms'].strip()
                    community.total_rooms = total_rooms 
                
                if 'paidservice_msg' in data:
                    paidservice_msg = data['paidservice_msg'].strip()
                    community.paidservice_msg = paidservice_msg
                
                if 'repaire_msg' in data:
                    repaire_msg = data['repaire_msg'].strip()
                    community.repaire_msg = repaire_msg

                if 'fee_msg' in data:
                    fee_msg = data['fee_msg'].strip()
                    community.fee_msg = fee_msg

                if community.organize:
                    organize = community.organize
                    if 'logo' in data:
                        logo = data['logo'].strip()
                        organize.logo = logo
                    
                    if 'license' in data:
                        wuye_license = data['license'].strip()
                        organize.license = wuye_license 
                    organize.save() 

                community.save()
                result['status'] = SUCCESS
                result['msg'] = "编辑成功"
            except Community.DoesNotExist: 
                result['msg'] = "未找到相关信息"
                    
            return HttpResponse(json.dumps(result), content_type="application/json")
        else: 
            result['status'] = ERROR
            result['msg'] = COMMUNITY_NAME_ERROR
        return HttpResponse(json.dumps(result), content_type="application/json")
  