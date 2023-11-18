from django.db import models

# Create your models here.
from appuser.models import AdaptorUser as User
from django.db import models
from basedatas.models import BaseDate
from property.entity import EntityType, AttrsTypes


class opRecords(BaseDate):
    """
    操作记录表
    """
    # 创建人
    creator = models.ForeignKey(User, related_name='oprecords_creator',
                                on_delete=models.PROTECT)
    # 内容
    content = models.TextField(blank=True)
    # 记录操作的实体表的id
    entity_id = models.IntegerField()
    # 实体类别
    # 任务实体 TASK,模板实体 WK_TEMPLATE,流程实体 RECORD
    # 项目实体 PROJECT，资产类别 ASSET,工种 WORKTYPE
    entity_type = models.SmallIntegerField()
    # 保存url路径
    url = models.CharField(max_length=1024)

    @property
    def entitytype_list(self):
        return [EntityType.TASK, EntityType.WK_TEMPLATE, EntityType.RECORD,
                EntityType.PROJECT,EntityType.ASSET,EntityType.WORKTYPE]

    class Meta:
        default_permissions = ()

