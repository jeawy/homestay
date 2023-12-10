from statistics import mode
from appuser.models import AdaptorUser as User
from django.db import models
from basedatas.models import BaseDate
from property.entity import EntityType, AttrsTypes
from django.conf import settings
import os


class Comment(models.Model):
    """
    评论/备注信息表
    """
    uuid = models.CharField(  max_length=64, unique=True)
    date = models.DateTimeField()
    # 评论人
    user = models.ForeignKey(User, related_name='comment_creator',
                                on_delete=models.PROTECT)
    # 内容
    content = models.TextField(blank=True)
    # 用来保存备注或者评论的实体表的id
    entity_uuid =  models.CharField(max_length=64)
    entity_type = models.SmallIntegerField()
    
    # 评价来源，0 表示虚拟评价
    comeway =  models.SmallIntegerField(default=1)
    # 评分
    rate = models.SmallIntegerField(default=5)
    # pid进行自关联,可以为空
    pid = models.ForeignKey("comment", null=True, on_delete=models.CASCADE)
   
    # 为了方便消息跳转，添加的url
    url = models.CharField(max_length=128) 
    @property
    def entitytype_list(self):
        return [EntityType.TASK, EntityType.WK_TEMPLATE, EntityType.RECORD,
                EntityType.PROJECT,EntityType.ASSET,EntityType.WORKTYPE]
    
    class Meta:
        ordering = ['-date']
        default_permissions = ()


class ImageQuerySet(models.QuerySet):
    def delete(self, *args, **kwargs):  
        for obj in self:
            path = os.path.join(settings.FILEPATH, obj.filepath)  
            if os.path.isfile(path):
                os.remove(path)
            obj.delete()


class CommentImgs(models.Model):
    """
    图片表
    """ 
    # 用来保存任务主表或工作流主表的id
    comment = models.ForeignKey(Comment, related_name='commentimages', on_delete=models.CASCADE ) 
    # 附件名称
    filename = models.CharField(max_length=128)
    # 附件地址
    filepath = models.CharField(max_length=1024)

    objects = ImageQuerySet.as_manager()
 
    class Meta: 
        default_permissions = () 
