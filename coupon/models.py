 
from django.db import models
from basedatas.models import BaseDate
from appuser.models import AdaptorUser as User


class Coupon(BaseDate):
    """
    优惠券：折扣券及满减券，目前只有这两种2022年7月14日10:31:34
    """
    uuid = models.CharField(max_length= 64, unique=True)
    # 优惠券的标题：如：洗车券
    name = models.CharField(max_length= 56)

    DRAFT = 0 # 未发布
    PUBLISHED = 1 # 已发布
    OVERTIMED = 2 # 已过期
    status = models.PositiveSmallIntegerField(default = DRAFT)
    # 谁创建的优惠券
    user = models.ForeignKey(User, related_name = "owner", on_delete = models.PROTECT) 
    DISCOUNT = 0  # 折扣券：如8折
    REDUCTION = 1 # 满减券：如满100减5元
    coupontype = models.PositiveSmallIntegerField(default = REDUCTION)
    # 购买用户
    buyers = models.ManyToManyField(User, related_name = "buyers")

    # 有效期的起止日期
    start = models.DateField()
    end = models.DateField()
    
    # 使用规则
    rules = models.TextField(null = True)
    
    # 折扣：不能大于10，不能小于1
    discount = models.FloatField(null=True)
    
    # 满减金额：满top_money减reduce_money，
    # reduce_money 不能大于top_money
    top_money = models.FloatField(null=True)
    reduce_money = models.FloatField(null=True)
    # 其他字段：如联系方式、地址等自定义信息
    extras = models.TextField(null = True)
    
    # 价格，如果price =0或者null,则表示免费领取
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True )
    # 允许购买的最大数量，为0时，表示不限制
    limit = models.PositiveSmallIntegerField(default=0)
    class Meta:
        default_permissions = () 

