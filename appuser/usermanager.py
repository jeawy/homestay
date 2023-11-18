from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser,PermissionsMixin
)
import pdb 

class UserManager(BaseUserManager):
    def create_user(self, phone, useruuid, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
         
        user = self.model(
            phone=phone,
            uuid = useruuid
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email,  password, name):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(email,
            password=password,
            username = name
        )
        user.is_admin = True
        user.save(using=self._db)
        return user
    
    def uniqueUsername(self, username):
        """
        check if the username is unique
        if unique, return True
        else return False
        """
        try: 
            self.get(username=username)
            return False
        except self.model.DoesNotExist:
            return True
        except self.model.MultipleObjectsReturned:
            return False
    

    
    def uniqueEmail(self, email):
        """
        check if the email is unique
        if unique, return True
        else return False
        """
        try: 
            self.get(email=email)
            return False
        except self.model.DoesNotExist:
            return True
        except self.model.MultipleObjectsReturned:
            return False

class AdaptorUserManager(UserManager):
    def getsuperuser_emails(self ):
        """
        get super users email list
        """
        users = self.filter(is_superuser = 1)
        return [user.email for user in users]
    
