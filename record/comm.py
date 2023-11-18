 
from property.code import ERROR, SUCCESS
from record.models import Record
from record.i18 import * 
from threading import Thread
import time
import json
import pdb
from django.conf import settings
from common.utils import create_logo_qrcode

def get_record_dict(records):
    record_ls = []
    for record in records:
        record_dict = {}
         
        record_dict['username'] = record.owner.username 
        record_dict['uuid'] = record.uuid 
        if record.community: 
            record_dict['communityname'] = record.community.name
        else:
            record_dict['communityname'] = "全平台"
        record_dict['title'] = record.title
        record_dict['content'] = record.content
        record_dict['status'] = record.status
        record_dict['duplicate'] = record.duplicate
        record_dict['need_login'] = record.need_login
        record_dict['notice'] = record.notice
        record_dict['only_owner_export'] = record.only_owner_export
        record_dict['date'] = time.mktime(record.date.timetuple())
        if record.deadline:
            record_dict['deadline'] = time.mktime(record.deadline.timetuple())
        else:
            record_dict['deadline'] = None
        record_dict['show_userinfo'] = record.show_userinfo 
        record_dict['autorecord'] = record.autorecord 
        record_dict['autotype'] = record.autotype 
        if record.autodays: 
            record_dict['autodays'] = json.loads(record.autodays )
        else:
            record_dict['autodays'] = []
        record_dict['available_appside'] = record.available_appside 
        record_dict['show_in_list'] = record.show_in_list
        record_dict['limits'] = record.limits 
        record_dict['allow_modify'] = record.allow_modify 
        record_dict['allow_delete'] = record.allow_delete 

        record_ls.append(record_dict)

    return record_ls

def sortrecordThread(record):
    thread = Thread(target=sortrecord, args=(record,))
    thread.start()
    #thread.join()
    #print("end thread")


def sortrecord(record):
    # 对登记记录进行排序
    extras = json.loads(record.extra) 
    autoincrease = False #默认没有自增的字段
    autoindex = -1
    
    for index, item  in enumerate( extras):
        if 'action' in item:
            if item['action'][1] == "autoincrease":
                autoincrease = True
                autoindex = index
                break
    
    if autoincrease:
        infos = record.userrecord.all().order_by("date") 
        sort = 1
        for info in infos:
            values = info.values
            values_ls = values.split(",")
            values_ls[autoindex] = str(sort)
            info.values = ",".join(values_ls)
            info.save()
            sort += 1
    print("sort end")
           
def get_record_detail(record, user=None, onlyShowMine = False):
    # 详情，带用户登记信息
    # user 不为none的时候，说明用户已经登录了。
    record_dict = {}
    record_dict['username'] = record.owner.username
    record_dict['uuid'] = record.uuid 
    record_dict['title'] = record.title
    if record.community: 
        record_dict['communityname'] = record.community.name
    else:
        record_dict['communityname'] = "全平台"
    record_dict['content'] = record.content
    record_dict['status'] = record.status
    record_dict['duplicate'] = record.duplicate
    record_dict['need_login'] = record.need_login
    record_dict['notice'] = record.notice
    record_dict['only_owner_export'] = record.only_owner_export
    record_dict['date'] = time.mktime(record.date.timetuple())
    if record.deadline:
        record_dict['deadline'] = time.mktime(record.deadline.timetuple())
    else:
        record_dict['deadline'] = None
    
    if record.owner == user: 
        record_dict['owner'] = True
    else:
        record_dict['owner'] = False
    record_dict['show_userinfo'] = record.show_userinfo 
    if record.tags: # 登记内容标记
        record_dict['tags'] = record.tags.split(",")
    else:
        record_dict['tags'] = []

    extra = record.extra
    '''
    extra_ls = []
    if extra:
        extra_json = json.loads(extra)
        if extra_json:
            for extra_item in extra_json:
                extra_ls.append(extra_item['label'])
    '''
    record_dict['extra'] = json.loads(extra)
    # 用户登记详细信息
    userinfos = [] 
    if onlyShowMine == True:
        # 仅展示我的登记 
        users = record.userrecord.filter(recorder = user)
        userinfos = get_userinfos(users)
    elif record.show_userinfo == 1  or record.owner == user:
        # 显示用户登记情况 
        users = record.userrecord.all()
        userinfos = get_userinfos(users)
         
    record_dict['autorecord'] = record.autorecord 
    record_dict['autotype'] = record.autotype 
    if record.qrcode is None:
        url = settings.PAYHOST + 'wx/records/'+str(record.uuid)
        qrcodepath = create_logo_qrcode(url) 
        record.qrcode = qrcodepath
        record.save()
    record_dict['qrcode'] = record.qrcode 
    if record.autodays: 
        record_dict['autodays'] = json.loads(record.autodays )
    else:
        record_dict['autodays'] = []
    record_dict['available_appside'] = record.available_appside 

    record_dict['users'] = userinfos
    record_dict['limits'] = record.limits 
    record_dict['allow_modify'] = record.allow_modify 
    record_dict['allow_delete'] = record.allow_delete 
    record_dict['show_in_list'] = record.show_in_list  
    return record_dict

