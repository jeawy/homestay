# 所有的订单号都在这个文件中生成方便后面修改
# M for 短信充值订单
# P for 有偿服务订单
# F for 物业费相关订单，FF固定物业费，FD非固定物业费，如停车费等。
# H for 互助单相关订单 
import pdb
from datetime import datetime

g_timestr = "%Y%m%d%H%M%S%f"

def get_aid_bill_no( user ):
    """
    互助单相关订单号
    H。
    """
    timestr = datetime.now().strftime(g_timestr)  
    orderno = "H"  +str(user.id) + "H" + timestr  
    return orderno

def get_fee_bill_no(org, user, geetype):
    """
    物业费相关订单号
    FF固定物业费，FD非固定物业费，如停车费等。
    """
    timestr = datetime.now().strftime(g_timestr) 
    if geetype == "D": # 非固定收费 
        orderno = "FD"  +str(org.id) + "FD" + timestr +"FD" + str(user.id)
    else: 
        orderno = "FF"  +str(org.id) + "FF" + timestr +"FF" + str(user.id)
    return orderno


def get_msg_bill_no( community, dates, spc):
    """
    生成短信充值订单编号
    # M 开头，表示是短信订单,
    并且用M分割了community id和spc id
    """
    orderno = "M" + str(community.id) +   "M" +  dates+"M"+str(spc.id)
    return orderno


def get_paidservice_bill_no(user, org=None):
    # 生成有偿服务订单号
    # P 开头，表示是有偿服务订单
    # org 为none时，代表生成第三方支付系统需要的订单号
    timestr = datetime.now().strftime(g_timestr)
    if org is None:
        # 第三方支付（支付宝、微信）需要的订单
        orderno = "P"  + timestr +"P" + str(user.id)
    else: 
        orderno = "P" +str(org.id)+"P" + timestr +"P" + str(user.id)
    return orderno
