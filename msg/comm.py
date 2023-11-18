import time
from msg.models import MsgOrders, MsgSendRecord
from django.db.models import Sum
import pdb

def get_record(records):
    records_ls = []
    for record in records:
        record_dict = {}
        record_dict['username'] = record.user.username 
        record_dict['org'] = record.org.alias
        record_dict['community'] = record.community.name
        record_dict['phone'] = record.phone
        record_dict['room'] = record.room.name
        record_dict['unitname'] = record.room.unit.name
        record_dict['message'] = record.message
        record_dict['date'] = time.mktime( record.date.timetuple())
        record_dict['status'] = record.status
        record_dict['msgtype'] = record.msgtype
        if record.order:
            record_dict['order'] = record.order.billno
        else:
            record_dict['order'] = ""
        records_ls.append(record_dict)
     
    return records_ls

def get_msg_left(community):
    """
    获得某个小区的短信剩余量
    订单数量-已经发送的数量=剩余量
    """
    total_buy = MsgOrders.objects.filter(community = community, status = MsgOrders.PAYED )\
        .aggregate(Sum("total"))['total__sum']
    total_consume = MsgSendRecord.objects.filter(community = community).count() 
     
    if total_buy is None:
        total_buy = 0
     
    return total_buy - total_consume


def msgSendRecord(community, phone, message, status, msgtype,
                    user = None,order = None, org = None, room = None):
    MsgSendRecord.objects.create(
        community = community,
        phone = phone,
        message = message,
        status = status,
        msgtype = msgtype,
        user = user,
        order = order,
        org = org, 
        room = room
    )