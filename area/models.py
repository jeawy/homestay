from django.db import models

class Area(models.Model):
    """地点表"""

    ID = models.IntegerField(primary_key=True)
    # pid进行自关联
    PARENT_ID = models.ForeignKey("Area", on_delete=models.CASCADE, db_column='PARENT_ID')
    # 地点名称
    NAME = models.CharField(max_length=256)
    # 地点简称
    SHORT_NAME = models.CharField(max_length=256, null=True)
    # 经度
    LONGITUDE = models.DecimalField(max_digits=10, decimal_places=6, null=True)
    # 维度
    LATITUDE = models.DecimalField(max_digits=10, decimal_places=6, null=True)
    # 省市级别
    LEVEL = models.SmallIntegerField(null=True)
    # 地区排序
    SORT = models.SmallIntegerField(null=True)
    # 状态，用不到
    STATUS = models.SmallIntegerField(default=1, null=True)

    class Meta:
        default_permissions = ()
        managed = False
        db_table = "area"