def get_userinfos(users):
    userinfos = []
    for user in users:
        user_dict = {}
        user_dict['uuid'] = user.uuid
        if user.recorder:
            user_dict['username'] = user.recorder.username
        else:
            user_dict['username'] = None 
        if user.values: 
            values = user.values.split(",")
        else:
            values = []
        user_dict['values'] = values
        userinfos.append(user_dict)
    return userinfos

# 以下为数据验证函数

def verify_fillup_data(record, values):
    """
    对登记数据进行验证，主要验证values的长度是否与extra字段的长度一致
    判断是否有自增字段，如果有，计算自增的序号
    """
    extra_json = json.loads(record.extra)
    extra_len = len(extra_json)
    values_ls = values.split(",")
    
    if len(values_ls) != extra_len:
        return False, values
    else:
        return True, values

def verify_userinfo_data(data):
    """
    用户登记时验证数据
    创建或者修改时 record的用户登记数据验证
    验证通过返回 SUCCESS, ""
    验证不通过，返回ERROR， "错误原因"
    """
    if 'title' in data:
        title = data['title'].strip()
        if len(title) > 256:
            return ERROR, RECORD_TITLE_TOO_LONG
     
    if 'status' in data:
        status = data['status'].strip()
        if int(status) not in [Record.DRAFT, Record.PUBLISHED, Record.CANCEL]:
            return ERROR, RECORD_STATUS_ERROR
    
    if 'show_userinfo' in data:
        show_userinfo = data['show_userinfo'].strip()
        if int(show_userinfo) not in [0,1]:
            return ERROR, RECORD_SHOW_USERINFO_ERROR
    
    

    return SUCCESS, ""

def  verify_data(data):
    """
    创建或者修改时 record的数据验证
    验证通过返回 SUCCESS, ""
    验证不通过，返回ERROR， "错误原因"
    """
    if 'title' in data:
        title = data['title'].strip()
        if len(title) > 256:
            return ERROR, RECORD_TITLE_TOO_LONG
     
    if 'status' in data:
        status = data['status'].strip()
        if int(status) not in [Record.DRAFT, Record.PUBLISHED, Record.CANCEL]:
            return ERROR, RECORD_STATUS_ERROR
    
    if 'show_userinfo' in data:
        show_userinfo = data['show_userinfo'].strip()
        if int(show_userinfo) not in [0,1]:
            return ERROR, RECORD_SHOW_USERINFO_ERROR
    
    if 'autorecord' in data:
        autorecord = data['autorecord'].strip()
        if int(autorecord) not in [0,1]:
            return ERROR, "定时字段数值错误"

    if 'available_appside' in data:
        available_appside = data['available_appside'].strip()
        if int(available_appside) not in [0,1]:
            return ERROR, "移动端可见数值错误"
    
    if 'autotype' in data:
        autotype = data['autotype'].strip()
        if int(autotype) not in [0,1,2]:
            return ERROR, "定时登记薄的类型数值错误"
 
    return SUCCESS, ""