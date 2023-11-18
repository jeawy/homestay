############################################
# 固定性收费（物业费）与非固定性收费计算
############################################
import logging
import pdb
import uuid
import time
from datetime import date, datetime
from property.code import SUCCESS, ERROR
from common.utils import get_final_date, diff_month
from building.models import RoomFixedFeeDetail, RoomDynamicFeeDetail, RoomFeeOrders
from django.conf import settings
from property.billno import get_fee_bill_no
from common.logutils import getLogger
from community.comm_statistics import community_statatics
logger = getLogger(True, 'building_fee_order', False)
from dateutil.relativedelta import SU, relativedelta
from fee.comm import   get_feetype_txt 
from webcoin.comm import add_webcoin


def delete_unpay_bills():
    """
    删除未支付的订单
    """
    # 1 固定收费账单：删除RoomFeeOrders，将room的cal_fee_status字段设置为未计算状态
    #               以便重新计算
    # 2 非固定收费账单：删除RoomFeeOrders，RoomDynamicFeeDetail的cal_fee_status
    #               字段设置为未计算状态以便重新计算
    pass

def fixedfee_calculate(room, final_date=None):
    """
    计算房屋的固定费率
    final_date 物业或者业主可以自己设定final_date，
    如果自己设定了final_date
    则优先使用自己设定的final_date
    同时生成订单信息
    """
    if room.arrearage_start_date is None:
        return ERROR, "未设定上次交费时间，无法计算需要交纳的物业费"

    if room.fixed_fee is None:
        return ERROR, "未设定收费制，无法计算需要交纳的物业费"

    if room.area is None:
        return ERROR, "房屋基本信息（面积）不全,无法计算需要交纳的物业费"

    next_season_day = get_final_date()
    if diff_month(next_season_day, room.arrearage_start_date) > 6:
        # 超过6个月未交费，设置为欠费状态，更新应缴费至哪一天，以及欠费金额
        room.status = room.ARREARAGED 
        room.save()

    if final_date is None:
        final_date = next_season_day

    if room.arrearage_start_date >= final_date:
        # 这种情况就是物业费提前交了，比如当前是第一季度的物业费，但是
        # 这个房屋已经交到第四个季度了
        if room.fee_status == room.ARREARAGED:
            # 将已欠费状态的房屋更新为正常
            room.fee_status = room.NORMAL
            room.money = 0
            room.save()
        return SUCCESS, "物业费已缴清"

    # 需要交几个月的物业费
    fee_months = diff_month(final_date, room.arrearage_start_date)
    # 固定收费项
    items = room.fixed_fee.fixed_fee_item.all()
    date_detail = room.arrearage_start_date.strftime(settings.DATEFORMAT) +\
        "-" + final_date.strftime(settings.DATEFORMAT)
    total_money = 0  # 总金额
    bill = create_fixedfee_order(room, 999999, date_detail, room.owner, room.arrearage_start_date, final_date)
    # 删除原来的
    RoomFixedFeeDetail.objects.filter(
        room=room, 
        bill=bill,
    ).delete()
    for item in items:
        # # 每月/每户
        item_money = 0
        if item.feetype == item.TYPE_NO_NEED_AREA:
            item_money = fee_months * item.money
        else:
            # 每月/每平米
            item_money = fee_months * item.money * room.area
        total_money += item_money
         
        feedetail = RoomFixedFeeDetail()
        feedetail.room = room 
        feedetail.bill = bill
        feedetail.uuid = uuid.uuid4()
        feedetail.months = fee_months
        feedetail.feetype = item.feetype
        feedetail.feename = item.name
        feedetail.feeprice = item.money
        feedetail.money = item_money
        feedetail.detail = date_detail + \
            item.name +"("+ get_feetype_txt(item.feetype)+str(item.money)+"元)共计: " + str(round(item_money,2)) + "元"
        feedetail.save()

    room.arrearage_end_date = final_date
    room.arrearage = total_money
    room.cal_fee_status = room.CALCALATED  # 已更新
    room.save()

    # 更新订单金额信息
    date_detail = date_detail + "【物业费】"
    bill.money = total_money
    bill.detail = date_detail 
    bill.save()

    if diff_month(next_season_day, room.arrearage_start_date) > 6 and final_date is None:
        # 超过6个月未交费，设置为欠费状态，更新应缴费至哪一天，以及欠费金额
        room.status = room.ARREARAGED 
        room.arrearage = total_money
        room.arrearage_end_date = next_season_day
        room.save()

    return SUCCESS, "计算完成"


