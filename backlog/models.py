#! -*- coding: utf-8 -*-
from django.db import models

from basedatas.models import BaseDate
from appuser.models import AdaptorUser as User 


class Backlog(BaseDate):
    """
    待办事项表
    待办事项仅自己可见
    """
    uuid = models.CharField(max_length= 64, unique=True) # UUID
    # 创建人
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # 图片
    picture = models.CharField(max_length=200,null=True)
    # 内容描述
    content = models.TextField(null=True)
    
    # 详细内容
    detail = models.TextField(null=True) 
    # 标题
    title = models.CharField(max_length=200,null=False)
      
    WAIT = 0  # 未完成
    PUBLISHED = 1 # 已完成
     
    status = models.PositiveSmallIntegerField(default = WAIT)  

    class Meta:
        default_permissions = ()
        ordering = [  'status', '-date']
        
 