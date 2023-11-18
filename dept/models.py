#! -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from basedatas.models import BaseDate 
from appuser.models import AdaptorUser as User
from ckeditor_uploader.fields import RichTextUploadingField
from category.models import Category
from community.models import Community


class Dept(Category):
    """部门表"""
    # 创建人
    creator = models.ForeignKey(User, null = True,  related_name='dept_creator', 
                                on_delete=models.SET_NULL)
    # 部门负责人
    charger = models.ForeignKey(User, null = True, related_name='charger', 
                                on_delete=models.SET_NULL)
    DEPT = 0 # 部门 是固定的
    TEAM = 1 # 团队 是临时的
    dept_type = models.SmallIntegerField(default = TEAM)
    # 部门员工
    users = models.ManyToManyField(User, related_name='user_depts')
    # 部门属于哪个小区的
    community = models.ForeignKey(Community, related_name="community_dept", 
                  on_delete=models.CASCADE)

    # 部门别名
    alias = models.CharField(max_length=128,  null=True)
    class Meta:
        db_table = "dept" 
        # 权限控制：添加、编辑、删除部门的权限
        default_permissions = ()
        permissions = [('can_manage_dept', '管理工种权限')]
      

class DeptKPI(BaseDate):
    """
    保存部门的总的kpi情况
    """
    # 部门
    dept = models.ForeignKey(Dept,related_name='deptkpi_dept',on_delete=models.CASCADE)
    # 完成的资产的数量
    accomplish_asset_num = models.IntegerField(default=0)
    # 完成的资产的帧数
    accomplish_asset_frame = models.IntegerField(default=0)
    # 该部门在该时间段内的实际工时
    total_actual_time = models.FloatField(default=0)
    # 该部门在该时间段内的加班工时
    total_over_time = models.FloatField(default=0)
    # 该部门的所有难度等级的平均每帧的耗时
    average_per_time = models.FloatField(default=0)
    # 记录的kpi 的年月
    record_time = models.CharField(max_length=200)
    class Meta:  
        default_permissions = ()

class DeptKPIDetail(BaseDate):
    """记录kpi的详细信息"""
    # kpi外键
    dept_kpi = models.ForeignKey(DeptKPI,related_name='deptkpi_detail',on_delete=models.CASCADE)
    # dept
    #dept = models.ForeignKey(Dept,related_name='dept_detail',on_delete=models.CASCADE)
    # 难度等级
    grade = models.SmallIntegerField()
    # 该难度等级下平均每帧耗时
    average_per_time = models.FloatField(null=True)
    # 该难度等级下的资产的数量
    accomplish_asset_num = models.IntegerField(default=0)
    # 该难度等级下的实际时间
    total_actual_time = models.FloatField(default=0)
    # 该难度等级下的加班工时
    total_over_time = models.FloatField(default=0)
    # 该难度等级下的总帧数
    accomplish_asset_frame = models.IntegerField(default=0)
    class Meta:  
        default_permissions = ()