def get_dynamic_start_date(room, dynamicfee):
    """
    获取某个房屋某条非固定收费项的上次交费到的日期
    RoomDynamicFeeDetail中的end_date
    """
    try:
        dynamicfee = RoomDynamicFeeDetail.objects.get(room=room,
                                                      dynamicfee=dynamicfee)

        if dynamicfee.end_date is None:
            # 一次都未支付过，返回start_date
            return SUCCESS, dynamicfee.start_date
        else:
            # 上次支付到的日期
            return SUCCESS, dynamicfee.end_date
    except RoomDynamicFeeDetail.DoesNotExist:
        # 该房屋不存在该收费项
        return ERROR, None


def dynamicfee_calculate(room,  user, force = False):
    """
    计算房屋的非固定费率， 如停车费
    force 表示是否强制更新账单，用户手动设置续费日期时用到
    """
    dynamicfees = RoomDynamicFeeDetail.objects.filter(
        room = room) 
    for dynamicfee_detail in dynamicfees:
        if dynamicfee_detail.cal_fee_status == dynamicfee_detail.CALCALATED and force == False:
            # 已更新，且不需要强制更新
            continue

        dynamicfee = dynamicfee_detail.dynamicfee
        status, start_date = get_dynamic_start_date(room, dynamicfee)
        if status == ERROR:
            logger.debug("{0}[{1}]该房屋不存在该收费项".format(room.name, str(room.id)))
            continue  # 进行下一个计算
        final_date = start_date + relativedelta(months=3) # 三个月的订单
        if dynamicfee.feetype == dynamicfee.TYPE_NEED_AREA:
            if room.area is None:
                logger.debug("{0}[{1}]房屋基本信息（面积）不全,无法计算需要交纳的费用".format(
                    room.name, str(room.id)))
                return ERROR, "房屋基本信息（面积）不全,无法计算需要交纳的费用"

        # 需要交几个月的物业费
        fee_months = diff_month(final_date, start_date)
     
        date_detail = start_date.strftime(settings.DATEFORMAT) +\
            "-" + final_date.strftime(settings.DATEFORMAT)
        money = 99999999
        if dynamicfee.TYPE_NEED_AREA:
            money = dynamicfee.money * fee_months * room.area
        else:
            money = dynamicfee.money * fee_months 

        detail = date_detail + dynamicfee.name + "("\
          + get_feetype_txt(dynamicfee.feetype)+str(dynamicfee.money)+  "元)共计: " + str(round(money,2)) + "元" 
        # 生成订单
        orderuuid = create_dynamic_order(
            room, dynamicfee_detail, money, detail, user, start_date,  final_date)
        dynamicfee_detail.cal_fee_status = dynamicfee_detail.CALCALATED
        dynamicfee_detail.save()

def single_dynamicfee_calculate(dynamicfeedetail, final_date, user):
    """
    计算房屋的单个非固定费率， 如停车费
    """

    room = dynamicfeedetail.room
    item = dynamicfeedetail.dynamicfee
    status, start_date = get_dynamic_start_date(room, item)
    if status == ERROR:
        return ERROR, "收费项未绑定"

    if final_date is None:
        final_date = get_final_date()

    if final_date < start_date:
        # 这种情况就是费提前交了，比如当前是第一季度的费，但是
        # 这个房屋已经交到第四个季度了
        return SUCCESS, "已更新"

    if item.feetype == item.TYPE_NEED_AREA:
        if room.area is None:
            return ERROR, "房屋基本信息（面积）不全,无法计算需要交纳的费用"

    # 需要交几个月的物业费
    fee_months = diff_month(final_date, start_date)

    date_detail = start_date.strftime(settings.DATEFORMAT) +\
        "-" + final_date.strftime(settings.DATEFORMAT)
    
    money = 999999
    if item.TYPE_NEED_AREA:
        money = item.money * fee_months * room.area
    else:
        money = item.money * fee_months

    detail = date_detail + item.name + "(" +  get_feetype_txt(item.feetype)+str(item.money)+   \
        "元)共计: " + str(round(money,2)) + "元"

    dynamicfeedetail.cal_fee_status = dynamicfeedetail.CALCALATED
    dynamicfeedetail.save()
    # 生成订单
    orderuuid = create_dynamic_order(
        room, dynamicfeedetail,money, detail, user, start_date,  final_date)

    return SUCCESS, orderuuid


