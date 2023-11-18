#! -*- coding: utf-8 -*-
from django.db import models
from django.contrib import auth
import pdb
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser,PermissionsMixin
) 
from django.utils.translation import ugettext_lazy as _
from basedatas.models import BaseDate
from appuser.usermanager import AdaptorUserManager
from appuser.codemanager import AdaptorCodeManager 
 

class BaseUser(BaseDate, AbstractBaseUser, PermissionsMixin):
    """
    model for User, using the column 'email' for primary key and login to our web site.
    """
    username  = models.CharField( _('username') ,max_length=50, null=True)
    email   = models.EmailField(
        verbose_name = _('email'),
        max_length = 255,
        unique=True,
        null = True
    )
	# 业主身份是否经过认证，默认为False代表未认证 
    is_verified = models.BooleanField( _('is active'), default=False) # 
    
    is_active   = models.BooleanField( _('is active'), default=True) # 

    is_admin    = models.BooleanField( _('is admin'), default=False) # u'是否为管理员'
      
    #identify is user saved the portraint they uploaded
    #True: they saved
    #False: by default, they didn't save
    is_head_portrait     = models.BooleanField(u'是否保存了上传后的头像',default=False)
    #the filename of portrait is something like: userid_*****.***, the prefix is userid, and then with 5 random chars.
    #ex:1_sdfs2.jpg 
    head_portrait   	 = models.ImageField(u'选择头像',  upload_to='portrait',null = True)	
    
	#definitions for social users
    email_verified       = models.BooleanField(u'是否保存了邮箱',default=False)
    #0 for not social user, 1 for user, 2 for both user
    social_user_status   = models.IntegerField(u'第三方用户状态',default=0)
    social_site_name     = models.IntegerField( u'第三方名称',default=0)#1 for qq          
    social_user_id       = models.CharField( u'第三方用户ID',max_length=255,default=u'未填写')
    is_staff = models.BooleanField(_('staff status'), default=True)
    
	#this is the thumbnail of user protrait
    #the filename of thumbnail portrait is something like: userid_thumbnl_*****.***, the prefix is userid, and then with 5 random chars.
    #these five random chars are the same with the portrait.
    #ex:1_thumbnl_sdfs2.jpg 
    thumbnail_portait = models.CharField(max_length=1024, null=True)
    #If there is message for this user, this column will be marked as TRUE; else will be marked as FALSE
    msg_mark             = models.BooleanField(_('new message'), default=False)
 
    phone = models.CharField( _('phone'),max_length=128, unique = True)
 
    USERNAME_FIELD       = 'phone'
    REQUIRED_FIELDS      = []

    def get_name(self):
        # The user is identified by their email address
        return self.username

    def __str__(self):              # __unicode__ on Python 2
        return self.username
  
    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        #return True
        """
        Returns True if the user has the specified permission. This method
        queries all available auth backends, but returns immediately if any
        backend returns True. Thus, a user who has permission from a single
        auth backend is assumed to have permission in general. If an object is
        provided, permissions for this specific object are checked.
        """
        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        # Otherwise we need to check the backends.
        return _user_has_perm(self, perm, obj)
    
    
    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True
    def get_short_name(self):
        # The user is identified by their email address
        return self.username

    def get_full_name(self):
        # The user is identified by their email address
        return self.username
    
    class Meta:
        default_permissions = ()
        permissions = (
            ("admin_management", "系统管理员"), 
            ("super_user", "超级管理员权限."),
        )
    
   

class CenterUser(BaseUser): 
    class Meta:
        abstract = True

class AdaptorUser(CenterUser):
    objects  = AdaptorUserManager() 
       
    # 是谁认证的该业主
    verified_user = models.ForeignKey("AdaptorUser", on_delete=models.SET_NULL, null = True) 
    sex = models.CharField( u'性别', max_length=10, default=u'男')
    uuid = models.CharField(  max_length=64, unique=True)
    # 微信小程序用户唯一id，小程序支付需要用到
    openid = models.CharField(  max_length=64, null = True)

    # 设备id
    cid = models.CharField(  max_length=64, null = True)
    
    # 提现用的支付宝账号
    alipay_account = models.CharField(max_length=128, null = True)
    
    # 减余额的过程中锁定用户
    # 0 表示未锁定，1表示已锁定，已锁定情况下不能减购物卡余额
    islooked = models.PositiveSmallIntegerField(default=0)
     
     
    def get_userrole(self):
        # 获取用户类型列表：
        return [1, 0]
  
    def has_role_perm(self, perms):
        roles = self.role_users.all()
        result = False

        if self.is_superuser: # 超级管理员拥有所有权限
            return True
        
        perms_list = perms.split(".") 
        for role in  roles: 
            result = role.permissions.filter(
                 content_type__app_label = perms_list[0],  
                  content_type__model = perms_list[1],  
                   codename =perms_list[2]).exists()
            if result:
                return result
        return result 
    
    def has_community_perm(self, perms, communityinstance):
        # 用户(物业)在社区中的权限
        if (communityinstance.IT_MANAGER == self):
            #  IT 管理者在本小区拥有全部权限 
            return True
        if self.is_superuser: # 超级管理员拥有所有权限
                return True

        try:    
            role = self.community_users.get(community=communityinstance)
            result = False
 
            perms_list = perms.split(".") 
            
            result = role.permissions.filter(
                    content_type__app_label = perms_list[0],  
                    content_type__model = perms_list[1],  
                    codename =perms_list[2]).exists()
           
            return result 
        except  :
            return False
     

    class Meta:
        default_permissions = ()
        db_table = 'user'
        ordering = ['-date', 'username']


def _user_has_perm(user, perm, obj):
    """
    A backend can raise `PermissionDenied` to short-circuit permission checking.
    """
    for backend in auth.get_backends():
        if not hasattr(backend, 'has_perm'):
            continue
        try:
            if backend.has_perm(user, perm, obj):
                return True
        except PermissionDenied:
            return False
    return False

 
class VerifyCode(BaseDate):
    """
    the random code used to verify the email validation  
    """
    email = models.EmailField(
        max_length=255, null = True
    )
    phone = models.CharField( _('Phone'), max_length=20, default=u'')
    #the random code
    code = models.CharField( _('code'), max_length=50, default=u'')
    #type = 0, the code used for register
    #type = 1, the code used to find password
    #type = 2, phone code
    type = models.CharField( _('type'), max_length=5, default='0')

    objects = AdaptorCodeManager()
    class Meta:
        default_permissions = ()


class InvalidUsername(models.Model):
    """
    不可用的用户名
    """
    username = models.CharField(max_length = 256)
    # 为什么不可用
    # 默认是已注册
    invalid_type = models.CharField(default = '0', max_length = 10)

    class Meta:
        default_permissions = ()
        db_table = 'invalidusername'
        