import pdb 
import os
import random
import uuid
from property.entity import EntityType
from rest_framework.views import APIView
from django.db.models import Sum, Avg
from django.views import View
from appuser.models import AdaptorUser as User
from django.http import HttpResponse
from common.fileupload import FileUpload
from comment.models import Comment, CommentImgs
from datetime import datetime
from common.logutils import getLogger
import json
import time
from bills.models import Bills 
from comment.comm import get_comments_list, cal_rate , get_comments_sub_list
from property import settings
from property.code import * 
from organize.models import Organize
from notice.comm import NoticeMgr
logger = getLogger(True, 'comment', False)


class CommentAnonymousView(View):
    def get(self, request):
        content = {}  
        kwargs = {} 

        if 'entity_uuid' in request.GET and 'entity_type' in request.GET :
            entity_uuid = request.GET['entity_uuid']
            entity_type = request.GET['entity_type']
             
            kwargs['entity_uuid'] = entity_uuid 
            kwargs['entity_type'] = entity_type  

            kwargs['pid__isnull'] = True 
            if 'ratesummary' in  request.GET:
                #评分统计
                '''
                summary:{//评分总统计 
                    total_service_rate:5,
                    total_health_rate:5,
                    total_real_rate : 5,
                    total_location_rate :5,
                }
                '''
                rates = Comment.objects.filter( **kwargs).aggregate(
                    Avg("rate"), Avg("real_rate"), Avg("service_rate"), 
                    Avg("health_rate"), Avg("location_rate"), 
                )
                summary = {  
                    "total_service_rate":round (rates['service_rate__avg'], 1)   if rates['service_rate__avg'] else "--",
                    "total_health_rate":round (rates['health_rate__avg'], 1)   if rates['health_rate__avg'] else "--",
                    "total_real_rate" : round (rates['real_rate__avg'], 1) if rates['real_rate__avg'] else "--",
                    "total_location_rate" :round (rates['location_rate__avg'], 1)   if rates['location_rate__avg'] else "--",
                }
                content['status'] = SUCCESS
                content['msg'] = summary
                return HttpResponse(json.dumps(content), content_type="application/json")
            
            elif "page" in request.GET and "pagenum" in request.GET:
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
            
            total = Comment.objects.filter( **kwargs).count() 
            comments = Comment.objects.filter( **kwargs)\
                [page*pagenum: (page+1)*pagenum] 
                      
            content['status'] = SUCCESS
            content['msg'] = {
                "total" : total,
                "list" : get_comments_sub_list(comments)
            } 
        else:
            content['status'] = COMMENT.COMMENT_ARGUMENT_ERROR_CONTENT_EMPTY
            content['msg'] = "参数错误：需要ID或者entity_uuid和entity_type" 

        return HttpResponse(json.dumps(content), content_type="application/json")


