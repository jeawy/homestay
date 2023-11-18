import time
import json
from property.code import ERROR, SUCCESS
from datetime import datetime
from property.settings import DATEFORMAT
from aid.models import Aid, AidImgs, AidOrders,AidCommunities, Entries
from role.models import Cert


def single_aid(aid, user, mine=False, need_detail = False):
    """
    详情
    user = None, 匿名
    mine 表示是否获取的是我的互助单，如果是，返回的信息较多。
    need_detail = false时，返回的是精简信息，true时，返回全部详细信息
    """

    aid_content = {}
    aid_content['uuid'] = aid.uuid
    aid_content['status'] = aid.status
    aid_content['user'] = {
        "username": aid.user.username[:1] + "***",
        "phone": aid.user.phone,
        "uuid": aid.user.uuid,
    }
    aid_content['title'] = aid.title
    aid_content['mode'] = aid.mode
    if aid.content:
        aid_content['content'] = aid.content
    else:
        aid_content['content'] = ""
    aid_content['money'] = aid.money
    aid_content['communityname'] = aid.community.name

    if aid.secretinfo:
        aid_content['secretinfo'] = aid.secretinfo
    else:
        aid_content['secretinfo'] = ""
    aid_content['need_propertior'] = aid.need_propertior
    if aid.end_date:
        aid_content['end_date'] = time.mktime(aid.end_date.timetuple())
    else:
        aid_content['end_date'] = ''
    aid_content['publich_myinfo'] = aid.publich_myinfo
    aid_content['payed'] = aid.payed
    if aid.date:
        aid_content['date'] = time.mktime(aid.date.timetuple())
    else:
        aid_content['date'] = ''
    if aid.answer:
        aid_content['answer'] = {
            "username": aid.answer.username,
            "phone": aid.answer.phone,
            "uuid": aid.answer.uuid,
            "image": aid.answer.thumbnail_portait,
        }
        if aid.answer_extra:
            aid_content['answer']['extra'] = json.loads(aid.answer_extra)
        else:
            aid_content['answer']['extra'] = {
                "servicetimes":'-',
                "score":'-',
            }
    else:
        aid_content['answer'] = {}
    aid_content['communities'] = list(AidCommunities.objects.filter(aid=aid 
                                                         ).values("community__uuid", "community__name"))
    if need_detail:
        aid_content['images'] = list(AidImgs.objects.filter(aid=aid,
                                                            imgtype=AidImgs.FROMAID).values("id", "filename", "filepath"))
        aid_content['commentimages'] = list(AidImgs.objects.filter(aid=aid,
                                                        imgtype=AidImgs.FROMCOMMENT).values("id", "filename", "filepath"))
        
        # 返回评论信息
        aid_content['comment'] = {
            "finish_date":time.mktime(aid.finished_date.timetuple()) if aid.finished_date else "",
            "content": aid.comment,
            "score": aid.score
        }
        # 报名信息
        if aid.status ==  aid.OPEN and aid.mode == aid.SELECTED:
            aid_content['entries'] = list(Entries.objects.filter(aid=aid ).values("id", 
            "score",
            "service_times",
            "user__username", 
            "user__phone", 
            "user__thumbnail_portait",
            "communityname")) 
        else:
            aid_content['entries'] = []
         
    else:
        # 仅返回前三张图片
        aid_content['images'] = list(AidImgs.objects.filter(aid=aid,
                                                            imgtype=AidImgs.FROMAID).values("id", "filename", "filepath"))[:3]
        aid_content['commentimages'] = list(AidImgs.objects.filter(aid=aid,
                                                        imgtype=AidImgs.FROMCOMMENT).values("id", "filename", "filepath"))[:3]
        aid_content['comment'] = {}
        aid_content['entries'] = []
         
    if mine:
        try:
            order = AidOrders.objects.get(aid=aid)
            aid_content['billno'] = order.billno
        except AidOrders.DoesNotExist:
            aid_content['billno'] = ""
    return aid_content


def verify_data(data):
    """
    数据验证
    """
    if 'title' in data:
        title = data['title'].strip()
        if len(title) > 64:
            return ERROR, "标题长度不能超过32"

    if 'money' in data:
        money = data['money'].strip()
        try:
            float(money)
        except ValueError:
            return ERROR, "费用输入错误"

    if 'status' in data:
        status = data['status'].strip()
        try:
            int(status)
        except ValueError:
            return ERROR, "状态码错误"

    if 'end_date' in data:
        end_date = data['end_date'].strip()
        try:
            end_date = end_date.replace("-", "/")
            datetime.strptime(end_date, DATEFORMAT)
        except ValueError:
            return ERROR, "截止日期格式错误"

    return SUCCESS, ""
