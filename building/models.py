#! -*- coding: utf-8 -*-
from email.policy import default
from statistics import mode
from django.db import models
from django.utils.translation import ugettext_lazy as _
from basedatas.models import BaseDate, PayBase
from appuser.models import AdaptorUser as User
from community.models import Community
from fee.models import DynamicFee, FixedFee, FixedItemFee
from organize.models import Organize


class Building(BaseDate):
    """
    资产：楼
    """

    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    uuid = models.CharField(max_length=64, unique=True)  # UUID
    name = models.CharField(max_length=28)  # 楼号

    class Meta:
        # 角色管理的权限
        default_permissions = ()
        permissions = [('manage_building', '管理资产的权限.')]
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['community', 'name'],
                                    name='unique_asset_community_name')
        ]


class Unit(BaseDate):
    """
    单元信息表
    """
    building = models.ForeignKey(
        Building, related_name="building_unit", on_delete=models.CASCADE)
    uuid = models.CharField(max_length=64, unique=True)  # UUID
    name = models.CharField(max_length=28)  # 单元号

    class Meta:
        default_permissions = ()
        ordering = ['building', 'name']
        constraints = [
            models.UniqueConstraint(fields=['building', 'name'],
                                    name='unique_asset_building_name')
        ]


class Room(BaseDate):
    """
    房屋信息:
    注意：一个人既可能是业主，也有可能是另一个地方的租客，所以在这个表中
    不能绑定用户信息
    """
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    # 存储起来，一是建立起来基本不修改，二是为了加快查询速度
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    uuid = models.CharField(max_length=64, unique=True)  # UUID
    name = models.CharField(max_length=28)  # 房号
    area = models.FloatField(null=True)  # 面积
    # LIVING = 0
    NOT_LIVING = 0  # 空置
    LIVING = 1  # 已入住
    status = models.PositiveSmallIntegerField(default=LIVING)

    # #########################
    # 以下为物业费相关字段
    # #########################
      
    # 统一收费：如一费制
    fixed_fee = models.ForeignKey(
        FixedFee, on_delete=models.SET_NULL, null=True)

    # 上次交费到的日期
    arrearage_start_date = models.DateField(null=True)
    # 当前应交费至。
    arrearage_end_date = models.DateField(null=True)

    # 欠费金额：通过后台程序定时计算，加快查询速度
    # 每月5号之后更新或者用户手动更新
    # 如果系统繁忙的话，将来更新周期会拉长
    arrearage = models.FloatField(null=True)

    NORMAL = 1  # 正常
    ARREARAGED = 0  # 已欠费
    fee_status = models.PositiveSmallIntegerField(default=NORMAL)
    #  当前使用人，可以是租户、业主，方便支付物业费等。
    owner = models.ForeignKey(User, on_delete=models.SET_NULL,
                              null=True, related_name="room_owner")
    # 业主家人信息
    roomers = models.ManyToManyField(User)

    # 收费金额是否已更新过
    CALCALATED = 1  # 已更新
    NOT_CALCALATED = 0
    cal_fee_status = models.PositiveSmallIntegerField(default=NOT_CALCALATED)
    
    # 近期是否已催缴物业费，催缴之后设置为1，代表已催缴过了。每月重置一次，
    press_fee = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        default_permissions = ()
        ordering = ['unit', 'name']
        constraints = [
            models.UniqueConstraint(fields=['unit', 'name'],
                                    name='unique_asset_unit_name')
        ]

 
class RoomDynamicFeeDetail(models.Model):
    """
    非固定收费(如停车费等)应交费明细
    # 非固定收费订单在到期之前（end_date)15天内更新，订单状态，用户可以提前支付
    """
    uuid = models.CharField(max_length=64, unique=True)  # UUID
            
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    dynamicfee = models.ForeignKey(DynamicFee, on_delete=models.CASCADE)
     
    # 账单费用的起始日期
    start_date = models.DateField()
    # 已交费至日期，只要订单支付成功，
    # 就更新这个字段，未支付不更新
    # 这个字段表示用户费用支付到什么时候了。
    end_date = models.DateField(null = True)
     
     
    # 收费金额是否已更新过
    CALCALATED = 1  # 已更新
    NOT_CALCALATED = 0
    cal_fee_status = models.PositiveSmallIntegerField(default=NOT_CALCALATED)
    
    class Meta:
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(fields=['room', 'dynamicfee'],
                                    name='unique_room_dynamicfee_item')
        ]

