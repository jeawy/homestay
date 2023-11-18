#! -*- coding:utf-8 -*-
import json
import pdb
import time
import os
from datetime import datetime 
from django.http import HttpResponse
from django.utils.translation import ugettext as _
from django.views import View
from feedback.comm import single_feedback
from feedback.models import Feedback, FdkImgs
from appuser.models import AdaptorUser as User
from rest_framework.views import APIView
from common.fileupload import FileUpload
from property import settings
from property.code import SUCCESS, ERROR 
from common.logutils import getLogger 
from common.e_mail import Email, EmailEx
logger = getLogger(True, 'feedback', False)


class FeedbackView(APIView): 
    def get(self, request):
        content = {}
        user = request.user
       
        if 'id' in request.GET:
            id = request.GET['id']
            content = single_feedback(id)
        elif "page" in request.GET and "pagenum" in request.GET:
            kwargs = {}
            feedback_list = []
            if 'tag' in request.GET:
                tag = request.GET['tag']
                try:
                    tag = int(tag)
                    if tag == 0:
                        kwargs['user'] = user
                except ValueError:
                    content['status'] = ERROR
                    content['msg'] = "tag参数不是int"
                    return HttpResponse(json.dumps(content), content_type="application/json")
            if 'read' in request.GET:
                read = request.GET['read']
                try:
                    kwargs['read'] = int(read)
                except ValueError:
                    content['status'] = ERROR
                    content['msg'] = "read参数不是int"
                    return HttpResponse(json.dumps(content), content_type="application/json")

            if 'status' in request.GET:
                status = request.GET['status']
                try:
                    kwargs['status'] = int(status)
                except ValueError:
                    content['status'] = ERROR
                    content['msg'] = "status参数不是int"
                    return HttpResponse(json.dumps(content), content_type="application/json")
            # 未读意见反馈
            unread_count = Feedback.objects.filter(read=Feedback.UNREAD).count()
            content['unread_count'] = unread_count
            pagenum = request.GET['pagenum']
            page = request.GET['page']
            try:
                page = int(page) - 1
                pagenum = int(pagenum)
            except ValueError:
                page = 0
                pagenum = settings.PAGE_NUM
            num = Feedback.objects.filter(**kwargs).count()
            content['count'] = num
            if num % pagenum == 0:
                content['page_count'] = int(num / pagenum)
            else:
                content['page_count'] = int(num / pagenum) + 1
            feedbacks = Feedback.objects.filter(**kwargs).order_by('-date') \
                            [page * pagenum: (page + 1) * pagenum]
            
            for feedback in feedbacks:
                feedback_list.append(single_feedback(feedback.id)['msg'])
            content['status'] = SUCCESS
            content['unread_count'] = unread_count
            content['msg'] = feedback_list
         
        return HttpResponse(json.dumps(content), content_type="application/json")
         
 
    def post(self, request):
        """
        新建
        """
        result = {} 
        content = {}
        user = request.user
        if 'method' in request.POST:
            method = request.POST['method'].lower()
            if method == 'put':  # 修改
                return self.put(request)
            elif method == 'delete':  # 删除
                return self.delete(request)

        # 新建
        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST
        
        logger.debug(json.dumps(data))
        if 'md' in data:
            device =  data['md'].strip()
        else:
            device =  ""

        if 'os' in data:
            sysos =  data['os'].strip()
        else:
            sysos =  ""
        
        if 'content' in data:
            content =  data['content'].strip()
        else:
            content =  ""
        
        if 'contact' in data:
            contact =  data['contact'].strip()
        else:
            contact =  ""

        if 'score' in data:
            score =  data['score'].strip()
            try:
                score = int(score)
            except ValueError:
                result['status'] = ERROR
                result['msg'] = "score参数不是int"
                return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            score =  None

        feedback = Feedback()
        feedback.device = device
        feedback.os = sysos
        feedback.content = content
        feedback.contact = contact
        feedback.score = score 
        feedback.user = user
        feedback.save() 
        if len(request.FILES) : 
            for image in request.FILES:
                # 获取附件对象 
                imagefile = request.FILES[image]
                pre = datetime.now().strftime("%Y%m%d%H%M%S%f")
                file_name, file_extension = os.path.splitext(imagefile.name)
                filename = pre+file_extension
                FileUpload.upload(imagefile, 
                               os.path.join('feedback', str(user.id)), 
                               filename )
                FdkImgs.objects.create(feedback=feedback,
                filepath= os.path.join('feedback', str( user.id), filename) ,
                                 filename=filename)
        result['status'] = SUCCESS
        result['msg'] = feedback.id
          
        return HttpResponse(json.dumps(result), content_type="application/json")

    def put(self, request):
        """
        修改
        """
        result = {}
        user = request.user

        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST
        if 'ids' in data:
            if 'read' in data:
                ids = data['ids']
                read = data['read']
                ids = ids.split(",")
                notices = Feedback.objects.filter(id__in = ids)
                if int(read) in [Feedback.READ,Feedback.UNREAD]:
                    for feedback in notices:
                        feedback.read = read
                        feedback.save()
                else:
                    result['status'] = ERROR
                    result['msg'] = "read参数只能为0或1"
                    return HttpResponse(json.dumps(result), content_type="application/json")

                result['status'] = SUCCESS
                result['msg'] = "操作成功"
            elif 'status' in data:
                ids = data['ids']
                ids = ids.split(",")
                notices = Feedback.objects.filter(id__in=ids)
                status = data['status']
                try:
                    status = int(status)
                except ValueError:
                    result['status'] = SUCCESS
                    result['msg'] = "status不是int"
                if 'result' in data:
                    fd_result = data['result'].strip()
                if status in [Feedback.NEW, Feedback.ACCEPTED, Feedback.FINISHED]:
                    for feedback in notices:
                        feedback.result = fd_result
                        feedback.status = status 
                        feedback.save()
                else:
                    result['status'] = ERROR
                    result['msg'] = "status参数只能为0或1或2"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                result['status'] = SUCCESS
                result['msg'] = "操作成功"
            else:
                result['status'] = ERROR
                result['msg'] = "缺失参数read或者status"
        if 'id' in request.POST:
            # 微信小程序单个文件上传
            feedbackid = request.POST['id']
            try:
                feedback = Feedback.objects.get(user = user, id= feedbackid)
                if len(request.FILES) : 
                    for image in request.FILES:
                        # 获取附件对象 
                        imagefile = request.FILES[image]
                        pre = datetime.now().strftime("%Y%m%d%H%M%S%f")
                        file_name, file_extension = os.path.splitext(imagefile.name)
                        filename = pre+file_extension
                        FileUpload.upload(imagefile, 
                                    os.path.join('feedback', str(user.id)), 
                                    filename )
                        FdkImgs.objects.create(feedback=feedback,
                        filepath= os.path.join('feedback', str( user.id), filename) ,
                                        filename=filename) 
                result['status'] = SUCCESS
                result['msg'] = "上传成功" 
            except Feedback.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = "未找到对应反馈" 
        else:
            result['status'] = ERROR
            result['msg'] = "ids参数为必需参数"
        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self, request):
        """
        删除
        """
        result = {}
        if len(request.POST) == 0:
            request.POST = request.data

        if 'ids' in request.POST:
            ids = request.POST['ids']
            ids = ids.split(",") 
            FdkImgs.objects.filter(feedback__id__in = ids).delete()
            Feedback.objects.filter(id__in = ids).delete()
            result['status'] = SUCCESS
            result['msg'] = _("已删除")
        else:
            result['status'] = ERROR
            result['msg'] = "请发送ids参数"

        return HttpResponse(json.dumps(result), content_type="application/json")

class FeedbackEmail(View):
    def post(self, request):
        """
        新建用户
        """
        content = {} 
        feedbacks = Feedback.objects.filter(read = Feedback.UNREAD)
        for feedback in feedbacks:
            title = '有新反馈来了'
            
            email_content = '用户：{0}提交了反馈：{1}'.\
                                format(feedback.user.username, feedback.content)
            emailex = EmailEx()
            emailex.send_html_email(title, email_content, settings.RECEIVE_EMAIL)
            feedback.read = Feedback.READ
            feedback.save()
            
        return HttpResponse(json.dumps(content), content_type="application/json")