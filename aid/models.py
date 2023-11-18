import os
from django.db import models
from basedatas.models import BaseDate, PayBase
from building.models import Unit
from community.models import Community
from appuser.models import AdaptorUser as User 
from django.conf import settings

#  有偿互助
class Aid(BaseDate):
    """
    有偿互助类
    """
    uuid = models.CharField(max_length=64, unique=True)
    # 求助人
    user = models.ForeignKey(
        User, related_name="helper", on_delete=models.PROTECT)
    # 标题
    title = models.CharField(max_length=64)
    # 内容
    content = models.TextField(null=True)
    # 机密信息
    secretinfo = models.TextField(null=True)
     
    community = models.ForeignKey(Community, on_delete=models.PROTECT)
    # 费用
    money = models.FloatField()
    # 是否要求必须是认证业主接单，默认是1
    YES = 1
    NO = 0
    need_propertior = models.PositiveSmallIntegerField(default=YES)
    # 截止日期
    end_date = models.DateTimeField(null=True)
    # 是否公开自己的电话、房号
    publich_myinfo = models.PositiveSmallIntegerField(default=NO)
    # 是否已支付了费用
    REFUNDING = 2 # 申请退款
    REFUNDED = 3 # 已退款
    payed = models.PositiveSmallIntegerField(default=NO)

    # 帮助人
    answer = models.ForeignKey(User, related_name="answer", null=True,
                               on_delete=models.PROTECT)
    # 接单人的额外信息，比如当时的评分、服务次数，认证信息等，用
    # JSON的格式存储，加快查询速度
    answer_extra = models.TextField(null = True)
    # 接单时间
    accepted_date = models.DateTimeField(null=True)
    DRAFT = 0  # 暂存
    OPEN = 1  # 等待接单，可以被人刷到
    CLOSD = 2  # 已关闭
    ACCEPTED = 3  # 已接单
    FINISHED = 4  # 已完成
    COMMENTED = 5  # 已评价
    status = models.PositiveSmallIntegerField(default=DRAFT)
    
    SELECTED = 0 #  报名备选模式，业主报名，发求助者自己选择服务这
    KNOCKED = 1 # 抢单模式
    mode =  models.PositiveSmallIntegerField(default = KNOCKED)
    # 互助类型：1 求助（需要别人帮忙）、2 提供帮助（主动发布的帮助别人的帖子）
    NEED_HELP = 1
    TO_HELP = 2
    aidtype = models.PositiveSmallIntegerField(default= NEED_HELP)
    
    # 完成日期
    finished_date = models.DateTimeField(null = True)
    # 接单人输入的完成内容
    comment = models.TextField(null = True)
    # 评分：给接单人的
    score = models.PositiveSmallIntegerField(null = True)

    class Meta:
        ordering = ['-date']
        default_permissions = ()


class AidCommunities(models.Model):
    """
    认证业主需来自哪些小区
    """
    aid = models.ForeignKey(Aid,  on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    class Meta:
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(fields = ['aid', 'community'], 
            name = "aid_community_unique")
        ]


class ImageQuerySet(models.QuerySet):
    def delete(self, *args, **kwargs):  
        for obj in self:
            path = os.path.join(settings.FILEPATH, obj.filepath)  
            if os.path.isfile(path):
                os.remove(path)
            obj.delete()


class AidImgs(models.Model):
    """
    图片表
    """
    aid = models.ForeignKey(Aid, related_name='aid', on_delete=models.CASCADE)
    # 附件名称
    filename = models.CharField(max_length=128)
    # 附件地址
    filepath = models.CharField(max_length=1024)

    objects = ImageQuerySet.as_manager()
    FROMAID = 0 # 来之求助
    FROMCOMMENT = 1 # 来自评论
    imgtype = models.PositiveSmallIntegerField(default = FROMAID)

    class Meta:
        default_permissions = ()


class Entries(models.Model):
    """
    报名表
    """ 
    date = models.DateTimeField(auto_now_add = True)
    aid = models.ForeignKey(Aid, on_delete=models.PROTECT )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # 截止报名时，该用户服务了几次，平均得分是多少
    # 这样设计表：一方面加快查询速度，
    # 一方面报名时的评价应该是固定的，不应该是动态计算的。
    score = models.PositiveSmallIntegerField(null = True) # 未收到评价时，评分为空。
    service_times = models.PositiveSmallIntegerField(default = 5)
    # 认证为业主的小区
    communityname = models.CharField(max_length=64, null = True)
    class Meta:
        ordering = ['-date']
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(fields = ['aid', 'user'], 
            name = "aid_entries_unique")
        ]


class AidOrders(PayBase):
    """
    支付表
    # 超时未支付也不需要删除
    """
    # 一个互助单只需要有一个订单即可
    aid = models.OneToOneField(Aid, on_delete=models.PROTECT   )
    # 订单创建人
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    # 加快查询速度
    community = models.ForeignKey(Community, on_delete=models.PROTECT) 
     
    # 未支付
    NON_PAYMENT = 0
    # 已支付
    PAYED = 2
    UNUSUAL = 3  # 异常订单
    status = models.SmallIntegerField(default=NON_PAYMENT)

    # 备注信息
    remark = models.CharField(max_length=256, null=True)

    class Meta:
        ordering = ['-date']
        default_permissions = ()
