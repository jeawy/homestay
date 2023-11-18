 
from property.code import ERROR, SUCCESS 
from organize.i18 import * 
import time
import json
import pdb 
from community.models import Community, Staff


def getUserOrganize(user):
    """
    获取用户所在物业
    # IT Manager 管理的物业
    # 员工所在物业community->staff表中
    """ 
    communities = set(Community.objects.filter(IT_MANAGER = user, 
     organize__isnull = False).values_list('organize__uuid', flat=True))
     
    staffs = set(Staff.objects.filter(user = user,
    community__organize__uuid__isnull = False).values_list(
        'community__organize__uuid', flat=True))
 
    return communities | staffs 

def get_organize_dict(organizes):
    organize_ls = []
    for organize in organizes:
        organize_dict = get_organize_detail(organize)     
        organize_ls.append(organize_dict)

    return organize_ls


def get_organize_detail(organize):
    # 详情
    organize_dict = {} 
    if organize.manager: 
        organize_dict['manager'] = {
            "name":organize.manager.username,
            "uuid":organize.manager.uuid,
            "phone":organize.manager.phone
        } 
    else:
        organize_dict['manager'] = {

        } 
    organize_dict['uuid'] = organize.uuid 
    organize_dict['name'] = organize.name
     
    organize_dict['date'] = time.mktime(organize.date.timetuple())
    organize_dict['logo'] = organize.logo
    organize_dict['license'] = organize.license
    organize_dict['alias'] = organize.alias
    organize_dict['code'] = organize.code
     
    return organize_dict



# 以下为数据验证函数
  
def  verify_data(data):
    """
    创建或者修改时 organize的数据验证
    验证通过返回 SUCCESS, ""
    验证不通过，返回ERROR， "错误原因"
    """
    if 'name' in data:
        name = data['name'].strip()
        if len(name) > 128:
            return ERROR, "物业全称太长，限64"
    
    if 'alias' in data:
        alias = data['alias'].strip()
        if len(alias) > 16:
            return ERROR, "物业别名太长，限16"


    if 'code' in data:
        code = data['code'].strip()
        if len(code) > 64:
            return ERROR, "统一社会信息代码太长，限64"

 
    return SUCCESS, ""