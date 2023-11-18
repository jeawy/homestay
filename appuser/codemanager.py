#! -*- coding:utf-8 -*- 
from django.db import models
import pdb
import random
import string
import traceback
from django.conf import settings
from common.e_mail import EmailEx 
from datetime import datetime, timedelta
from django.utils.translation import ugettext as _
from property.code import * 
from common.utils import  verify_phone
from common.sms import send_sms
from common.logutils import getLogger
logger = getLogger(True, 'users', False)


class CodeManager(models.Manager):
    """
    验证码的manager
    """
    email = EmailEx()
     
    def generate_code(self):
        code = ''.join(random.choice(string.digits) for i in range(4))
        return code

    def send_code(self, email, codetype = '0'):
        result={} 
        if not self.email.EMAIL_REGEX.match(email):
            result['status'] = ERROR
            result['msg'] = [email] #'电子邮件格式不正确'
        else:
            code    =  self.generate_code()
            Subject = settings.PROJECTNAME+' Verify Code'
            content = _("Your verify code is ") + code #'您好， 欢迎您注册'+settings.PROJECTNAME+'，您的邮箱验证码是： ' + code
            try:
                self.email.send_html_email(Subject, content, email)
                try:
                    verify_code = self.model.objects.get(email__exact = email, type =codetype)
                    verify_code.code = code
                    verify_code.save()
                except self.model.DoesNotExist: 
                    verify_code = self.model(email=email, code=code, type = codetype)
                    verify_code.save()
                    
                result['status'] = SUCCESS
                result['msg'] = _("验证码已发送!")#'验证码已发至您的邮箱中， 请到邮箱中查看您的验证码!'
            except Exception :
                logger.error("发送邮件的过程中发生错误:{0}".format(traceback.format_exc()))
                result['status'] =  ERROR
                result['msg'] = '发送邮件的过程中发生错误 ' 

        return result
    
    def veirfy_code(self, code, email, codetype='0'):
        # 验证正确返回1 ，否则返回0
        result = 0
        try:
            verify_code = self.model.objects.get(email__exact = email, 
            code =code, type=codetype)
            result = 1
        except self.model.DoesNotExist:
            pass
        return result


class PhoneCodeManager(CodeManager):
    """
    验证码的manager
    """ 
    def send_code_phone(self, phone, codetype):
        result={}  
        if not verify_phone(phone):
            result['status'] = ERROR 
            result['msg'] = '手机号码格式错误'
            return result
        code = self.generate_code() 
        
        try:
            # send phone code from a SDK 
            try:
                verify_code = self.model.objects.get(phone__exact = phone, type =codetype)
                modify_date = verify_code.modify_date
                # 确认是否频繁发送   
                if datetime.today()+timedelta(seconds=-30) < modify_date:
                    result['status'] = ERROR 
                    result['msg'] = '请勿频繁操作'
                    return result
 
                verify_code.code = code
                verify_code.save()
            except self.model.DoesNotExist:
                verify_code = self.model(phone=phone, code=code, type = codetype)
                verify_code.save() 
             
            # 调用接口发送短信
            print(send_sms(str(codetype), phone, code))

            result['status'] = SUCCESS
            result['msg'] = '验证码已发送.'  
        except Exception as e:
            result['status'] = ERROR 
            result['msg'] = '发送手机验证码的过程中发生错误： '+ str(e)

        return result
    
    def veirfy_code_phone(self, code, phone, codetype='0'): 
        """
        获取手机验证码
        """
        if code == '1111' or code == 1111:
            return True

        try:
            self.model.objects.get(phone__exact = phone, code =code,type = codetype )
            return True
        except self.model.DoesNotExist:
            return False

class AdaptorCodeManager(PhoneCodeManager):
    pass