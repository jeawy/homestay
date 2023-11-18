from django.db import models

class Tags(models.Model):
    """
    标签
    """
    # 标签名称
    name = models.CharField(max_length = 128, unique=True)
    # 标签：程序使用
    label = models.CharField(max_length = 128, unique=True)
    class Meta:
        default_permissions = ()
        db_table = 'tags'