from statistics import mode
from django.db import models
from gift.models import Gift, Specifications
from appuser.models import AdaptorUser as User


class Cart(models.Model):
    # 购物车 
    uuid = models.CharField(max_length= 64, unique=True) # UUID
    user = models.ForeignKey(User, on_delete=models.CASCADE )
    # 规格
    spec = models.ForeignKey(Specifications, on_delete=models.CASCADE)
    # 数量
    number = models.SmallIntegerField(default=1)

    class Meta:
        default_permissions = () 
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'spec'],
                name='unique_cart'
            )
        ]
