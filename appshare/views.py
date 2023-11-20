from django.shortcuts import render
from django.views import View
from property.entity import EntityType
from record.models import Record
from aid.models import Aid
from content.models import   TxtContent
from django.conf import settings

class ShareView(View):
    def get(self, request):
        # 打开网页分享页面
        context = {
            "title":"",
            "username":"",
            "date":"",
            "content":"" 
        }
        if 'entity_type' in request.GET and 'entity_uuid' in request.GET:
            try:
                entity_type = int(request.GET['entity_type'])
                entity_uuid = request.GET['entity_uuid']
                context['entity_type'] = entity_type
                context['entity_uuid'] = entity_uuid
                if entity_type == EntityType.RECORD:
                    # 登记薄
                    try:
                        record = Record.objects.get(uuid = entity_uuid)
                        context['title'] = record.title
                        context['content'] = record.content
                        context['date'] = record.date.strftime(settings.DATETIMEFORMAT)
                        context['username'] =  record.owner.username 
                    except Record.DoesNotExist:
                        pass
                elif entity_type == EntityType.PRODUCT:
                    # 通知、公告、百事通、社区见闻
                    try:
                        product = Product.objects.get(uuid = entity_uuid)
                        context['title'] = product.title
                        context['content'] = product.detail
                        if product.community:
                            context['username'] =  product.community.name 

                        context['date'] =  product.date.strftime(settings.DATETIMEFORMAT)
                        
                    except Product.DoesNotExist:
                        pass
                elif entity_type == EntityType.AID:
                    # 互助服务
                    try:
                        aid = Aid.objects.get(uuid = entity_uuid)
                        context['title'] = aid.title + "【佣金:" + str(aid.money) + "】元"
                        context['content'] = aid.content + '<br/><br/><br/><br/><strong style="color:#ff8000">打开社区互通APP，进行抢单，丰厚佣金等你来拿。</strong>'
                        context['date'] =  aid.date.strftime(settings.DATETIMEFORMAT)
                        context['username'] =  aid.user.username 
                    except Aid.DoesNotExist:
                        pass 
            except ValueError:
                pass 
        return render(request, 'share.html', context)


