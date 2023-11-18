from django.db import models
from appuser.models import AdaptorUser as User


class Menu(models.Model):
    """
    菜单配置表
    """
    PROJECT_TASK_LIST_MENU = 0 # 项目中任务列表菜单配置
    PROJECT_ASSET_LIST_MENU = 1 # 项目中资产列表菜单配置
    PROJECT_SHOT_LIST_MENU = 2 # 项目中镜头列表菜单配置
    menu_type = models.PositiveSmallIntegerField(default = PROJECT_TASK_LIST_MENU)
    # 菜单项，每个菜单以英文逗号隔开
    menu_list = models.CharField(max_length = 1024)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        default_permissions = ()
        db_table = 'menu'
        constraints = [
            models.UniqueConstraint(fields=['user','menu_type'],
            name='unique_menu_type')
        ]
