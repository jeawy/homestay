from common.logutils import getLogger
import pdb  
from rest_framework.views import APIView
from django.http import HttpResponse 
from like.models import Like, Readcount
from django.views import View 
import json 
from property.code import ERROR, SUCCESS  
from notice.comm import NoticeMgr
from property.entity import EntityType
from organize.models import Organize
logger = getLogger(True, 'like', False)


class CountAnonymousView(View): 
    def get(self, request):
        """
        查询
        """
        # 
        content = {}  
        if 'entity_uuid' in request.GET and 'entity_type' in request.GET:
            entity_uuid = request.GET['entity_uuid']
            entity_type = request.GET['entity_type']
            try:
                readcount = Readcount.objects.get(
                            entity_uuid=entity_uuid,
                             entity_type=entity_type) 
                content['msg'] = readcount.number 
            except Readcount.DoesNotExist:
                content['msg'] = 1 
            content['status'] = SUCCESS  
        else:
            content['status'] = ERROR
            content['msg'] = "参数错误：需要entity_uuid或者entity_type" 

        return HttpResponse(json.dumps(content), content_type="application/json")


class LikeAnonymousView(View): 
    def get(self, request):
        """
        查询
        """
        # 
        content = {}  
        if 'entity_uuid' in request.GET and 'entity_type' in request.GET:
            entity_uuid = request.GET['entity_uuid']
            entity_type = request.GET['entity_type']
             
            likes = list(Like.objects.filter(
                            entity_uuid=entity_uuid,
                             entity_type=entity_type).\
                                 values("user__thumbnail_portait",
                                 "user__username")) 
            content['status'] = SUCCESS 
            content['msg'] = likes 
        else:
            content['status'] = ERROR
            content['msg'] = "参数错误：需要entity_uuid或者entity_type" 

        return HttpResponse(json.dumps(content), content_type="application/json")


class LikeView(APIView):  
    def post(self, request):
        """
        点赞信息
        """
        result = {}
        user = request.user
          
        if 'entity_uuid' in request.POST \
               and 'entity_type' in request.POST and \
               'url' in request.POST:
            entity_uuid = request.POST['entity_uuid'].strip()
            entity_type = request.POST['entity_type'].strip()
            url = request.POST['url'].strip()
            like, created =  Like.objects.get_or_create(user = user, 
                             entity_type = entity_type,
                             entity_uuid = entity_uuid)
            if not created:
                # 取消赞
                like.delete()
            else:
                like.url = url 
                like.save()
                # 点赞 
                if 'orguuid' in request.POST:
                    # 目前获得点赞的文章都是物业发出的，所以消息通知会发给物业
                    # 发送消息
                    title = "{0}赞了你".format(user.username) 
                    appurl = like.url
                    pcurl = '/product/product-detail?id='+entity_uuid
                    orguuid = request.POST['orguuid']
                    try:
                        org = Organize.objects.get(uuid = orguuid)
                        NoticeMgr.create(
                            title = title,
                            content = "",  
                            appurl = appurl, 
                            pcurl = pcurl,
                            entity_type = EntityType.LIKE,
                            entity_uuid = entity_uuid  
                        )
                    except Organize.DoesNotExist:
                        logger.debug("因为org不存在而未成功发送点赞消息")
                        
 
            result['status'] = SUCCESS
            result['msg'] = '已完成'
        else:
            result['status'] = ERROR
            result['msg'] = 'Need entity_uuid 和 entity_typein POST.' 
        return HttpResponse(json.dumps(result), content_type="application/json")

    