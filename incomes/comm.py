from django.db.models import Sum
from aid.models import AidOrders, Aid
from building.models import RoomFeeOrders
from paidservice.models import PaidOrder
from common.logutils import getLogger  
from withdraw.models import WithDraw
from datetime import datetime
from msg.models import MsgOrders

logger = getLogger(True, 'incomes', False)


def statisticsMoney(user):
    # 计算user用户的收入、支出、余额总和
    # 返回：收入、支出、余额
    kwargs={}
    kwargs['aid__answer'] = user
    kwargs['status'] = AidOrders.PAYED
    kwargs['aid__status__gte'] = Aid.ACCEPTED # 已完成的订单
    income_total = 0 # 收入总和
    expend_total = 0 # 支出总和
    aidorders = list(AidOrders.objects.filter(**kwargs).values_list(
        "money",
        "aid__community__aid_commission_rate"))
    for aidorder in aidorders:
        income_total += aidorder[0] * (1 - aidorder[1])

    # 计算支出总和
    kwargs={} 
    kwargs['status'] = AidOrders.PAYED
    kwargs['user'] = user 
    # 1、互助类支出
    aidmoney = AidOrders.objects.filter(**kwargs).aggregate(Sum("money"))['money__sum'] 
    logger.debug("expend for aid: " + str(aidmoney))
    # 2、物业费支出
    kwargs={} 
    kwargs['status'] = RoomFeeOrders.PAYED
    kwargs['user'] = user 
    feemoney = RoomFeeOrders.objects.filter(**kwargs).aggregate(Sum("money"))['money__sum'] 

    # 3、有偿服务支出
    kwargs={} 
    kwargs['status'] = PaidOrder.PAYED
    kwargs['user'] = user 
    paidservicemoney = PaidOrder.objects.filter(**kwargs).aggregate(Sum("money"))['money__sum'] 
    
    # 计算余额
    kwargs={} 
    kwargs['user'] = user
    kwargs['community__isnull'] = True
    withdrawmoney = WithDraw.objects.filter(**kwargs).aggregate(Sum("money"))['money__sum']
    
    if aidmoney:
        expend_total +=  aidmoney
    if feemoney :
        expend_total +=  feemoney
    if paidservicemoney:
        expend_total +=  paidservicemoney

    if withdrawmoney:
        left = income_total - withdrawmoney
    else:
        left = income_total

    return income_total, expend_total, left



def statisticsMoneyOrg(community):
    # 计算物业的收入、支出、余额总和
    # 返回：收入(物业费：固定和非固定, 有偿服务)、支出(短信购买)、余额、今日收入
    kwargs={} 
    income_today = 0 # 今日收入
    income_total = 0 # 收入总和
    expend_total = 0 # 支出总和

    # 1 物业费收入总和
    kwargs={} 
    kwargs['status'] = RoomFeeOrders.PAYED 
    kwargs['community'] = community 
    income_total_sum = RoomFeeOrders.objects.filter(**kwargs).aggregate(Sum("money"))['money__sum'] 
    if income_total_sum:
        income_total += income_total_sum
    kwargs['date__gte'] = datetime.now().date() # 计算今日收入
    income_today_tmp = RoomFeeOrders.objects.filter(**kwargs).aggregate(Sum("money"))['money__sum'] 
    if income_today_tmp:
        income_today += income_today_tmp

    # 2 有偿服务总和
    kwargs={} 
    kwargs['status__in'] = [PaidOrder.PAYED, PaidOrder.CLOSED]
    kwargs['community'] = community 

    income_total_sum = PaidOrder.objects.filter(**kwargs).aggregate(Sum("money"))['money__sum']
    if income_total_sum:
        income_total += income_total_sum

    kwargs['date__gte'] = datetime.now().date() # 计算今日收入
    income_today_tmp = PaidOrder.objects.filter(**kwargs).aggregate(Sum("money"))['money__sum']
    if income_today_tmp:
        income_today += income_today_tmp

    # 计算支出总和（短信充值） 
    kwargs={} 
    kwargs['status'] = AidOrders.PAYED
    kwargs['community'] = community  
    expend_total = MsgOrders.objects.filter(**kwargs).aggregate(Sum("money"))['money__sum'] 
    if expend_total is None:
        expend_total = 0
    # 计算余额
    kwargs={} 
    kwargs['community'] = community
    withdrawmoney = WithDraw.objects.filter(**kwargs).aggregate(Sum("money"))['money__sum'] 
 
    if withdrawmoney:
        left = income_total - withdrawmoney
    else:
        left = income_total 
        
    return round(income_total,2), round(expend_total,2), round(left,2), round(income_today,2)