def create_dynamic_order(room, dynamicfeedetail, money, detail, user, start_date,  final_date):
    # 生成非固定收费项订单
    # 删除原来未支付的
    RoomFeeOrders.objects.filter(dynamicfee_detail=dynamicfeedetail,
                                 status=RoomFeeOrders.NON_PAYMENT).delete()
    # 新建订单
    org = room.community.organize  # 物业  # 物业 
    billno = get_fee_bill_no(org, user, geetype="D")
    order = RoomFeeOrders()
    order.uuid = uuid.uuid4()
    order.subject = "【{0}】{1}".format(
        org.alias, dynamicfeedetail.dynamicfee.name)
    order.billno = billno
    order.money = money
    order.room = room

    order.user = user
    order.community = room.community
    order.org = org
    order.detail = detail
    order.feetype = order.DYNAMIC

    order.dynamicfee_detail = dynamicfeedetail
    order.feename = dynamicfeedetail.dynamicfee.name
    order.start_date = start_date
    order.end_date = final_date 
    order.save()
    return str(order.uuid)


def create_fixedfee_order(room, money, detail, user, start_date,  final_date):
    # 生成固定收费项订单
    # 删除原来未支付的
    RoomFeeOrders.objects.filter(room=room,
                                 feetype=RoomFeeOrders.FIXED,
                                 status=RoomFeeOrders.NON_PAYMENT).delete()
    # 新建订单
    org = room.community.organize  # 物业
    billno = get_fee_bill_no(org, user, geetype="F")
    order = RoomFeeOrders()
    order.uuid = uuid.uuid4()
    order.subject = "【{0}】物业费".format(org.alias )
    order.billno = billno
    order.money =  money
    order.room = room 
    order.user = user
    order.community = room.community
    order.org = org
    order.detail = detail 
 
    order.feename = "物业费"
    order.start_date = start_date
    order.end_date = final_date
    order.feetype = order.FIXED
    order.save()
    return order


def fee_end_date(order):
    """
    物业费或者非固定收费支付之后，更新最新的到期时间
    同时增加积分
    """
    # 更新交费到期时间
    community_statatics(order.community) # 更新收入
    if order.feetype == order.DYNAMIC:
        # 非固定性收费
        # 将order 中的end_date更新到RoomDynamicFeeDetail中的end_date中
        order.dynamicfee_detail.end_date = order.end_date
        # 设置dynamicfee_detail为未更新，以便继续更新账单
        order.dynamicfee_detail.cal_fee_status = order.dynamicfee_detail.NOT_CALCALATED
        order.dynamicfee_detail.save()
    else:
        # 固定性收费
        order.room.arrearage_start_date = order.end_date 
        order.room.arrearage = 0
        # 设置为未更新，以便计算新的账单
        order.room.cal_fee_status = order.room.NOT_CALCALATED
        order.room.save()
    
    # 物业缴费增加积分
    add_webcoin(0, order.user,order.uuid,  order.money )