class RoomFeeOrders(PayBase):
    """
    交费记录表
    # 超过24小时未支付的订单会被删除，物业费会重新计算（需要将Room和RoomDynamicFeeDetail
    # 的cal_fee_status字段设置为未计算，以便重新开始计算
    """
    # 删除房屋的时候，不能删除
    room = models.ForeignKey(Room, on_delete=models.PROTECT)
    # 缴费人
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    # 加快查询速度
    community = models.ForeignKey(Community, on_delete=models.PROTECT)
     
    # 物业
    org = models.ForeignKey(Organize, on_delete=models.PROTECT)
    # 支付说明：如20211001-20220910物业费
    detail = models.CharField(max_length=256)
    
    # 固定收费、非固定收费
    FIXED = 0 # 固定性收费
    DYNAMIC = 1 # 非固定性收费
    feetype = models.PositiveSmallIntegerField(default= FIXED )
    #  
    dynamicfee_detail = models.ForeignKey(RoomDynamicFeeDetail, null=True, on_delete=models.SET_NULL)
    # 收费项名称
    feename = models.CharField(max_length= 128)
    # 账单费用的起始日期
    start_date = models.DateField()
    # 账单费用的结束日期
    end_date = models.DateField()

    # 未支付
    NON_PAYMENT = 0
    # 已支付
    PAYED = 2
    UNUSUAL = 3  # 异常订单
    status = models.SmallIntegerField(default=NON_PAYMENT)
    
    # 备注信息
    remark = models.CharField(max_length= 256, null = True)
    class Meta:
        ordering = ['-date']
        default_permissions = ()
        permissions = [("manage_fee", "小区物业费查看、打印")]


class RoomFixedFeeDetail(models.Model):
    """
    固定收费应交费明细
    """
    uuid = models.CharField(max_length=64, unique=True)  # UUID
    # 在哪个账单中交的
    # 为空时，代表这个账单还没有交费
    bill = models.ForeignKey(RoomFeeOrders,
                             on_delete=models.SET_NULL, null=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
     
    # 当时的收费项名称
    feename = models.CharField(max_length=64 )  
    # 当时的费用单价
    feeprice = models.FloatField(default=0 )   
    # 当时的收费方式：
    TYPE_NEED_AREA = 0  # 每月/每平米
    TYPE_NO_NEED_AREA = 1  # 每月/每户
    feetype = models.PositiveSmallIntegerField(default=TYPE_NEED_AREA ) 
    # 交费周期(以月为单位)  
    months = models.PositiveSmallIntegerField(default=3 )   
    # 收费金额
    money = models.FloatField()
    # 说明
    detail = models.CharField(max_length=128)
    
    class Meta:
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(fields=['room', 'item', 'bill'],
                                    name='unique_fixedfee_item')
        ]


class RoomFeeOpHistory(models.Model):
    """
    物业费的历史操作记录
    如：修改欠费起始日期、修改缴费制、修改非统一性收费制
    """
    uuid = models.CharField(max_length=64, unique=True)  # UUID
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    # 操作员
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now=True)
    # 操作说明
    detail = models.TextField()

    class Meta:
        default_permissions = ()


class RoomReminderRecord(models.Model):
    """
    缴费提醒记录
    """
    uuid = models.CharField(max_length=64, unique=True)  # UUID
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    # 操作员
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # 提醒日期
    reminder_date = models.DateTimeField()

    MESSAGE = 0  # 短信
    VISITED = 1  # 上门
    reminder_type = models.PositiveSmallIntegerField(default=MESSAGE)
    # 操作说明（如果是通过短信发的提醒，这存储的是短信内容，上门时，存储的是图片的路径
    detail = models.TextField()

    class Meta:
        ordering = ['-reminder_date']
        default_permissions = ()



class FeeRate(models.Model):
    """
    物业费缴费率统计，按季度统计
    """
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    # 缴费率, 有的小区无法计算缴费率，但是曲线应该展示
    rate = models.FloatField(null = True)
    date = models.DateTimeField(auto_now_add=True)
    # 2022年4季度
    season = models.CharField(max_length=56)
    class Meta:
        default_permissions = () 
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(fields=['community', 'season'],
                                    name='unique_community_feerate')
        ]
