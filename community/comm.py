 
from property.code import ERROR, SUCCESS 
from community.i18 import * 
import time
from datetime import datetime, timedelta
import json
import pdb
from area.comm import get_parent, get_parent_id
from community.models import Community, Staff
from building.models import RoomDynamicFeeDetail
from common.utils import verify_phone


def getUserCommunities(user):
    """
    获取物业或者IT manager所在社区
    # 功能还未完成
    # 员工所在物业community->staff表中
    """ 
    communities = set(Community.objects.filter(IT_MANAGER = user ).values_list('uuid', flat=True)) 
    staffs = set(Staff.objects.filter(user = user).values_list(
        'community__uuid', flat=True)) 
    return communities | staffs 


def get_community_dict(communitys, perm=False, needfeedetail = False ):
    # pc=True时，返回pc端需要的数据, pc端获取更详细的数据
    # <QuerySet [{'org__uuid': '2cd928bc-d455-49d9-92f5-243ba19829f4', 'tatol_count': 4},
    #  {'org__uuid': 'fa3825bb-0653-4b46-8af4-a9bd95bd61ed', 'tatol_count': 2}]>
    community_ls = []
    for community in communitys:
        community_dict = get_community_detail(community, perm, needfeedetail)     
        community_ls.append(community_dict)

    return community_ls


def get_community_detail(community, perm=False, needfeedetail = False):
    # 详情
    # pc=True时，返回pc端需要的数据, pc端获取更详细的数据
    # <QuerySet [{'org__uuid': '2cd928bc-d455-49d9-92f5-243ba19829f4', 'tatol_count': 4},
    #  {'org__uuid': 'fa3825bb-0653-4b46-8af4-a9bd95bd61ed', 'tatol_count': 2}]>

    # needfeedetail 与小区信息一起返回即将到期的非固定性收费
    community_dict = {} 
    community_dict['username'] = community.user.username 
    community_dict['uuid'] = community.uuid 
    community_dict['name'] = community.name
    if community.area:
        community_dict['area'] = get_parent(community.area)
        community_dict['areaids'] = get_parent_id(community.area)
    else:
        community_dict['area'] = ""
        community_dict['areaids'] = []
     
    if community.IT_MANAGER:
        community_dict['itmanager'] =  community.IT_MANAGER.uuid
        community_dict['itmanagername'] =  community.IT_MANAGER.username
        community_dict['itmanagerphone'] =  community.IT_MANAGER.phone
    else:
        community_dict['itmanager'] = ""
        community_dict['itmanagername'] = ""
        community_dict['itmanagerphone'] = ""
    
    if community.organize:
        community_dict['organize'] =  community.organize.uuid
        community_dict['organizename'] =  community.organize.alias
        community_dict['organizelogo'] =  community.organize.logo
        community_dict['organizelicense'] =  community.organize.license
         
    else:
        community_dict['organize'] = ""
        community_dict['organizename'] = ""
        community_dict['organizelogo'] = ""
        community_dict['organizelicense'] = ""
         

    community_dict['address'] = community.address
    community_dict['longitude'] = community.longitude
    community_dict['latitude'] = community.latitude
    community_dict['shequ'] = community.shequ
    community_dict['jiedaoban'] = community.jiedaoban 

    community_dict['service_level'] = community.service_level
    community_dict['fee_level'] = community.fee_level
    community_dict['fee_standand'] = community.fee_standand
    community_dict['fee_way'] = community.fee_way

    community_dict['contract'] = community.contract
    community_dict['manager_name'] = community.manager_name
    community_dict['manager_position'] = community.manager_position
    community_dict['manager_phone'] = community.manager_phone

    community_dict['manager_photo'] = community.manager_photo
    community_dict['weibao_license'] = community.weibao_license
    community_dict['signet'] = community.signet
    community_dict['tel'] = community.tel
    community_dict['extra_content'] = community.extra_content

    community_dict['total_area'] = community.total_area
    community_dict['total_rooms'] = community.total_rooms
 
    community_dict['date'] = time.mktime(community.date.timetuple())

    if perm:
        # 返回pc端需要的数据, 及时是pc端， 用户必须是物业员工 
        community_dict['wx_sub_mch_id'] = community.wx_sub_mch_id  
        community_dict['money_left'] = community.money_left
        community_dict['today_income_money'] = community.today_income_money
        community_dict['msg_left'] = community.msg_left  
        community_dict['expend_total'] = community.expend_total
        community_dict['income_total'] = community.income_total 

        community_dict['paidservice_msg'] = community.paidservice_msg  
        community_dict['repaire_msg'] = community.repaire_msg
        community_dict['fee_msg'] = community.fee_msg
 
    if needfeedetail:
        # 与小区信息一起返回即将到期的非固定性收费
        now = datetime.now() + timedelta(days = 15) # 剩余15天
        fees = list(RoomDynamicFeeDetail.objects.filter(
            room__community = community, 
            end_date__lte = now
         ).values("room__unit__name","room__uuid",
         "room__unit__building__name",
          "room__name", "room__owner__phone", "dynamicfee__name",
          "end_date"))
        for fee in fees:
            fee['end_date'] = time.mktime(fee['end_date'].timetuple())
        community_dict['fees'] = fees

    return community_dict

