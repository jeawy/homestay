from statistics import mode
from django.db import models
from django.db.models.base import Model
from area.models import Area
from appuser.models import AdaptorUser as User
from organize.models import Organize
from django.contrib.auth.models import Permission 

class Community(models.Model):
    """
    小区表:
    权限：仅平台管理员，也就是超级管理员可以管理小区
    """
    uuid = models.CharField(max_length= 64, unique=True) # UUID
    # 创建者
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    # 小区基本情况介绍
    detail = models.TextField(null = True)
    # 小区名字
    name = models.CharField(max_length=256)
    # 小区所在区县
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True)
    # 小区的详细地址
    address = models.CharField(max_length= 128, null=True)
    # 社区
    shequ = models.CharField(max_length=128, null = True)
    # 街道办
    jiedaoban = models.CharField(max_length=128, null = True)
    # 小区所在位置的经纬度
    longitude = models.CharField(max_length=128, null=True)
    latitude = models.CharField(max_length=128, null=True)
    date = models.DateTimeField(auto_now_add=True)
    AVAILABLE = 1
    NOTAVAILABLE = 0 
    status = models.PositiveSmallIntegerField(default=AVAILABLE)

    # IT管理员:负责管理小区的权限分配、基本信息(开放给物业可编辑的物业和小区信息)
    # 导入物业员工信息
    IT_MANAGER = models.ForeignKey(User, related_name="itmanager", on_delete=models.SET_NULL, null=True)
    
    # 物业管理公司
    organize = models.ForeignKey(Organize,  on_delete=models.PROTECT)
    # 以下是小区公示信息字段
    
    #############
    # 以下是小区的物业公示信息部分
    #############
    # 物业服务等级: 一级
    service_level = models.CharField(max_length=56, null=True)
    # 物业收费等级: 一级
    fee_level = models.CharField(max_length=56, null=True)
    
    # 收费等级仅用作公示使用，不用做实际物业费收费标准，
    # 物业费收费标准按照收费制度，与每一户绑定
    # 1.5元每月
    fee_standand = models.CharField(max_length=56, null=True)
    # 物业收费方式
    fee_way = models.CharField(max_length=56, null=True)
    # 合同
    contract = models.TextField(null = True)
    
    # 物业经理姓名、职务、联系电话、物业经理头像
    manager_name = models.CharField(max_length=32, null=True)
    manager_position = models.CharField(max_length=32, null=True)
    manager_phone = models.CharField(max_length=12, null=True)
    manager_photo = models.CharField(max_length=256, null=True)

    # 维保单位营业执照
    weibao_license = models.CharField(max_length=256, null=True)

    # 电子印章
    signet = models.CharField(max_length=256, null=True)

    # 物业客服电话
    tel = models.CharField(max_length=18 , null=True)
    
    # 是否开启报修短信通知，如果开启：1，关闭：0
    OPEN = 1 
    CLOSE = 0
    switch_repair_phone = models.PositiveSmallIntegerField(default=OPEN)
    # 报修服务短信通知的接收电话
    repair_phone = models.CharField(max_length=11 , null=True)
    
    # 是否开启有偿服务短信通知，如果开启：1，关闭：0
    OPEN = 1 
    CLOSE = 0
    switch_aid_phone = models.PositiveSmallIntegerField(default=OPEN)
    # 有偿服务短信通知的接收电话
    aid_phone = models.CharField(max_length=11 , null=True)
 
    

    # 平台抽成比例只有超级用户可以修改
    # 互助平台分成比例，默认10%(含支付宝或者微信收取的手续费)
    aid_commission_rate = models.FloatField(default = 0.1)

    # 固定及非固定物业费平台分成比例，默认0.6%(这0.6%是支付宝或者微信收取的)
    fee_commission_rate = models.FloatField(default = 0.006)

    # 物业费有偿服务平台分成比例，默认10%(含支付宝或者微信收取的手续费)
    paidservice_commission_rate = models.FloatField(default = 0.1)


    # 提现银行卡信息 
    # 户主:物业是企业信息，户主姓名不一定
    bank_owner_name = models.CharField(max_length=56, null = True)
    # 银行名称
    bank_name = models.CharField(max_length=56, null = True)
    # 开户行
    deposit_bank = models.CharField(max_length=56, null = True)
    # 银行账号
    bank_number = models.CharField(max_length=56, null = True)
    
    # 小区总面积数：单位平米
    total_area = models.PositiveIntegerField(null = True)
    # 小区总户数
    total_rooms = models.PositiveIntegerField(null = True)
    

    # 额外字段
    extra_content = models.TextField(null = True)
    

    # 以下字段是为了快速查询做的统计数据，由定时器统一更新
    # 总支出：如短信购买等
    expend_total = models.FloatField(null = True)
    # 总收入
    income_total = models.FloatField(null = True)
    # 总余额：仅PC端可见
    money_left = models.FloatField(null = True)
    
    # 今日收入：仅PC端可见
    today_income_money = models.FloatField(null = True)

    # 短信余额
    msg_left = models.PositiveIntegerField(null = True)
    
    # 小区物业在微信中的子商户号
    # 该字段如何设置了，那么物业费将会直接支付到该账户中
    # 否则会先支付到平台账户中
    wx_sub_mch_id = models.CharField(max_length=28, null = True)


    # 短信配置：多个负责人电话用逗号隔开
    # 有偿服务通知人配置
    paidservice_msg = models.CharField(max_length=56, null=True)
    # 报修人配置
    repaire_msg = models.CharField(max_length=56, null=True)
    # 账单人配置,有人支付物业费之后，就会有提醒
    fee_msg = models.CharField(max_length=56, null=True)
    
    # 物业公司的短信签名ID，需要找国阳云客服联系
    smsSignId = models.CharField(max_length=56, null=True)
    class Meta:
        default_permissions = ()
        ordering = ['name']
        permissions = [("manage_community","物业管理公示信息")]


class Staff(models.Model):
    """
    物业员工表
    """
    user = models.ForeignKey(User, related_name="community_users", on_delete=models.CASCADE)
    community = models.ForeignKey(Community, related_name="staff_community", on_delete=models.CASCADE)
    # 角色权限
    permissions = models.ManyToManyField(Permission, related_name='staff_permissions')
    
    class Meta:
        default_permissions = ()
        permissions = [("manage_staff","管理物业员工")]
        constraints = [
            models.UniqueConstraint (
                fields=['user', 'community'],
                name = 'unique_staff_community'
            )
        ]
        
 
class Proprietor(models.Model):
    """
    业主关注小区表。
    业主关注小区后，默认展示为本小区未认证业主，当permission中有业主角色的时候，
    """
    user = models.ForeignKey(User, related_name="community_proprietor_users", on_delete=models.CASCADE)
    community = models.ForeignKey(Community, related_name="proprietor_community", on_delete=models.CASCADE)
    # 是否已认证为业主
    NO = 0 # 未认证
    YES = 1 # 已认证
    certificated = models.PositiveSmallIntegerField(default = NO)
    
    class Meta:
        default_permissions = () 
        constraints = [
            models.UniqueConstraint (
                fields=['user', 'community'],
                name = 'unique_proprietor_community'
            )
        ]
        

