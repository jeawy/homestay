from statistics import mode
from django.db import models 
from appuser.models import AdaptorUser as User
from community.models import Community
from organize.models import Organize


class Record(models.Model):
    """
    内容登记主表
    """
    uuid = models.CharField(max_length= 64, unique=True) # UUID
    # 小区，该字段并不限定登记仅在该小区进行，只是为了方便在小区范围内查询登记情况
    community = models.ForeignKey(Community, on_delete=models.SET_NULL, null=True)
    
    # 发起人
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    # 登记内容标题
    title = models.CharField(max_length=256)
    # 登记内容
    content = models.TextField()
    # 发起时间
    date = models.DateTimeField(auto_now_add=True)

    DRAFT = 0 # 草稿
    PUBLISHED = 1 # 已发布
    CANCEL = 2 # 已取消/已结束
    status = models.PositiveSmallIntegerField(default = PUBLISHED)
    # 登记截止时间
    deadline = models.DateTimeField(null = True)
    # 要求必须登录用户才可以登记
    # 默认为不要求： 0
    # 1 表示要求必须登录
    need_login = models.PositiveSmallIntegerField(default = 0)
    # 是否允许重复登记：仅仅对要求必须登录的登记记录有效
    # 默认为不允许： 0
    # 1 表示允许
    duplicate = models.PositiveSmallIntegerField(default = 1)
    # 是否公开用户登记情况
    # 默认为公开： 1
    # 0 表示不公开
    show_userinfo = models.PositiveSmallIntegerField(default = 1)

    # 当登记是由物业发的时候，该字段不能为空
    # 物业在移动端创建的时候，无法
    organize = models.ForeignKey(Organize, on_delete=models.CASCADE,  null = True)

    # 是否仅发起人可导出结果
    # 默认为： 1 仅发起人可导出结果
    # 0 表示所有人都可以导出结果
    # 2 表示当前物业员工都可以导出
    only_owner_export = models.PositiveSmallIntegerField(default = 1)

    # 二维码,用户扫码之后即可填写信息
    qrcode = models.CharField(max_length=256, null=True)
    # 是否开启登记通知，默认不开启
    notice = models.PositiveSmallIntegerField(default = 0)
    # 额外字段
    # actions 有sum：自动求和（仅数字列), 
    #           autoincrease:自增加，不需要用户填写，从1开始自增加， 如序号
    # 格式为:[{
    #    label: "成绩",
    #    type:"number",
    #    required:1, # 必填， 0 非必填 
    #    action:"sum" # 自动求和
    # },
    # {
    #    label: "是否入住",
    #    type:"string",
    #    required:1, # 必填， 0 非必填 
    #    action:"" # 自动求和
    # }]
    # 在excel中打印的时候，name是列名，列里的值从登记表中获取
    extra = models.TextField(null = True)
    # 标记列表：如“已处理”、“未处理”
    # 这样发起人就可以快速的标记登记人信息。
    # 这些标记会在excel中展示出来，标记可以取消
    tags = models.CharField(max_length=256, null=True)
    
    # 定时登记薄
    YES = 1 # 定时登记薄
    NO = 0 # 非定时登记薄
    autorecord = models.PositiveSmallIntegerField(default = NO)
    
    # 定时登记薄的类型
    EVERYDAY = 0 # 每天执行
    EVERYWEEK = 1 # 每周执行
    EVERYMONTH = 2 # 每月执行
    autotype = models.PositiveSmallIntegerField(default = NO)

    # 定时登记薄执行日期
    # 每天执行的定时器,该字段不需要存储数据，每天零时自动创建
    # 每周执行的定时器，该字段存储的是星期几，比如存储：1,3,5,7则表示
    #     每周星期一、三、五、日零时创建同样登记薄
    # 每月执行的定时器，该字段存储的是每月几号，比如存储：1,3,5,7则表示
    #     每月1号、3号、5号、7号零时创建同样登记薄，-1表示当月最后一天创建
    autodays = models.CharField(max_length=80, null=True)

    
    # 是否在移动端可见，通常应该场景为该登记只在小区内登记 
    available_appside = models.PositiveSmallIntegerField(default = YES)
    
    # 是否在小区的列表中展示，有些登记薄不方便的小区列表中公开展示
    show_in_list = models.PositiveSmallIntegerField(default = YES)
    
    # 登记人数上限，超过不允许登记，为空时，代表不限上限
    limits = models.PositiveIntegerField(null = True)

    # 是否允许登记人删除登记记录
    allow_delete = models.PositiveIntegerField(default = YES)

    # 是否允许登记人修改登记记录
    allow_modify = models.PositiveIntegerField(default = YES)

    class Meta:
        default_permissions = ()


class RecordUserInfo(models.Model):
    """
    登记记录表：记录登记的用户详细情况
    """

    uuid = models.CharField(max_length= 64, unique=True) # UUID
    record = models.ForeignKey(Record, related_name="userrecord", on_delete=models.CASCADE)
    # 登记人, 登记人可以为空，为空的时候，提供一个默认的登记人字段，
    # 直接添加登记人内容,如楼号
    recorder = models.ForeignKey(User, on_delete=models.SET_NULL, null = True) 
    # 登记时间
    date = models.DateTimeField(auto_now_add=True) 
    # 用户登记的数据，与record表中的extra字段一一对应，
    # 举例：extra：户名、温度
    # 那么：values:['1-2206','36.6']
    values = models.TextField(null = True) 
    # 标记列表：发起人打上的标记
    tags = models.CharField(max_length=256, null=True)
    class Meta:
        ordering = ['-id']
        default_permissions = ()