# 以下为数据验证函数
 

def verify_userinfo_data(data):
    """
    用户登记时验证数据
    创建或者修改时 community的用户登记数据验证
    验证通过返回 SUCCESS, ""
    验证不通过，返回ERROR， "错误原因"
    """
    if 'title' in data:
        title = data['title'].strip()
        if len(title) > 256:
            return ERROR, community_TITLE_TOO_LONG
     
    if 'status' in data:
        status = data['status'].strip()
        if int(status) not in [community.DRAFT, community.PUBLISHED, community.CANCEL]:
            return ERROR, community_STATUS_ERROR
    
    if 'show_userinfo' in data:
        show_userinfo = data['show_userinfo'].strip()
        if int(show_userinfo) not in [0,1]:
            return ERROR, community_SHOW_USERINFO_ERROR
     
    return SUCCESS, ""

def  verify_data(data):
    """
    创建或者修改时 community的数据验证
    验证通过返回 SUCCESS, ""
    验证不通过，返回ERROR， "错误原因"
    """
    myDict = data.dict()
    if 'name' in data:
        name = data['name'].strip()
        if len(name) > 256:
            return ERROR, COMMUNITY_TITLE_TOO_LONG

    if 'address' in data:
        address = data['address'].strip()
        if len(address) > 128:
            return ERROR, COMMUNITY_ADDRESS_TOO_LONG
    
    if 'shequ' in data:
        shequ = data['shequ'].strip()
        if len(shequ) > 128:
            return ERROR, "社区长度不能超过64"
    
    if 'tel' in data:
        tel = data['tel'].strip()
        if len(tel) > 18:
            return ERROR, "客服电话不能超过18"

    if 'jiedaoban' in data:
        jiedaoban = data['jiedaoban'].strip()
        if len(jiedaoban) > 128:
            return ERROR, "街道办长度不能超过64"

    if 'service_level' in data:
        service_level = data['service_level'].strip()
        if len(service_level) > 56:
            return ERROR, "服务等级限28汉字"

    if 'fee_level' in data:
        fee_level = data['fee_level'].strip()
        if len(fee_level) > 56:
            return ERROR, "收费等级限28汉字"
    if 'fee_standand' in data:
        fee_standand = data['fee_standand'].strip()
        if len(fee_standand) > 56:
            return ERROR, "收费标准限28汉字"
    if 'fee_way' in data:
        fee_way = data['fee_way'].strip()
        if len(fee_way) > 56:
            return ERROR, "收费方式限28汉字"
    
    if 'manager_name' in data:
        manager_name = data['manager_name'].strip()
        if len(manager_name) > 16:
            return ERROR, "物业经理限16汉字"
    
    if 'manager_position' in data:
        manager_position = data['manager_position'].strip()
        if len(manager_position) > 56:
            return ERROR, "职务限16汉字"

    if 'manager_phone' in data:
        manager_phone = data['manager_phone'].strip()
        if len(manager_phone) > 12:
            return ERROR, "联系电话不超过12个数字"
    
    if 'total_area' in data:
        total_area = data['total_area'].strip()
        try:
            int(total_area)
        except ValueError: 
            return ERROR, "总面积数必须是整数"
    
    if 'total_rooms' in data:
        total_rooms = data['total_rooms'].strip()
        try:
            int(total_rooms)
        except ValueError: 
            return ERROR, "总户数必须是整数"
    
    if 'paidservice_msg' in data:
        paidservice_msg = data['paidservice_msg'].strip()
        paidservice_msg.replace("，", ",")
        paidservice_msg = paidservice_msg.split(",")
        paidservice_msg_tmp = ""
        for item in paidservice_msg:
            # 验证手机格式是否正确，去掉不正确的
            if verify_phone(item):
                if paidservice_msg_tmp:
                    paidservice_msg_tmp += ","+item
                else:
                    paidservice_msg_tmp = item
        myDict['paidservice_msg'] = paidservice_msg_tmp

    
    if 'repaire_msg' in data:
        repaire_msg = data['repaire_msg'].strip()
        repaire_msg.replace("，", ",")
        repaire_msg = repaire_msg.split(",")
        repaire_msg_tmp = ""
        for item in repaire_msg:
            # 验证手机格式是否正确，去掉不正确的
            if verify_phone(item):
                if repaire_msg_tmp:
                    repaire_msg_tmp += ","+item
                else:
                    repaire_msg_tmp = item
        myDict['repaire_msg'] = repaire_msg_tmp

    
    if 'fee_msg' in data:
        fee_msg = data['fee_msg'].strip()
        fee_msg.replace("，", ",")
        fee_msg = fee_msg.split(",")
        fee_msg_tmp = ""
        for item in fee_msg:
            # 验证手机格式是否正确，去掉不正确的
            if verify_phone(item):
                if fee_msg_tmp:
                    fee_msg_tmp += ","+item
                else:
                    fee_msg_tmp = item
        myDict['fee_msg'] = fee_msg_tmp

    return SUCCESS, myDict