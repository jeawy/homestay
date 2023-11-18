from appuser.models import AdaptorUser as User
from django.db import models
from basedatas.models import BaseDate
from property.entity import EntityType  
  

class Like(BaseDate):
    """
    点赞表
    """
    # 点赞人
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # 用来保存备注或者评论的实体表的id
    entity_uuid = models.CharField(max_length=64)
    # 实体类别
    # 任务实体 TASK,模板实体 WK_TEMPLATE,流程实体 RECORD
    # 项目实体 PROJECT，资产类别 ASSET,工种 WORKTYPE
    entity_type = models.SmallIntegerField()
    # 为了方便消息跳转，添加的url
    url = models.CharField(max_length=128) 
    
    @property
    def entitytype_list(self):
        return [EntityType.PRODUCT]
    
    class Meta:
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(fields=['user', 'entity_uuid', 'entity_type'],
                                    name='unique_like')
        ]


class Readcount(models.Model):
    """
    阅读数表
    """
    # 阅读数
    number = models.PositiveIntegerField(default=1)
    
    # 用来保存备注或者评论的实体表的id
    entity_uuid = models.CharField(max_length=64) 
    entity_type = models.SmallIntegerField()
    
    @property
    def entitytype_list(self):
        return [EntityType.TASK, EntityType.WK_TEMPLATE, EntityType.RECORD,
                EntityType.PROJECT,EntityType.ASSET,EntityType.WORKTYPE]
    
    class Meta:
        default_permissions = ()
        constraints = [
            models.UniqueConstraint(fields=[ 'entity_uuid', 'entity_type'],
                                    name='unique_read_count')
        ]
