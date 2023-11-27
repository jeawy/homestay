from django.db import models

class Tags(models.Model):
    """
    标签
    """
    # 标签名称
    name = models.CharField(max_length = 128 )
    # 标签：app程序使用
    label = models.CharField(max_length = 128 )
    class Meta:
        default_permissions = ()
        db_table = 'tags'
        constraints = [
            models.UniqueConstraint(fields = ['name', 'label'], 
            name = "tags_name_unique")
        ]