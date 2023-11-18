 
from fee.models import DynamicFee, FixedFee
from property.code import ERROR, SUCCESS 
 
import time
import json
import pdb
from area.comm import get_parent, get_parent_id
from fee.models import DynamicFee

def get_feetype_txt(feetype):
    """
    获取收费方式的文字说明
    """
    feetype = int (feetype)
    if (feetype == DynamicFee.TYPE_NEED_AREA) :
        return "每月/每平米"
    elif (feetype == DynamicFee.TYPE_NO_NEED_AREA):
        return "每月/每户"
    else:
        return "未知类型"

def get_fee(room):
    """
    获取该房产所欠的物业费用
    """
    allfees == 0 
    # 具体功能待完善
    return allfees

def get_dynamic_fees_dict(fees):
    fee_ls = []
    for fee in fees:
        fee_dict = get_dynamic_fee_dict(fee)     
        fee_ls.append(fee_dict)

    return fee_ls

def get_dynamic_fee_dict(fee):
    fee_dict = {}   
    fee_dict['uuid'] = fee.uuid 
    fee_dict['name'] = fee.name
    fee_dict['money'] = fee.money
    fee_dict['feetype'] = fee.feetype
      
    fee_dict['date'] = time.mktime(fee.date.timetuple())
    
    return fee_dict



def get_fixed_fees_dict(fees):
    fee_ls = []
    for fee in fees:
        fee_dict = get_fixed_fee_detail(fee)     
        fee_ls.append(fee_dict)

    return fee_ls


def get_fixed_fee_detail(fee):
    # 详情
    fee_dict = {}  
    fee_dict['uuid'] = fee.uuid 
    fee_dict['name'] = fee.name
    fee_dict['items'] = []
    for item in fee.fixed_fee_item.all():
        item_dict = {}
        item_dict['name'] = item.name
        item_dict['money'] = item.money
        item_dict['feetype'] = item.feetype
        fee_dict['items'].append(item_dict)
    
    fee_dict['date'] = time.mktime(fee.date.timetuple())
    
    return fee_dict



# 以下为数据验证函数
def verify_dynamic_name_exist(name, community, uuid=None):
    """
    """
    if uuid:
        return DynamicFee.objects.filter(name = name, community=community).exclude(uuid=uuid).exists()
    else:
        return DynamicFee.objects.filter(name = name, community=community).exists()

def verify_fixed_name_exist(name, community, uuid=None):
    """
    """
    if uuid:
        return FixedFee.objects.filter(name = name, community=community).exclude(uuid=uuid).exists()
    else:
        return FixedFee.objects.filter(name = name, community=community).exists()
 

def verify_userinfo_data(data):
    """
    用户登记时验证数据
    创建或者修改时 fee的用户登记数据验证
    验证通过返回 SUCCESS, ""
    验证不通过，返回ERROR， "错误原因"
    """
    if 'title' in data:
        title = data['title'].strip()
        if len(title) > 256:
            return ERROR, fee_TITLE_TOO_LONG
     
    if 'status' in data:
        status = data['status'].strip()
        if int(status) not in [fee.DRAFT, fee.PUBLISHED, fee.CANCEL]:
            return ERROR, fee_STATUS_ERROR
    
    if 'show_userinfo' in data:
        show_userinfo = data['show_userinfo'].strip()
        if int(show_userinfo) not in [0,1]:
            return ERROR, fee_SHOW_USERINFO_ERROR
    
    

    return SUCCESS, ""

def  verify_dynamic_data(data):
    """
    创建或者修改时 fee的数据验证
    验证通过返回 SUCCESS, ""
    验证不通过，返回ERROR， "错误原因"
    """
    if 'name' in data:
        name = data['name'].strip()
        if len(name) > 20:
            return ERROR, "收费制名称太长，不能超过10个字"
    
    if 'money' in data:
        money = data['money'].strip()
        try:
            money = float(money)
        except ValueError:
            return ERROR, "金额必须是数字"

        if money < 0:
            return ERROR, "金额不能是负数"
     
    return SUCCESS, ""



def  verify_fixed_data(data):
    """
    创建或者修改时 fee的数据验证
    验证通过返回 SUCCESS, ""
    验证不通过，返回ERROR， "错误原因"
    """
    if 'name' in data:
        name = data['name'].strip()
        if len(name) > 20:
            return ERROR, "收费制名称太长，不能超过10个字"
    
    if 'money' in data:
        money = data['money'].strip()
        try:
            money = float(money)
        except ValueError:
            return ERROR, "金额必须是数字"

        if money < 0:
            return ERROR, "金额不能是负数"
     
    return SUCCESS, ""