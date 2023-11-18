#! -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from basedatas.models import BaseDate
from appuser.models import AdaptorUser as User
from ckeditor_uploader.fields import RichTextUploadingField
from category.models import Category
from wktemplate.models import WkTemplate

class WkRecords(BaseDate):
    """流程信息表"""

    # 外键，来自用户表的ID，表示谁创建的流程
    user = models.ForeignKey(User, related_name='wk_creator', on_delete=models.PROTECT)
    # 流程类别
    category = models.ForeignKey(Category, related_name='wk_category', null=True, on_delete=models.SET_NULL)
    #流程名
    name = models.CharField(max_length=200)
    #详细内容
    context = models.TextField(blank=True)
    #审批状态
    #0：待批（提交），1：审批中，2：通过，3：拒绝，-1：草稿，-2：用户撤回。默认为0
    SUBMITTED = 0 #已提交
    APPROVE = 1 #正在审批
    PASS = 2 #通过
    REFUSE =3 #拒绝
    DRAFT = -1 #草稿
    RECALL = -2 #撤回
    status = models.SmallIntegerField(default=SUBMITTED)
    #审批完成时间，流程审批完成以后添加
    over_time=models.DateTimeField(null=True)
    #扩展属性,可为空
    extra = models.TextField(blank=True)
    #模板ID，表示属于模板创建，外键
    template = models.ForeignKey(WkTemplate, related_name='modelclass', blank=True, null=True, on_delete=models.SET_NULL)

    class Meta: 
        default_permissions = ()
        db_table = "wk_message_records"
        ordering = ['-date']

    def __str__(self):
        return self.name


class Approve(models.Model):
    """流程审批表"""

    #外键，流程ID，来自流程信息表
    flow = models.ForeignKey(WkRecords, related_name='flow_id', on_delete=models.CASCADE)
    #外键，审批人员ID，来自用户表
    approver = models.ForeignKey(User, related_name='approve_uer', on_delete=models.PROTECT)
    # 审批级别，0：为收文人员，其他数字为第几级审批,默认为0
    level = models.SmallIntegerField(default=0)
    #审批状态，0：待批，1：通过，2：拒绝，3：转批，-1：未到当前审批，-2：草稿或用户撤回。默认为0
    SUBMITTED = 0 #待批
    PASS = 1 #通过
    REFUSE =2 #拒绝
    OTHER =3 #转批
    WAIT = -1 #未到当前审批
    DRAFT = -2 #草稿或用户撤回
    OTHER_PASS = -3 #他人进行审批通过
    status = models.SmallIntegerField(default=SUBMITTED)
    #外键，转批人员，来自用户表
    touser = models.ForeignKey(User, related_name='touser_user', blank=True, null=True, on_delete=models.PROTECT)
    #审批时间
    time = models.DateTimeField(null=True)
    #审批意见
    opinion = models.TextField(blank=True)
    #审批顺序，0,1
    AND = 0 #同级都通过进入下一级审批
    OR = 1 #同级有人通过进入下一级审批
    and_or = models.SmallIntegerField(default=AND)

    class Meta:
        default_permissions = ()
        db_table = "wk_approve_records"


class Associate(models.Model):
    """关联表，记录的是关联的流程和被关联的流程"""

    #关联的流程ID
    associate = models.ForeignKey(WkRecords, related_name='associate_id', on_delete=models.CASCADE)
    #被关联的流程ID
    be_associate = models.ForeignKey(WkRecords, related_name='be_associate_id', on_delete=models.CASCADE)
    class Meta:
        default_permissions = ()
