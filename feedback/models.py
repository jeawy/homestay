#! -*- coding: utf-8 -*-
import os
import pdb
from django.db import models
from django.utils.translation import ugettext_lazy as _
from basedatas.models import BaseDate
from appuser.models import AdaptorUser as User 
from django.conf import settings



class Feedback(BaseDate):
    """
    反馈 
        {"appid":"HBuilder","imei":" ","p":"i",
        "md":"iPhone11","app_version":"9.6.87",
        "plus_version":"1.9.9.80100",
        "os":"13.3.1","net":"3","score":4,
        "content":"1111","contact":"你手机上"} 
    """
    
    # 反馈提交人
    user = models.ForeignKey(User, related_name='user', on_delete=models.CASCADE )
      
    # 反馈内容
    content = models.TextField()
    # 联系方式 
    contact = models.CharField(max_length = 1024, null = True)
    
    # 评分
    score = models.SmallIntegerField(null = True) 
    #  状态
    NEW = 0 # 新建(未处理)
    ACCEPTED = 1 # 采纳
    FINISHED = 2 # 未采纳
    status = models.SmallIntegerField(default = NEW) 
    
    device = models.CharField(max_length = 128, null = True)
    os = models.CharField(max_length = 56, null = True)
    # result 
    result = models.TextField(null = True)
    # 是否已读
    UNREAD = 0
    READ = 1
    read = models.SmallIntegerField(default=UNREAD)
    class Meta:
        default_permissions = ()
        db_table = 'feedback'


class ImageQuerySet(models.QuerySet):
    def delete(self, *args, **kwargs):  
        for obj in self:
            path = os.path.join(settings.FILEPATH, obj.filepath)  
            if os.path.isfile(path):
                os.remove(path)
            obj.delete()
             

class FdkImgs(models.Model):
    """
       图片表
    """ 
    # 用来保存任务主表或工作流主表的id
    feedback = models.ForeignKey(Feedback, related_name='feedback', on_delete=models.CASCADE ) 
    # 附件名称
    filename = models.CharField(max_length=128)
    # 附件地址
    filepath = models.CharField(max_length=1024)
    
    objects = ImageQuerySet.as_manager()

    class Meta:
        db_table = 'fdkimgs'
        default_permissions = () 






