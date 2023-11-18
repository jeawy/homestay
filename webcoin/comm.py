import json
import pdb
import random
import string
from datetime import datetime
from common.fun import datetimeStamp
import configparser
from property import settings
from property.code import  SUCCESS, ERROR 
from property.entity import EntityType
from webcoin.models import WebCoin  
from appuser.models import AdaptorUser as User 


def reduce_coin(bill, coin):
    # 使用余额支付 
    user = bill.user
    webcoins = WebCoin.objects.filter(user = user)
    total_coin = 0
    for webcoin in webcoins:
        total_coin += webcoin.action 

    if total_coin < coin:
        bill.status = bill.UNUSUAL
        bill.remark = "积分不足"
        bill.save()
        return 1, "积分不足"
    else:
        if user.islooked == 0:
            user.islooked = 1
            user.save() # 锁定用户
            WebCoin.objects.create(
                user = user,
                entity = EntityType.BILL,
                instanceuuid = bill.uuid,
                action = -coin,
                reason = "礼品兑换:"+bill.billno
            ) 
            user.islooked = 0
            user.save() # 解锁用户  

            bill.status = bill.PAYED 
            bill.save()     
            return 0, "已支付" 
        else:
            return 2, "用户已锁定, 请等待"



def cnum_filter(user, tag):
    """
    积分数量筛选
    """
    # 获取积分的数量统计
    get_sum = 0
    # 使用积分的数量统计
    use_sum = 0
    result = {}
    try:
        tag = int(tag)
    except ValueError:
        result['status'] = ERROR
        result['msg'] = 'tag不是int'
        return result
    get_coins = WebCoin.objects.filter(user=user,action__gte=0)
    for get_coin in get_coins:
        get_sum += get_coin.action
    use_coins = WebCoin.objects.filter(user=user,action__lt=0)
    for use_coin in use_coins:
        use_sum += use_coin.action
    if tag == 1:
        result['get'] = get_sum
    if tag == -1:
        result['use'] = use_sum
    elif tag == 0:
        result['get'] = get_sum
        result['use'] = use_sum
    return result

def  webcoin_info_lst(rets):
    """
    获取交易明细
    """
    ret_lst = []
    for ret in rets:
        ret_dct = {}
        ret_dct['id'] = ret.id
        ret_dct['user'] = ret.user.username
        ret_dct['modify_date'] = datetimeStamp(ret.date)
        ret_dct['entity'] = ret.entity 
        ret_dct['action'] = ret.action
        ret_dct['reason'] = ret.reason
        ret_lst.append(ret_dct)
    return ret_lst

def add_webcoin(rule, user, instanceuuid,   money=None,   tag=0):
    """
    增加积分 
    rule：0.物业费  
    money: 物业费 
    """
    result = {
        'status': SUCCESS
    }  
    webcoin = WebCoin()
    if rule == webcoin.PROPERTY_MGE_FEE:
        coins = int(money / 10) # 10元一个积分
        action = coins 
        webcoin.entity = webcoin.PROPERTY_MGE_FEE
        webcoin.instanceuuid = instanceuuid
        webcoin.reason = '物业缴费获得{0}积分'.format(str(coins))
     
    webcoin.action = action
    webcoin.user = user
    webcoin.save()
    result['msg'] = webcoin
    return result

def activation_code(id,length=6):
    '''
    生成邀请码：id + L + 随机码
    '''
    prefix = hex(int(id))[2:]+ 'L'
    length = length - len(prefix)
    chars=string.ascii_letters+string.digits
    return prefix + ''.join([random.choice(chars) for i in range(length)])

def get_id(code):
    """
    获取邀请码对应的主键id
    """
    content = {
        'status': SUCCESS
    }
    id_hex = code.split('L')[0]
    try:
        invite_id = int(id_hex.upper(), 16)
        content['status'] = SUCCESS
        content['msg'] = str(invite_id)
    except ValueError:
        content['status'] = ERROR
        content['msg'] = '邀请码不存在'
    return content

def check_user(id):
    """
    userid校验
    """
    content = {
        'status': SUCCESS
    }
    try:
        id = int(id)
    except ValueError:
        content['status'] = ERROR
        content['msg'] = 'id不是int'
        return content
    try:
        user = User.objects.get(id=id)
        content['user'] = user
    except User.DoesNotExist:
        content['status'] = ERROR
        content['msg'] = 'user id不存在'
        return content
    return content
