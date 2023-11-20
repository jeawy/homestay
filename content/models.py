#! -*- coding: utf-8 -*-
from django.db import models

from basedatas.models import BaseDate
from appuser.models import AdaptorUser as User
from address.models import Address
from category.models import Category
from tags.models import Tags
from community.models import Community


class TxtContent(BaseDate):
    """内容管理：信息、公告、通知、社区见闻、内部内容表"""

    # 创建人
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="product_creator")
    # 图片
    picture = models.CharField(max_length=200,null=True)
    # 内容描述
    content = models.TextField(null=True)
    # 轮播图
    turns = models.TextField(null=True)
    uuid = models.CharField(max_length= 64, unique=True) # UUID
    # 详细内容
    detail = models.TextField(null=True) 
    # 标题
    title = models.CharField(max_length=200,null=False)
    INFORMATION = 0 # 百事通
    NOTIFICATION = 1 # 通知
    ANNOUNCEMENT = 2 # 公告 
    NEWS = 3 # 社区见闻，为了增加社区见闻的美观性，picture字段为必填
    INNER = 4 #内部文章，不在app中显示，或者只能通过app的活动页面点击进入的
    product_type = models.PositiveSmallIntegerField(default = INFORMATION)
    # 类别
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING,null= True, related_name="cat_product")
     
    tags = models.ManyToManyField(Tags)
    DRAFT = 0 
    PUBLISHED = 1
    # 商品状态
    status = models.PositiveSmallIntegerField(default = PUBLISHED) 
    YES = 1
    NO = 0 
    # 是否允许评论, 默认不开启评论
    allow_comment = models.PositiveSmallIntegerField(default = NO)
    
    class Meta:
        default_permissions = ()
        ordering = ['-date']
        permissions = [("manage_product", "发布、编辑：信息薄、公告通知等")]
 