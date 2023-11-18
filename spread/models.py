from statistics import mode
from django.db import models
from community.models import Community


class Spread(models.Model):
    """
    活动表
    """
    # 活动表题
    title =  models.CharField(max_length = 256)
    # 跳转连接
    url = models.CharField(max_length = 256, null = True)
    # 活动图片
    image = models.CharField(max_length = 256, null = True)
    # 创建日期
    date = models.DateTimeField(auto_now_add = True)

    # 活动内容
    content = models.TextField(null = True)
    DRAFT = 0 # 草稿
    AVAILABLE = 1  # 可用
    OUTDATE = 2 # 已过期
    # 活动状态
    status = models.PositiveSmallIntegerField( default = 0)
    
    # community 字段为空时，代表是平台发送的活动
    community = models.ForeignKey(Community, on_delete=models.CASCADE, null=True )
    
    def getstatus (self):
        return [self.DRAFT, self.AVAILABLE, self.OUTDATE]

    class Meta:
        db_table = "spread"
        default_permissions = ()
        permissions = [("addspread", "活动管理")]
