#! -*- coding: utf-8 -*-
from statistics import mode
from django.db import models 
from basedatas.models import BaseDate
from appuser.models import AdaptorUser as User  


class Notice(BaseDate):
    """
    通知
    用户只能删除单独发给自己的通知消息，
    如果是发给集体的则不能主动删除，
    系统会在3个月后自动删除这类通知消息（如公告消息)
    """
    # 接收人（业主）
    receiver = models.ForeignKey(User, related_name='receiver', on_delete=models.CASCADE, null = True)
     
    # 通知标题
    title = models.CharField(  max_length=2048)
    # 通知内容 
    content = models.TextField()
    # 紧急程度
    AVERAGE = 0 # 一般
    URGENT = 1 # 紧急
    SUPOR_URGENT = 2 # 特急
    urgency_level = models.SmallIntegerField(default = AVERAGE)
    # 通知属于的业务类型
    ANNOUCEMENT = 1
    REPAIR = 2 # 维修单   
    entity_type = models.SmallIntegerField(null = True)
    # 业务uuid， 方便将来对应的删除通知uuid
    entity_uuid = models.CharField(null = True, max_length=64)
     
    # 1表示发给平台的通知，
    platform = models.PositiveSmallIntegerField(default= 0)
    # 是否已读，默认0，表示未读
    # 1 表示已读
    READ = 1
    UNREAD = 0
    read = models.SmallIntegerField(default = UNREAD)
    # 移动端的跳转链接
    appurl = models.CharField(null = True, max_length=256)
    # PC端的跳转链接
    pcurl = models.CharField(null = True, max_length=256)
    #  APP端还是PC端接收, ALL代表PC和移动端都可以接收
    PC = 1
    APP = 0 
    ALL = 2
    notice_type = models.PositiveSmallIntegerField(default = ALL)
 
    class Meta:
        default_permissions = ()
        db_table = 'notice'
        ordering = ['read', '-date']

    def __str__(self):
        return self.title

    def level_list(self):
        return [self.AVERAGE, self.URGENT, self.SUPOR_URGENT]

    def read_list(self):
        return [self.READ, self.UNREAD]



