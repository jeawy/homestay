from django.db import models


class Attachment(models.Model):
    """
       附件表
    """

    # 用来保存任务主表或工作流主表的id
    app_id = models.IntegerField()
    # type 1表示任务附件，2表示工作流附件
    # 1 任务附件
    TASKATTACH = 1
    # 2 工作流附件
    FLOWATTACH = 2
    # 3 评论附件
    COMMENTATTACH = 3
    # 4 临时附件：会定期删除，或者删除也没有影响的附件信息，删除时，同时删除文件
    TEMP = 4
    apptype = models.SmallIntegerField()
    # 添加日期
    date = models.DateTimeField(auto_now_add=True)

    # 附件名称
    filename = models.CharField(max_length=128)
    # 附件地址
    filepath = models.CharField(max_length=1024)
    
    @property
    def filetype_list(self):
        """
        获取文件类型列表
        """
        return [self.TASKATTACH, self.FLOWATTACH, self.COMMENTATTACH, self.TEMP]

    class Meta:
        default_permissions = ()