import smtplib
import os
from email import encoders
from email import utils
from email.message import Message
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText
from property import settings
import pdb
import re
import threading
import traceback
from common.logutils import getLogger

logger = getLogger(True, 'thread_email', False)

class Email(object):
    EMAIL_REGEX = re.compile(r'[^@]+@[^@]+\.[^@]+')



        
class EmailEx(Email):
    def read_html(self):
        """
        read html content
        """
        htmlpath = os.path.join(settings.BASE_DIR, 'common', 'email.html')
        with open(htmlpath, 'r',encoding='utf-8') as f:
            return f.read()

        return ""

    def send_text_email(self,Subject,content,receiver):
        
        if settings.EMAIL_SWITCH:
            sender              = settings.SMTP_SERVER_USER
            themsg              = MIMEMultipart()
            themsg['Subject']   = Subject

            if isinstance(receiver, list):
                themsg['To'] = ', '.join(receiver)
            else:
                themsg['To'] = receiver
            #themsg['To']        = receiver
            themsg['From']      = settings.PROJECTNAME + "<" + sender + ">"
            themsg['Date']      = utils.formatdate(localtime = 1)
            themsg['Message-ID'] = utils.make_msgid()
            msgAlternative      = MIMEMultipart('alternative')
            themsg.attach(msgAlternative)
            content = content + '<br/>www.map2family.com'
            msgText = MIMEText(content,'html', 'utf-8')
            msgAlternative.attach(msgText)
            themsgtest = themsg.as_string()      
            # send the message
            server = smtplib.SMTP()
            server.connect(settings.SMTP_SERVER)
            server.login(settings.SMTP_SERVER_USER, settings.SMTP_SERVER_PWD)
            server.sendmail(sender, receiver, themsgtest)
            
            server.quit()#SMTP.quit()
   

    def send_html_email(self,  Subject,content,receiver):
        if settings.EMAIL_SWITCH:
            sender              = settings.SMTP_SERVER_USER
            themsg              = MIMEMultipart()
            themsg['Subject']   = Subject
            if isinstance(receiver, list):
                themsg['To']        = ', '.join(receiver)
            else:
                themsg['To']        = receiver
            themsg['From']      = settings.PROJECTNAME + "<" + sender + ">"
            themsg['Date']      = utils.formatdate(localtime = 1)
            themsg['Message-ID'] = utils.make_msgid()
            msgAlternative      = MIMEMultipart('alternative')
            themsg.attach(msgAlternative)
            html_content = self.read_html()
            if html_content:
                html_content = html_content.replace("XXXXXX", Subject)
                content = html_content.replace("######", content)

            msgText = MIMEText(content,'html', 'utf-8')
            msgAlternative.attach(msgText)
            themsgtest = themsg.as_string()     
            # send the message
            server = smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT)
            server.login(settings.SMTP_SERVER_USER, settings.SMTP_SERVER_PWD)
            server.sendmail(sender, receiver, themsgtest)
            server.quit()#SMTP.quit()

    def send_sync(self, subject, content, receiver):
        """
        异步发送
        :param subject:  title
        :param content:
        :param receiver:
        :return:
        """
        #self.send_text_email(subject, content, receiver)
        #self.send_html_email(subject, content, receiver)
        #threading.Thread(target=self.send_text_email, args=(subject, content, receiver)).start()
        threading.Thread(target=self.send_html_email, args=(subject, content, receiver)).start()
        logger.error(traceback.format_exc())
