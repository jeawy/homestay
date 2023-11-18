#! -*- coding:utf-8 -*-
import json
import pdb
import time 
from django.http import HttpResponse
from django.views import View 
from django.utils.translation import ugettext as _
from notice.models import Notice   
from rest_framework.views import APIView 
from property.code import SUCCESS, ERROR
from django.conf import settings
from organize.comm import getUserOrganize


def get_notice_dict(notice):
    '''
    返回notice的字典实例
    字典格式：
    {
        "id": notice.id,
        "title": notice.title,
        "content": notice.content,
        "receiver": notice.receiver,
        "urgency_level": notice.urgency_level,
        "entity_uuid": notice.entity_uuid,
        "read": notice.read,
        "url": notice.url,
        "date": date,
        "modify_date": modify_date,
        "entity_type": entity_type,
    }
    '''  
    # 任务创建时间
    date = time.mktime(notice.date.timetuple())
    # 任务开始时间
    modify_date = time.mktime(notice.modify_date.timetuple())
   
    notice_dict = {
        "id": notice.id,
        "title": notice.title,
        "content": notice.content,
        "receiver": notice.receiver.id,
        "urgency_level": notice.urgency_level,
        "entity_uuid": notice.entity_uuid,
        "read": notice.read,
        "url": notice.url,
        "date": date,
        "modify_date": modify_date,
        "entity_type": notice.entity_type, 
    } 
    return notice_dict


class NoticeAnonymousView(View):
    # 不需要登录就可以查看的通知:如小区的公告通知等
    pass


class NoticeView(APIView):
    
    def get(self, request):
        content = {}
        user = request.user  
        kwargs = {}
        updatekwargs = {
            "receiver":user,
            "read":Notice.UNREAD
        }
       
        if 'entity_type' in request.GET:
            entity_type = request.GET['entity_type']
            try:
                kwargs['entity_type'] = int(entity_type)
                content['entity_type'] = kwargs['entity_type']
            except ValueError:
                pass
        pc = False
        if 'pc' in request.GET:
            # PC端物业获取通知
            pc = True 
            kwargs['platform'] = 1
            unreadcount = Notice.objects.filter(platform = 1, read=Notice.UNREAD).count() 
        else:
            kwargs['receiver'] = user 
            unreadcount = Notice.objects.filter(receiver = user, read=Notice.UNREAD).count() 
             
        if 'read' in request.GET:
            read = request.GET['read']
            if int(read) != -1: 
                kwargs['read'] = read

        if "page" in request.GET and "pagenum" in request.GET:
            # 分页
            pagenum = request.GET['pagenum']
            page = request.GET['page']
            try:
                page = int(page) - 1
                pagenum = int(pagenum)
            except ValueError:
                page = 0
                pagenum = settings.PAGE_NUM 
        else:
            page = 0
            pagenum = settings.PAGE_NUM
         
        # PC端请求通知
        total = Notice.objects.filter(**kwargs).count() 
        notices = list(Notice.objects.filter(**kwargs).order_by('-urgency_level','-date')\
                [page*pagenum : (page+1)*pagenum].values('id','title',
                                            'content',  'urgency_level','entity_uuid','read',
                                            'appurl', 'pcurl','date', 'entity_type'))
            
        for notice in notices: 
            notice['date'] = time.mktime(notice['date'].timetuple()) 

        content['status'] = SUCCESS
        content['msg'] = {
            "list":notices,
            "total":total,
            "unreadcount":unreadcount
        }

        return HttpResponse(json.dumps(content), content_type="application/json")

    
    def post(self, request):
        """
        删除消息
        """
        result = {}
        user = request.user 
        if 'pc' in request.POST and 'ids' in request.POST:
            # 物业删除或者标记已读
            ids = request.POST['ids']
            ids = ids.split(",") 
            kwargs = {} 
            kwargs['platform'] = 1
            kwargs['id__in'] = ids
            result['status'] = SUCCESS
            if 'delete' in request.POST:
                # 删除
                Notice.objects.filter(**kwargs).delete()
                result['msg'] =  "已删除"
            else:
                # 标记为已读
                Notice.objects.filter(**kwargs).update(read = Notice.READ)
                result['msg'] =  "已标记为已读"
        elif 'ids' in request.POST:
            ids = request.POST['ids']
            ids = ids.split(",")
            if 'read' in request.POST:
                Notice.objects.filter(id__in = ids ).update(
                    read = Notice.READ
                )
            else:
                Notice.objects.filter(id__in = ids).delete() 
                result['msg'] =  "已删除"
            result['status'] = SUCCESS
        else:
            result['status'] = ERROR
            result['msg'] = "需要ids"

        return HttpResponse(json.dumps(result), content_type="application/json")

