from django.db import models
from community.models import Community
from appuser.models import AdaptorUser as User


class DynamicFee(models.Model):
    """
    动态收费项，如：停车费，不是每一户都必须的收费项
    """
    uuid = models.CharField(max_length=64, unique=True)  # UUID
    community = models.ForeignKey(Community,
                                  related_name="community_dynamic_fee",
                                  on_delete=models.CASCADE)
    # 收费项名称：如地面停车费
    name = models.CharField(max_length=20)

    # 收费金额
    money = models.FloatField()
    # 收费方式
    TYPE_NEED_AREA = 0  # 每月/每平米
    TYPE_NO_NEED_AREA = 1  # 每月/每户
    feetype = models.PositiveSmallIntegerField(default=TYPE_NO_NEED_AREA)

    date = models.DateTimeField(auto_now=True)

    class Meta:
        default_permissions = ()
        constraints = [
            models.UniqueConstraint (fields=["name", "community"],
            name = "unique_dynamic_fee_name")
        ]


class FixedFee(models.Model):
    """
    固定收费， 每一户都必须的收费项
    如：一费制
    """
    uuid = models.CharField(max_length=64, unique=True)  # UUID
    community = models.ForeignKey(Community,
                                  related_name="community_fixed_fee",
                                  on_delete=models.CASCADE)
    # 收费名称：如一费制
    name = models.CharField(max_length=20)

    date = models.DateTimeField(auto_now=True)

    class Meta:
        default_permissions = ()
        permissions = [("manage_fee", "创建、编辑、删除收费项权限"),
                       ("asign_fee", "为业主绑定收费项的权限")]
        constraints = [
            models.UniqueConstraint (fields=["name", "community"],
            name = "unique_fixed_fee_name")
        ]


class FixedItemFee(models.Model):
    """
    固定收费中的收费项， 每一户都必须的收费项
    """
    uuid = models.CharField(max_length=64, unique=True)  # UUID
    fixedfee = models.ForeignKey(FixedFee,
                                 related_name="fixed_fee_item",
                                 on_delete=models.CASCADE)
    # 收费项名称：如物业费、垃圾费
    name = models.CharField(max_length=20)

    # 收费金额
    money = models.FloatField()
    # 收费方式
    TYPE_NEED_AREA = 0  # 每月/每平米
    TYPE_NO_NEED_AREA = 1  # 每月/每户
    feetype = models.PositiveSmallIntegerField(default=TYPE_NO_NEED_AREA)

    class Meta:
        default_permissions = ()
         