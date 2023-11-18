from appuser.models import AdaptorUser as User
from django.db import models
from basedatas.models import BaseDate
from property.entity import EntityType, AttrsTypes


class AttrsCreate(BaseDate):
    """
    属性创建表
    """
    # 属性名称
    name = models.CharField(max_length=128)
    # 属性类型
    # 数字 NUMBER,字符 CHARACTER,日期 DATE,布尔 BOOLEAN,枚举 ENUMERATE
    # type 属性类型判断
    # 1 代表 数字
    # 2 代表 字符 长度不超过1024
    # 3 代表 日期
    # 4 代表 布尔
    # 5 代表 枚举
    type = models.SmallIntegerField()

    # 创建人
    creator = models.ForeignKey(User, related_name='attrs_creator',
                                on_delete=models.PROTECT)
    # 属性默认值
    default = models.CharField(max_length=128)
    # 属性值
    value = models.TextField(blank=True)

    @property
    def attrstype_list(self):
        return [AttrsTypes.NUMBER, AttrsTypes.CHARACTER, AttrsTypes.DATE,
                AttrsTypes.BOOLEAN, AttrsTypes.ENUMERATE]
    
    class Meta:
        # 管理的权限 
        default_permissions = ()
        permissions = [('can_manage_attr', '自定义属性管理权限')]
        

class AttrsInstances(models.Model):
    """
    属性实体表
    """
    # 用来保存添加新属性的实体表的id
    entity_id = models.IntegerField()
    # 实体类别
    # 任务实体 TASK,模板实体 WK_TEMPLATE,流程实体 RECORD
    # 项目实体 PROJECT，资产类别 ASSET,工种 WORKTYPE
    entity_type = models.SmallIntegerField()
    attr_name = models.CharField(max_length=128)
    attr_value = models.TextField(blank=True)
    # 属性类型
    # 数字 NUMBER,字符 CHARACTER,日期 DATE,布尔 BOOLEAN,枚举 ENUMERATE
    attr_type = models.SmallIntegerField()

    @property
    def attrstype_list(self):
        return [AttrsTypes.NUMBER, AttrsTypes.CHARACTER, AttrsTypes.DATE,
                AttrsTypes.BOOLEAN, AttrsTypes.ENUMERATE]

    @property
    def entitytype_list(self):
        return [EntityType.TASK, EntityType.WK_TEMPLATE, EntityType.RECORD,
                EntityType.PROJECT, EntityType.ASSET, EntityType.WORKTYPE]

    class Meta:
        default_permissions = ()

class AttrsBind(models.Model):
    """
    属性绑定表
    """
    attr = models.ForeignKey(AttrsCreate, related_name='attrs_bind',
                             on_delete=models.CASCADE)
    # 实体类别
    # 任务实体 TASK,模板实体 WK_TEMPLATE,流程实体 RECORD
    # 项目实体 PROJECT，资产类别 ASSET,工种 WORKTYPE
    entity_type = models.SmallIntegerField()

    # 用来保存添加新属性的实体表的id
    entity_id = models.IntegerField(null=True)

    @property
    def bindentity_list(self):
        return [EntityType.TASK, EntityType.WK_TEMPLATE, EntityType.RECORD,
                EntityType.PROJECT, EntityType.ASSET, EntityType.WORKTYPE]

    class Meta:
        # 管理的权限
        default_permissions = ()
        permissions = [('can_manage_attrsbind', '属性绑定权限')]