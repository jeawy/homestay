#! -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from basedatas.models import BaseDate
from appuser.models import AdaptorUser as User
from ckeditor_uploader.fields import RichTextUploadingField
from dept.models import Dept
from category.models import Category

RULE_ARGUMENT_NULL = -1 #用户没有填写对应选项
RECEIVE_LEVEL = 0 #规则是收文人员
RULE_ROLE_ID_NOT_FIND = 1
AND = 0 #与审批
OR = 1  #或审批
APPROVE_ONE = 2 #一对一审批
USER_ID = 0 #rule_type = USER_ID，说明entity_id中存的是user_id
ROLE_ID = 1 #rule_type = ROLE_ID，说明entity_id中存的是role_id
RECEIVE_RULE = 3
DELETE_RULE = -1 #删除收文规则
DRAFT = 0  #模板为草稿
NORMAL = 1 #模板正式可用
ONLY_EXIST_RECEIVE = 1 #只有收文环节，没有审批环节
class WkTemplate(BaseDate):
    """
    模板信息表
    继承自：BaseDate
    """
    # 模板名称
    name = models.CharField(max_length=300,null=False)
    # 模板类别
    # 来自Category
    type = models.ForeignKey(Category, related_name='type',on_delete=models.PROTECT,null=True)
    # 收文人员规则
    #receive_rule = models.TextField(null=True)
    #审批人员规则
    #approve_rule = models.TextField(null=True)
    #自定义属性
    extra = models.TextField(null=True)
    #模板状态
    # 0:模板为草稿
    # 1:模板可用
    status = models.SmallIntegerField(null=False)
    #创建人
    creator = models.ForeignKey(User, related_name='creator', on_delete=models.PROTECT,null = True)
    #修改人
    modifier = models.ForeignKey(User, related_name='modifier', on_delete=models.PROTECT)
    #模板属于哪个工种
    dept = models.OneToOneField(Dept, related_name='wktmp_dept', on_delete=models.CASCADE, null=True)
    class Meta:
        default_permissions = ()
        ordering = ['-date'] 
        
    def __str__(self):
        return self.name

class Rule(models.Model):
    """
    规则表
    """
    #template_id
    #规则关联的模板
    template = models.ForeignKey(WkTemplate, related_name='template_id', on_delete=models.PROTECT)
    #rule_type
    #保存0或者1
    rule_type = models.SmallIntegerField()
    #实体id
    #if (rule_type = 0): entity_id保存userid
    #if (rule_type = 1): entity_id保存roleid
    entity_id = models.IntegerField()
    #name
    #审批名称或者是收人人员名称
    name = models.CharField(max_length=200)
    #approve_type
    #0: and
    #1：or
    #2: 一对一
    approve_type = models.SmallIntegerField()
    #level
    #审批级别
    level = models.SmallIntegerField()

    def __str__(self):
        return self.name
    class Meta:
        default_permissions = () 


class WkTemplate_V2(BaseDate):
    """
    模板信息表
    继承自：BaseDate
    """
    # 模板名称
    name = models.CharField(max_length=300,null=False)
    #模板状态
    # 0:模板为草稿
    # 1:模板可用
    status = models.SmallIntegerField(null=True)
    #创建人
    creator = models.ForeignKey(User, related_name='creator_v2', on_delete=models.PROTECT,null = True)
    #修改人
    modifier = models.ForeignKey(User, related_name='modifier_v2', on_delete=models.PROTECT)
    #模板属于哪个工种
    dept = models.OneToOneField(Dept, related_name='wktmp_dept_v2', on_delete=models.CASCADE, null=True)
    #标记模板是否可用
    flag = models.BooleanField(default=False)

    class Meta:
        default_permissions = ()
        ordering = ['-date'] 

    def __str__(self):
        return self.name

class Rule_V2(models.Model):
    """
    规则表
    """
    #template_id
    #规则关联的模板
    template = models.ForeignKey(WkTemplate_V2,related_name='template_v2', on_delete=models.CASCADE)
    #审批人角色ID
    entity_id = models.IntegerField()
    #name
    #审批名称
    name = models.CharField(max_length=200,null=True)
    #level
    #审批级别
    level = models.SmallIntegerField()
    #type用于标记enty_id保存的是user还是role
    #0 role,默认保存的是role
    #1 user
    ROLE = 0
    USER = 1
    type = models.IntegerField(default=ROLE)

    # def __str__(self):
    #     return self.name
    class Meta:
        default_permissions = () 


class ExtraWorkRule(models.Model):
    # 审批人角色ID
    entity_id = models.IntegerField()
    # name
    # 审批名称
    # level
    # 审批级别
    level = models.SmallIntegerField()
    # type用于标记enty_id保存的是user还是role
    # 0 role,默认保存的是role
    # 1 user
    ROLE = 0
    USER = 1
    type = models.IntegerField(default=ROLE)

    class Meta:
        # 权限控制：添加、编辑、删除规则的权限
        default_permissions = () 