class CommentView(APIView): 
    def get(self, request):
        """
        查询
        """
        # 
        content = {} 
        user = request.user
        kwargs = {}
        if 'id' in request.GET:
            comment_id = request.GET['id']
            try:
                comment_id = int(comment_id)
            except ValueError:
                content['status'] = ARGUMENT_ERROR_ID_NOT_INT
                content['msg'] = 'id not int'
                return HttpResponse(json.dumps(content), content_type="application/json")
 
            comments = Comment.objects.filter(id=comment_id)
            content['status'] = SUCCESS
            comment_list = get_comments_list(comments)
            if comment_list : 
                content['msg'] = get_comments_list(comments)[0]
            else:
                content['msg'] = []
        elif 'entity_uuid' in request.GET and 'entity_type' in request.GET :
            entity_uuid = request.GET['entity_uuid']
            entity_type = request.GET['entity_type']
            try:
                int (entity_uuid)
                int(entity_type)
            except ValueError:
                content['status'] = COMMENT.COMMENT_ARGUMENT_ERROR_CONTENT_EMPTY
                content['msg'] = "参数错误：entity_uuid:{0}, entity_type:{1}不是整数".format(entity_uuid,entity_type )
                return HttpResponse(json.dumps(content), content_type="application/json")

            kwargs['pid__isnull'] = True
            kwargs['entity_uuid'] = entity_uuid
            kwargs['entity_type'] = entity_type
            if 'name' in request.GET:
                name = request.GET['name']
                kwargs['content__icontains'] = name
            comments = Comment.objects.filter( **kwargs)
            comments_list = get_comments_list(comments)
            
            content['status'] = SUCCESS
            content['msg'] = comments_list
        else:
            content['status'] = COMMENT.COMMENT_ARGUMENT_ERROR_CONTENT_EMPTY
            content['msg'] = "参数错误：需要ID或者entity_uuid和entity_type" 

        return HttpResponse(json.dumps(content), content_type="application/json")

    
    def post(self, request):
        """
        创建评论信息
        """
        result = {}
        user = request.user
        # 新建 
        if 'method' in request.POST:
            method = request.POST['method'].lower()
            if method == 'delete':  # 删除
                return self.delete(request)
            elif method == 'put':  # 删除
                return self.put(request)

        comment = Comment()
        comment.creator = user
  
        # 内容 必填项
        if 'content' in request.POST and 'entity_uuid' in request.POST and \
            'entity_type' in request.POST and 'url'   in request.POST:
            content = request.POST['content'].strip()
            entity_uuid = request.POST['entity_uuid'].strip()
            entity_type = request.POST['entity_type'].strip()
            url = request.POST['url'].strip()
            if content:
                comment.content = content
            else:
                result['status'] = COMMENT.COMMENT_ARGUMENT_ERROR_CONTENT_EMPTY
                result['msg'] = '请输入评价内容'
                return HttpResponse(json.dumps(result), content_type="application/json")
            
            comment.entity_uuid = entity_uuid  
            comment.entity_type = entity_type
            comment.url = url 
            comment.uuid = uuid.uuid4()
            

            if 'rate' in request.POST:
                rate = request.POST['rate']
                comment.rate = rate
            
            if 'real_rate' in request.POST:
                real_rate = request.POST['real_rate']
                comment.real_rate = real_rate

            if 'service_rate' in request.POST:
                service_rate = request.POST['service_rate']
                comment.service_rate = service_rate
            
            if 'health_rate' in request.POST:
                health_rate = request.POST['health_rate']
                comment.health_rate = health_rate 
            
            if 'location_rate' in request.POST:
                location_rate = request.POST['location_rate']
                comment.location_rate = location_rate

            if 'billuuid' in request.POST:
                billuuid = request.POST['billuuid'] 
                try:
                    bill = Bills.objects.get(uuid = billuuid)
                    comment.bill = bill
                    bill.status = bill.COMMENTED
                    bill.save()
                except Bills.DoesNotExist:
                    result['msg'] = '订单不存在'
                    return HttpResponse(json.dumps(result), content_type="application/json")

            if 'useruuid' in request.POST:
                useruuid = request.POST['useruuid']
                try:
                    comment.user = User.objects.get(uuid = useruuid)
                    comment.comeway = 0 # 虚拟评价
                except User.DoesNotExist:
                    result['msg'] = '用户不存在'
                    return HttpResponse(json.dumps(result), content_type="application/json")
            else:
                comment.user = user
            
            if 'datetime' in request.POST:
                datetimestr = request.POST['datetime']
                comment.date  = datetime.strptime(datetimestr, settings.DATETIMEFORMAT)
            else:
                comment.date = datetime.now()
                 
        
            pcurl = "/product-manage/product-detail?uuid="+entity_uuid
            # pid 必填项
            if 'puuid' in request.POST:
                puuid = request.POST['puuid'].strip()
                try: 
                    parent_id = Comment.objects.get(uuid=puuid)
                    comment.pid = parent_id 

                    # 发消息给评论人
                    title = "{0}回复了您的评论".format(user.username) 
                    appurl = url
                    NoticeMgr.create(
                        title = title,
                        content = content, 
                        user = parent_id.user,
                        appurl = appurl, 
                        pcurl = pcurl,
                        entity_type = EntityType.COMMENT,
                        entity_uuid = entity_uuid  
                    ) 
                except Comment.DoesNotExist:
                    result['status'] =ERROR
                    result['msg'] = 'pid not found.'
                    return HttpResponse(json.dumps(result), content_type="application/json") 
            comment.save()
            cal_rate(entity_uuid, entity_type)
            # 更新商品评分

            # 发消息通知
            if 'orguuid' in request.POST:
                # 目前获得点赞的文章都是物业发出的，所以消息通知会发给物业
                # 发送消息
                title = "{0}发表了评论".format(user.username) 
                appurl = url
                orguuid = request.POST['orguuid']
                try:
                    org = Organize.objects.get(uuid = orguuid)
                    NoticeMgr.create(
                        title = title,
                        content = content, 
                        organize = org,
                        appurl = appurl, 
                        pcurl = pcurl,
                        entity_type = EntityType.COMMENT,
                        entity_uuid = entity_uuid  
                    )
                except Organize.DoesNotExist:
                    logger.debug("因为org不存在而未成功发送评论消息")
                    
            result['uuid'] = str(comment.uuid)
            result['status'] = SUCCESS
            result['msg'] = '已完成'
        else:
            result['status'] = COMMENT.COMMENT_ARGUMENT_ERROR_NEED_CONTENT
            result['msg'] = 'Need content entity in POST.'
        return HttpResponse(json.dumps(result), content_type="application/json")
    

    def put(self, request):
        # 上传图片
        data = request.POST
        result = {} 
        if 'uuid' in data:
            user = request.user
            instance_uuid = data['uuid']
            try:
                comment = Comment.objects.get(uuid=instance_uuid)
                logger.warning("delete content:{0}, pid:{1}, entity_uuid:{2}, entity_type:{3}".
                               format(comment.content, comment.pid,
                                      comment.entity_uuid, comment.entity_type))
                
                if len(request.FILES):
                    # 存文件
                    for image in request.FILES:
                        # 获取附件对象
                        imagefile = request.FILES[image]
                        pre = datetime.now().strftime("%Y%m%d%H%M%S%f")
                        file_name, file_extension = os.path.splitext(
                            imagefile.name)
                        filename = pre+file_extension
                        FileUpload.upload(imagefile,
                                            os.path.join(
                                                'comments', str(user.id)),
                                            filename)
                        CommentImgs.objects.create(comment=comment,
                                                filepath=os.path.join(
                                                    'comments', str(user.id), filename),
                                                filename=filename)  
                result['status'] = SUCCESS
                result['msg'] = '已保存'
            except Comment.DoesNotExist:
                result['status'] = ERROR
                result['msg'] = '404 Not found the id'
        else:
            result['status'] = ERROR
            result['msg'] = 'Need id in POST'
        return HttpResponse(json.dumps(result), content_type="application/json")
        
    def delete(self, request):
        """
        删除功能
        """
        result = {}
        user = request.user
        # 应加权限验证
        data = request.POST
        if 'uuid' in data:
            instance_uuid = data['uuid']
            try:
                comment = Comment.objects.get(uuid=instance_uuid)
                logger.warning("delete content:{0}, pid:{1}, entity_uuid:{2}, entity_type:{3}".
                               format(comment.content, comment.pid,
                                      comment.entity_uuid, comment.entity_type))
                
                CommentImgs.objects.filter(comment = comment).delete()
                # 删除的时候，更新评分
                cal_rate(comment.entity_uuid,  EntityType.PRODUCT)
                comment.delete()
                result['status'] = SUCCESS
                result['msg'] = '已删除'
            except Comment.DoesNotExist:
                result['status'] = COMMENT.COMMENT_ID_NOTFOUND
                result['msg'] = '404 Not found the id'
        else:
            result['status'] = COMMENT.COMMENT_ARGUMENT_ERROR_NEED_ID
            result['msg'] = 'Need id in POST'

        return HttpResponse(json.dumps(result), content_type="application/json")
