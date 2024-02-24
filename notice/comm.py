# ！ -*- coding:utf-8 -*-
import os
import pdb
from notice.models import Notice
from common.e_mail import EmailEx
from common.logutils import getLogger
from appuser.models import AdaptorUser as User
 
logger = getLogger(True, 'notice', False)


def get_unread_notice_count(user):
    #  返回某个用户的未读消息数
    return Notice.objects.filter(receiver = user, read = Notice.UNREAD).count()

class NoticeMgr(object):
    """
    通知模块函数接口
    """
    # 紧急程度
    AVERAGE = 0
    URGENT = 1
    SUPOR_URGENT = 2

    @classmethod
    def create_by_ids(cls, user_ids,  title, level, content, url=None, entity_type=None,
                      entity_uuid=None, Email=True, SMS=False):
        """
        添加通知
        :param user_ids: 接收用户id列表:[1,2,3]
        :param title: 通知标题
        :param level: 紧急程度等级：0 （默认）一般；1 紧急；2 非常紧急 
        :param content: 内容
        :param url: 跳转链接,用户点击通知链接后跳转的页面，页面地址可以和前端要
        :param entity_type: 实体类型
        :param entity_uuid: 实体uuid 
        :param Email: 本次通知是否发送email邮件，当全局邮件开关关闭时，该参数不生效。
                    全局邮件发送开关：settings.py的EMAIL_SWITCH，只有该值设置为True时，
                    create函数的email才生效。
        :param SMS: 是否发送短信提醒
        :return:空 
        """
        # logger.info("user_ids:{0},title:{1},content:{2},url:{3}".format(user_ids,title,content,url))
        users = User.objects.filter(id__in=user_ids)
        for user in users:
            cls.create(title=title, level=level, content=content, user=user, url=url, entity_type=entity_type,
                       entity_uuid=entity_uuid, Email=Email, SMS=SMS)

    @classmethod
    def create(cls, title,content,  level=AVERAGE, user=None,    
               appurl=None, pcurl=None, entity_type=None,
               entity_uuid=None,  platform=None, Email=True  ):
        """
        添加通知
        :param user: 接收用户
        :param title: 通知标题
        :param level: 紧急程度等级：0 （默认）一般；1 紧急；2 非常紧急 
        :param content: 内容
        :param appurl/pcrul: 跳转链接,用户点击通知链接后跳转的页面，页面地址可以和前端要
        :param entity_type: 实体类型
        :param entity_uuid: 实体uuid 
        :param Email: 本次通知是否发送email邮件，当全局邮件开关关闭时，该参数不生效。
                    全局邮件发送开关：settings.py的EMAIL_SWITCH，只有该值设置为True时，
                    create函数的email才生效。
        :param SMS: 是否发送短信提醒
        :return:空 
        """ 
        notice = Notice.objects.create(
            receiver=user, title=title, urgency_level=level, content=content)
        if appurl:
            notice.appurl = appurl
        if pcurl:
            notice.pcurl = pcurl
        if entity_type is not None:
            notice.entity_type = entity_type
        if entity_uuid:
            notice.entity_uuid = entity_uuid
       
         
        if platform:
            notice.platform = platform
        notice.save()
          
    @classmethod
    def delete(cls,  entity_type, entity_uuid,  user=None):
        """
        添加通知
        :param user: 接收用户
        :param entity_type: 通知业务分类
        :return:
        """
         
        if user:
                Notice.objects.filter(
                receiver=user, entity_type=entity_type, entity_uuid=entity_uuid).delete()
        

    @classmethod
    def complete_by_id(cls, user, title, level, content, url=None, entity_type=None,
                       entity_uuid=None, Email=False, SMS=False):
        """
        添加通知
        :param user_ids: 接收用户id列表:[1,2,3]
        :param title: 通知标题
        :param level: 紧急程度等级：0 （默认）一般；1 紧急；2 非常紧急
        :param content: 内容
        :param url: 跳转链接,用户点击通知链接后跳转的页面，页面地址可以和前端要
        :param entity_type: 实体类型
        :param entity_uuid: 实体uuid
        :param Email: 本次通知是否发送email邮件，当全局邮件开关关闭时，该参数不生效。
                    全局邮件发送开关：settings.py的EMAIL_SWITCH，只有该值设置为True时，
                    create函数的email才生效。
        :param SMS: 是否发送短信提醒
        :return:空
        """
        cls.create(title=title, level=level, content=content, user=user, url=url, entity_type=entity_type,
                   entity_uuid=entity_uuid, Email=Email, SMS=SMS)
