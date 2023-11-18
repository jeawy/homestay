from  withdraw.models import WithDraw, WithdrawImgs
from datetime import datetime 
import time


def has_submit_withdraw(user = None, community = None):
    # 本月是否提交过取现申请？一个月只能提交一次取现申请
    now = datetime.now()
    month = now.month
    year = now.year
    firstday = datetime(year, month, 1) 
    if user is not None:
        return WithDraw.objects.filter(user = user, date__gte = firstday).exists()
    else:
        return WithDraw.objects.filter(community = community, date__gte = firstday).exists()


def single_withdraw(withdraw): 
    content = {}
    content['uuid'] = withdraw.uuid
    content['username'] = withdraw.user.username
    content['phone'] = withdraw.user.phone
    
    content['money'] = withdraw.money
    if withdraw.payed_date:
        content['payed_date'] = time.mktime(withdraw['payed_date'].timetuple())
    else:
        content['payed_date'] = ""
    
    if withdraw.community:
        content['communityname'] = withdraw.community.name
    else:
        content['communityname'] = ""
    content['date'] = time.mktime(withdraw.date.timetuple()) 
    content['status'] = withdraw.status
    content['remark'] = withdraw.remark
    
    imgs = list(WithdrawImgs.objects.filter(withdraw=withdraw).values("filepath"))
  
    content['images'] = imgs 

    return content
   