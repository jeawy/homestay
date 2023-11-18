from property.code import SUCCESS, ERROR 
import time

def get_paidservice_detail(paidservice): 
    paidservice_dict = {}
    paidservice_dict['uuid'] = paidservice.uuid
    paidservice_dict['category'] = paidservice.category
    paidservice_dict['username'] = paidservice.user.username  
    paidservice_dict['community'] = paidservice.community.name
    paidservice_dict['title'] = paidservice.title
    paidservice_dict['content'] = paidservice.content
    paidservice_dict['money'] = paidservice.money
    paidservice_dict['unit'] = paidservice.unit
    paidservice_dict['date'] = time.mktime( paidservice.date.timetuple())
    paidservice_dict['status'] = paidservice.status
    paidservice_dict['number'] = 0
     
    return paidservice_dict
         

def get_paidservice(paidservices):
    paidservices_ls = []
    for paidservice in paidservices:
        paidservice_dict = get_paidservice_detail(paidservice)
        paidservices_ls.append(paidservice_dict)
     
    return paidservices_ls

def  verify_data(data):
    """
    创建或者修改时 fee的数据验证
    验证通过返回 SUCCESS, ""
    验证不通过，返回ERROR， "错误原因"
    """
    if 'title' in data:
        title = data['title'].strip()
        if len(title) > 64:
            return ERROR, "名称太长，不能超过32个字"

    if 'unit' in data:
        unit = data['unit'].strip()
        if len(unit) > 10:
            return ERROR, "单位太长，不能超过5个字"

    if 'money' in data:
        money = data['money'].strip()
        try:
            money = float(money)
        except ValueError:
            return ERROR, "金额必须是数字"

        if money < 0:
            return ERROR, "金额不能是负数"
     
    return SUCCESS, ""