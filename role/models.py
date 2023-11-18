#! -*- coding: utf-8 -*-
from django.db import models
from django.db.models import constraints
from django.utils.translation import ugettext_lazy as _
from basedatas.models import BaseDate 
from appuser.models import AdaptorUser as User
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from community.models import Community


class Role(BaseDate):
    """
    角色信息表 
    # 注意：角色跟小区绑定，同一个人在不同的小区可能拥有不同的角色，所以角色是跟小区绑定的
    # 1 初始化角色：默认角色：物业、业主、租户
    内置角色全局共有
    role_json =[
        ["物业", 2,   "wuye",  0],
        ["业主", 2,  "yezhu",  0],
        ["租户", 2,  "zuhu",  0]
    ]
    """
    # 内置角色的code
    CODE_WUYE = "wuye" # 物业
    CODE_YEZHU = "yezhu" # 业主
    CODE_ZUHU = "zuhu" # 租户

    name = models.CharField(max_length=200) 
    # 角色类型
    # 1 表示角色和用户是一对一的，2表示角色和用户可以一对多
    UNIQUE = 1
    MUL = 2
    role_type = models.SmallIntegerField(default = UNIQUE)
    # 角色绑定的用户
    users = models.ManyToManyField(User, related_name='role_users')
    # 角色权限
    permissions = models.ManyToManyField(Permission, related_name='role_permissions')
    # 角色编码
    code = models.CharField(max_length=100) 
    # 角色分类
    # 0 表示内置角色，不能删除，不能修改
    # 1 表示自定义角色，支持删除和修改
    INTERNAL = 0
    DEFINE = 1
    role_sort = models.SmallIntegerField(default = DEFINE)
    
    # 除了内置角色之外，其他的角色都应该跟小区绑定
    community = models.ForeignKey(Community, null = True, on_delete=models.CASCADE)

    class Meta:
        db_table = "role_records"
        ordering = ['-date']
        default_permissions = ()
        # 角色管理的权限
        permissions = [('can_manage_role', '管理角色的权限.')]
        constraints = [
            models.UniqueConstraint(fields = ['community', 'code'],
            name="unqiue_role_community"
            )
        ]

    def __str__(self):
        return self.name

    def get_role_type_list(self):
        # 获取角色类型
        return [self.UNIQUE, self.MUL]

    def get_role_sort_list(self):
        # 获取角色分类
        return [self.INTERNAL, self.DEFINE]

class CertManager(models.Manager):
     
    def has_community_role(self, user, rolecode, community):
        # 用户在社区中是否拥有的rolecode的角色  
        rolecount = self.filter(user = user,
                community=community, 
                role__code = rolecode).count()
        
        return rolecount

class Cert(models.Model):
    """
    身份认证表
    # 一个小区一个用户可能有多个角色：如业主、业主委员会主任等。
    """
    uuid = models.CharField(max_length=64, unique=True)
    # 所在小区
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    # 对应的角色
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    # 用户
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    objects = CertManager()
      
    class Meta:
        default_permissions = ()
        permissions = (("manage_cert", "管理认证权限"),)
        constraints = [
            models.UniqueConstraint(
                fields=['community','user', 'role'],
                name="community_role_unique"
            )
         ]
        