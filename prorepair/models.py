#! -*- coding: utf-8 -*-
import os
from statistics import mode
from django.db import models
from django.utils.translation import ugettext_lazy as _
from basedatas.models import BaseDate
from appuser.models import AdaptorUser as User 
from community.models import Community
from django.conf import settings


class ProRepair(BaseDate):
    """
    反馈 
        {"appid":"HBuilder","imei":" ","p":"i",
        "md":"iPhone11","app_version":"9.6.87",
        "plus_version":"1.9.9.80100",
        "os":"13.3.1","net":"3","score":4,
        "content":"1111","contact":"你手机上"} 
    """
    uuid = models.CharField(max_length=64, unique=True)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    # 反馈提交人
    user = models.ForeignKey(User, related_name='prorepair_user', on_delete=models.CASCADE )
      
    # 反馈内容
    content = models.TextField()
    # 联系方式 
    contact = models.CharField(max_length = 1024, null = True)
    
    # 评分
    score = models.SmallIntegerField(null = True) 
    #  状态
    NEW = 0 # 新建(待处理) 
    FINISHED = 1 # 已完成
    status = models.SmallIntegerField(default = NEW) 
     
    reply_user = models.ForeignKey(User,  null = True, related_name='reply_user', on_delete=models.PROTECT )
    reply_date = models.DateTimeField( null = True )
    # result 
    result = models.TextField(null = True)
     

    # 评价内容
    estimate = models.TextField(null = True)
    estimate_date = models.DateTimeField(null = True)

    # user delete it
    owner_delete = models.SmallIntegerField(default=0)

    # organize delete it
    org_delete = models.SmallIntegerField(default=0)


    class Meta:
        default_permissions = () 
        permissions = [
            ("manage_prorepair", "维修单：查看全部、编辑、删除")
        ] 
        ordering = ['-date']


class ImageQuerySet(models.QuerySet):
    def delete(self, *args, **kwargs):  
        for obj in self:
            path = os.path.join(settings.FILEPATH, obj.filepath)  
            if os.path.isfile(path):
                os.remove(path)
            obj.delete()

class RepairFdkImgs(models.Model):
    """
       图片表
    """ 
    # 用来保存任务主表或工作流主表的id
    prorepair = models.ForeignKey(ProRepair, related_name='prorepair', on_delete=models.CASCADE ) 
    # 附件名称
    filename = models.CharField(max_length=128)
    # 附件地址
    filepath = models.CharField(max_length=1024)
    REPLY = 1 # 回复时的图片
    REQUEST = 0 # 发起维修单的时候提交 的图片
    imagetype = models.PositiveSmallIntegerField(default = REQUEST)
    objects = ImageQuerySet.as_manager()

    
    class Meta:
        default_permissions = ()  






