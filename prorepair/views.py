#! -*- coding:utf-8 -*-
import json
import pdb
import time 
import uuid
import os
from datetime import datetime
from django.http import HttpResponse
from django.utils.translation import ugettext as _ 
from prorepair.comm import single_repair, create_sms_notice
from prorepair.models import ProRepair, RepairFdkImgs
from appuser.models import AdaptorUser as User
from rest_framework.views import APIView
from common.fileupload import FileUpload
from property import settings
from property.code import SUCCESS, ERROR
from common.logutils import getLogger
from notice.comm import NoticeMgr 
from community.models import Community
from property.entity import EntityType
from community.comm import getUserCommunities

logger = getLogger(True, 'prorepair', False)
  
class ProRepairView(APIView):
    def get(self, request):
        content = {
            "status": ERROR
        }
        user = request.user
        community = None
        kwargs = {}
        if 'communityuuids' in request.GET:
            # 首页获取相关统计接口
            communityuuids = getUserCommunities(user)
            kwargs['community__uuid__in'] = list(communityuuids)
        elif 'communityuuid' in request.GET:
            communityuuid = request.GET['communityuuid']
            try:
                community = Community.objects.get(uuid=communityuuid)
                kwargs['community'] = community
            except Community.DoesNotExist:
                content['msg'] = "没有找到对应小区"
                return HttpResponse(json.dumps(content), content_type="application/json")
        else:
            content['msg'] = "缺少必须参数 community uuid"
            return HttpResponse(json.dumps(content), content_type="application/json")
        
        if 'uuid' in request.GET:
            repairuuid = request.GET['uuid']
            content = single_repair(repairuuid)
        elif "page" in request.GET and "pagenum" in request.GET:

            repair_list = []
            
            if 'tag' in request.GET:
                tag = request.GET['tag']
                try:
                    tag = int(tag)
                    if tag == 0:
                        kwargs['user'] = user
                        kwargs['owner_delete'] = 0
                except ValueError:
                    content['status'] = ERROR
                    content['msg'] = "tag参数不是int"
                    return HttpResponse(json.dumps(content), content_type="application/json")
            else:
                # 物业
                kwargs['org_delete'] = 0 
                if 'username' in request.GET:
                    username = request.GET['username']  
                    kwargs['user__username__icontains'] = username
                
                if 'keyword' in request.GET:
                    keyword = request.GET['keyword']  
                    kwargs['content__icontains'] = keyword
 
            if 'status' in request.GET:
                status = request.GET['status']
                try:
                    kwargs['status'] = int(status)
                except ValueError:
                    content['status'] = ERROR
                    content['msg'] = "status参数不是int"
                    return HttpResponse(json.dumps(content), content_type="application/json")
              
            pagenum = request.GET['pagenum']
            page = request.GET['page']
            try:
                page = int(page) - 1
                pagenum = int(pagenum)
            except ValueError:
                page = 0
                pagenum = settings.PAGE_NUM
            num = ProRepair.objects.filter(**kwargs).count() 
            repairs = ProRepair.objects.filter(
                **kwargs).order_by('-date')[page * pagenum: (page + 1) * pagenum]

            for prorepair in repairs:
                repair_list.append(single_repair(prorepair.uuid)['msg'])
            content['status'] = SUCCESS
            
            content['msg'] = {
                "list":repair_list,
                "total":num, 
            }

        return HttpResponse(json.dumps(content), content_type="application/json")

    def post(self, request):
        """
        新建
        """
        result = {
            "status": ERROR
        }

        user = request.user
        data = request.POST

        community = None
        if 'communityuuid' in data:
            communityuuid = data['communityuuid']
            try:
                community = Community.objects.get(uuid=communityuuid)
            except Community.DoesNotExist:
                result['msg'] = "没有找到对应小区"
                return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            result['msg'] = "缺少必须参数 community uuid"
            return HttpResponse(json.dumps(result), content_type="application/json")

        if 'method' in request.POST:
            method = request.POST['method'].lower()
            if method == 'put':  # 修改
                return self.put(request, community)
            elif method == 'delete':  # 删除
                return self.delete(request, community)
 
        if 'content' in data:
            content = data['content'].strip()
        else:
            content = ""

        if 'contact' in data:
            contact = data['contact'].strip()
        else:
            contact = ""

        prorepair = ProRepair()
        prorepair.uuid = uuid.uuid4()
        prorepair.community = community
        prorepair.content = content
        prorepair.contact = contact
        prorepair.user = user
        prorepair.save()
        if len(request.FILES):
            for image in request.FILES:
                # 获取附件对象
                imagefile = request.FILES[image]
                pre = datetime.now().strftime("%Y%m%d%H%M%S%f")
                file_name, file_extension = os.path.splitext(imagefile.name)
                filename = pre+file_extension
                FileUpload.upload(imagefile,
                                  os.path.join('prorepair', str(user.id)),
                                  filename)
                RepairFdkImgs.objects.create(prorepair=prorepair,
                                             filepath=os.path.join(
                                                 'prorepair', str(user.id), filename),
                                             filename=filename)

        result['status'] = SUCCESS
        result['msg'] = str(prorepair.uuid)
        # 添加通知
        NoticeMgr.create(title="新维修单", 
                         content = content, 
                         pcurl='/repair/repair-list/',
                         entity_type=EntityType.REPAIR, 
                         entity_uuid=prorepair.uuid)
        create_sms_notice(community)
        return HttpResponse(json.dumps(result), content_type="application/json")

    def put(self, request, community):
        """
        修改
        """
        result = {}
        user = request.user

        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST
        if 'uuid' in data:
            repairuuid = data['uuid']
            perm = user.has_community_perm("prorepair.prorepair.manage_prorepair", community)
            prorepair = ProRepair.objects.get(
                uuid=repairuuid, community=community)
            owner = False  # 标记是否是业主本人
            if user == prorepair.user:
                owner = True
            
            if 'manage' in data:
                # 物业工作人员结单
                owner = False

            if len(request.FILES):
                for image in request.FILES:
                    # 获取附件对象
                    imagefile = request.FILES[image]
                    pre = datetime.now().strftime("%Y%m%d%H%M%S%f")
                    file_name, file_extension = os.path.splitext(
                        imagefile.name)
                    filename = pre+file_extension
                    FileUpload.upload(imagefile,
                                      os.path.join('prorepair', str(user.id)),
                                      filename)
                    status = prorepair.NEW
                    if 'status' in data:
                        status = data['status']
                        status = int(status)
                    imagetype = RepairFdkImgs.REQUEST
                    if status == prorepair.FINISHED and perm:
                        imagetype = RepairFdkImgs.REPLY
                    filepath = os.path.join( 'prorepair', str(user.id), filename)
                    repairimg = RepairFdkImgs.objects.create(prorepair=prorepair,
                                                 imagetype = imagetype,
                                                 filepath=filepath,
                                                 filename=filename)
                result['status'] = SUCCESS
                result['msg'] = {
                    "filepath" : filepath,
                    "id":repairimg.id
                    }
                return HttpResponse(json.dumps(result), content_type="application/json")

            
            if owner == False and not perm:
                return HttpResponse('Unauthorized', status=401)

            if 'result' in data:
                fd_result = data['result'].strip()
                prorepair.result = fd_result

            if owner:
                # 打分
                if 'score' in data:
                    score = data['score'].strip()
                    try:
                        score = int(score)
                        prorepair.score = score
                    except ValueError:
                        result['status'] = ERROR
                        result['msg'] = "score参数不是int"
                        return HttpResponse(json.dumps(result), content_type="application/json")
                if 'estimate' in data:
                    estimate = data['estimate'].strip()
                    prorepair.estimate = estimate
                    prorepair.estimate_date = datetime.now()
                result['msg'] = "评价成功"
            else:
                prorepair.status = ProRepair.FINISHED
                prorepair.reply_user = user
                prorepair.reply_date = datetime.now()

                if 'result' in data:
                    repair_result = data['result']
                    prorepair.result = repair_result

                result['msg'] = "操作成功"
                # 添加通知
                NoticeMgr.create(title="维修单已完成",
                                 level=0,
                                 user=prorepair.user,
                                 content="您提交的维修单已完成，请查看", 
                                 appurl='/pages/repair/detail?uuid=' +
                                     str(prorepair.uuid),
                                 entity_type= EntityType.REPAIR, entity_uuid=prorepair.uuid)
            prorepair.save()
            result['status'] = SUCCESS
        else:
            result['status'] = ERROR
            result['msg'] = "ids参数为必需参数"
        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self, request, community):
        """
        删除
        """
        result = {}
        user = request.user
        perms = user.has_community_perm(
            "prorepair.prorepair.manage_prorepair", community)

        if 'uuids' in request.POST:
            uuids = request.POST['uuids']
            uuids = uuids.split(",")

            if perms:
                # 物业删除
                ProRepair.objects.filter(uuid__in=uuids, community=community).update(
                    org_delete=1
                )

            RepairFdkImgs.objects.filter(prorepair__uuid__in=uuids,
                                         prorepair__user=user,
                                         prorepair__status=ProRepair.NEW,
                                         ).delete()
            ProRepair.objects.filter(uuid__in=uuids,
                                     user=user,
                                     status=ProRepair.NEW).delete()  # 已提交状态的可以删除

            ProRepair.objects.filter(uuid__in=uuids,
                                     community=community,
                                     user=user
                                     ).update(
                owner_delete=1
            )
            result['status'] = SUCCESS
            result['msg'] = _("已删除")
        elif 'imgid' in request.POST:
            imgid = request.POST['imgid']
            if perms:
                RepairFdkImgs.objects.filter(id=imgid).delete()
                result['status'] = SUCCESS
                result['msg'] = "已删除"
            else:
                result['status'] = ERROR
                result['msg'] = "权限不足"
        else:
            result['status'] = ERROR
            result['msg'] = "请发送ids参数"

        return HttpResponse(json.dumps(result), content_type="application/json")

 