import json
import pdb
import time
from prorepair.models import ProRepair, RepairFdkImgs
from property.code import SUCCESS, ERROR
from common.sms import send_sms
from threading import Thread
from common.utils import verify_phone
from notice.comm import NoticeMgr 
from msg.comm import msgSendRecord

def create_sms_notice(community):
    # 维修服务
    #thread = Thread(target=thread_create_notice, args=(community,))
    #thread.start()
    thread_create_notice(community)
     
def thread_create_notice(community):  
    if community.repaire_msg:
        # 发短信通知给verify_phone
        kwargs = {
            "smsSignId":community.smsSignId
        }
        phones = community.repaire_msg.split(",")
        print(phones)
        for phone in phones:
            print(phone)
            if verify_phone(phone): 
                msg_result = send_sms(smstype="repair", phone=phone, code=community.name, **kwargs)
                msgSendRecord(community, phone, msg_result[1], status=0,msgtype=1 )
  

def single_repair(repairuuid):
    """
    维修详情
    """
    content = {
        'status':SUCCESS
    }
    try:
        prorepair = ProRepair.objects.get(uuid=repairuuid)
        notice_content = {}
        notice_content['uuid'] = prorepair.uuid
        notice_content['content'] = prorepair.content
        notice_content['contact'] = prorepair.contact
        notice_content['communityname'] = prorepair.community.name
        notice_content['user'] = {
            "username" : prorepair.user.username,
            "phone" : prorepair.user.phone,
        } 
        if prorepair.score:
            notice_content['score'] = prorepair.score
        else:
            notice_content['score'] = ''
        
        if prorepair.reply_user:
            notice_content['reply_user'] = prorepair.reply_user.username
        else:
            notice_content['reply_user'] = ''
        
        if prorepair.reply_date:
            notice_content['reply_date'] = time.mktime(prorepair.reply_date.timetuple()) 
        else:
            notice_content['reply_date'] = ''
 
        notice_content['status'] = prorepair.status 
        notice_content['result'] = prorepair.result
        notice_content['estimate'] = prorepair.estimate
        if prorepair.estimate_date:
            notice_content['estimate_date'] = time.mktime(prorepair.estimate_date.timetuple())
        else:
            notice_content['estimate_date'] = ""
        if prorepair.date:
            notice_content['date'] = time.mktime(prorepair.date.timetuple())
        else:
            notice_content['date'] = ''
        reply_img_list =list(RepairFdkImgs.objects.filter(prorepair=prorepair, 
                             imagetype=RepairFdkImgs.REPLY).values("filepath", "id")) 
        request_img_list =list(RepairFdkImgs.objects.filter(prorepair=prorepair, imagetype=RepairFdkImgs.REQUEST).values("filepath")) 
        notice_content['reply_img_list'] = reply_img_list
        notice_content['request_img_list'] = request_img_list
        content['status'] = SUCCESS
        content['msg'] = notice_content
    except ProRepair.DoesNotExist:
        content['status'] = ERROR
        content['msg'] = '反馈不存在'
    return content