def get_bill(room, final_date):
    """
    获取账单
    """
    roomorder_dict = {}
    if room.cal_fee_status == room.NOT_CALCALATED:
        # 固定费率计算
        cal_result = fixedfee_calculate(room, final_date)
        logger.debug("固定费率计算结果：" + str(cal_result))

    # 非固定费率计算
    dynamicfee_calculate(room,  room.owner)
      
    roomorder_dict['uuid'] = room.uuid
    roomorder_dict['name'] = room.name
    roomorder_dict['area'] = room.area
    roomorder_dict['fee_status'] = room.fee_status
    roomorder_dict['status'] = room.status
    roomorder_dict['money'] = room.arrearage
    roomorder_dict['unitname'] = room.unit.name
    roomorder_dict['buildingname'] = room.unit.building.name
    roomorder_dict['communityname'] = room.community.name

    roomorder_dict['orgname'] = room.community.organize.alias
    roomorder_dict['orgtel'] = room.community.tel
    roomorder_dict['parent'] = False  # 方便前端UI控制
    if room.owner:
        roomorder_dict['username'] = room.owner.username
        roomorder_dict['phone'] = room.owner.phone
    else:
        roomorder_dict['username'] = ""
        roomorder_dict['phone'] = ""

    roomorder_dict['fixed_fee'] = {}
    if room.fixed_fee:
        roomorder_dict['fixed_fee']['name'] = room.fixed_fee.name
        roomorder_dict['fixed_fee']['uuid'] = room.fixed_fee.uuid
     
    
    # 查询收费账单
    # 固定性收费(如物业费)
    bill = RoomFeeOrders.objects.filter(room=room,
                                feetype=RoomFeeOrders.FIXED)\
                                    .latest("id")

    # 非固定性收费(如停车费)
    dynamicfees = list(RoomFeeOrders.objects.
                    filter(status=RoomFeeOrders.NON_PAYMENT,
                    feetype = RoomFeeOrders.DYNAMIC, 
                            room=room).values(
                                "uuid",
                                "billno", 
                                "dynamicfee_detail__uuid",
                                "dynamicfee_detail__dynamicfee__name",
                                "money", 
                                "detail",
                                "start_date",
                                "end_date"))
    
    for dynamicfee in dynamicfees:
        end_date = dynamicfee['end_date']
        start_date = dynamicfee['start_date']
        dynamic_final_date = final_date
        if end_date > dynamic_final_date:
            dynamic_final_date = end_date

        dynamicfee['end_date'] = time.mktime(end_date.timetuple())
        dynamicfee['start_date'] = time.mktime(start_date.timetuple())
        dynamicfee['end_date_pre'] = [
            time.mktime(dynamic_final_date.timetuple()),
            time.mktime(
                (dynamic_final_date + relativedelta(months=3)).timetuple()),
            time.mktime(
                (dynamic_final_date + relativedelta(months=6)).timetuple()),
            time.mktime(
                (dynamic_final_date + relativedelta(months=9)).timetuple()),
            time.mktime(
                (dynamic_final_date + relativedelta(months=12)).timetuple()),
        ]
        dynamicfee['children'] = False

    roomorder_dict['dynamicfees'] = dynamicfees
     
    if room.arrearage_start_date is not None:
        roomorder_dict['arrearage_start_date'] = time.mktime(
            room.arrearage_start_date.timetuple())
    else:
        roomorder_dict['arrearage_start_date'] = None
         
    if room.arrearage_end_date is not None:
        roomorder_dict['arrearage_end_date'] = time.mktime(
            room.arrearage_end_date.timetuple())

        fixed_final_date = final_date
        if bill.status == bill.PAYED:
            # 已支付的订单，预付时间以arrearage_end_date为准，
            # 未支付的，以arrearage_start_date为准
            if room.arrearage_end_date > final_date:
                fixed_final_date = room.arrearage_end_date
            elif room.arrearage_end_date == final_date:
                fixed_final_date = final_date + relativedelta(months=3)

        else:
            if room.arrearage_start_date > final_date:
                fixed_final_date = room.arrearage_start_date
            elif room.arrearage_start_date == final_date:
                fixed_final_date = final_date + relativedelta(months=3)

        roomorder_dict['arrearage_end_date_pre'] = [
            time.mktime(fixed_final_date.timetuple()),
            time.mktime(
                (fixed_final_date + relativedelta(months=3)).timetuple()),
            time.mktime(
                (fixed_final_date + relativedelta(months=6)).timetuple()),
            time.mktime(
                (fixed_final_date + relativedelta(months=9)).timetuple()),
            time.mktime(
                (fixed_final_date + relativedelta(months=12)).timetuple()),
        ]
    else:
        roomorder_dict['arrearage_end_date'] = None
            
    roomorder_dict['fixedfees'] = list(RoomFixedFeeDetail.objects.
                                    filter(bill=bill,
                                            room=room).values("uuid",
                                                                "feename", "money",
                                                                "detail"))
    roomorder_dict['bill'] = { 
        "billno":bill.billno,
        "uuid":bill.uuid
    }
    roomorder_dict['billstatus'] = bill.status
    
    return roomorder_dict