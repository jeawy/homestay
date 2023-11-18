#! -*- coding:utf-8 -*-
import json
import pdb
import time
import os
import uuid
from django.core.checks.messages import Error
from django.db.models import Sum, Count
from datetime import datetime
from django.http import HttpResponse
from django.views import View
from django.conf import settings
from aid.comm import single_aid
from aid.comm_order import create_order
from appuser.models import AdaptorUser as User
from building.comm_fee import delete_unpay_bills
from notice.comm import NoticeMgr
from property.entity import EntityType
from rest_framework.views import APIView
from common.fileupload import FileUpload
from property.code import SUCCESS, ERROR
from common.logutils import getLogger
from community.models import Community
from aid.comm import verify_data
from role.models import Cert
from aid.models import Aid, AidImgs, AidOrders, Entries, AidCommunities
from property.settings import DATEFORMAT
logger = getLogger(True, 'aid', False)


class AnonymousAidView(View):
    # 匿名获取互助单、互助广场
    def get(self, request):
        content = {
            "status": ERROR
        }
        if 'uuid' in request.GET:
            aiduuid = request.GET['uuid']
            try:
                content['status'] = SUCCESS
                content['msg'] = single_aid(Aid.objects.get(uuid=aiduuid), user=None, need_detail=True)
            except Aid.DoesNotExist:
                content['msg'] = "没有找到互助单"
        elif "page" in request.GET and "pagenum" in request.GET:
            kwargs = {
                "status": Aid.OPEN,  # 默认展示正在进行的互助单
                "payed": Aid.YES ,# 默认展示已支付的
            }
            aids_list = []

            if 'title' in request.GET:
                title = request.GET['title']
                kwargs['title__icontains'] = title

            if 'status' in request.GET:
                status = request.GET['status']
                try:
                    kwargs['status'] = int(status)
                except ValueError:
                    content['status'] = ERROR
                    content['msg'] = "status参数不是int"
                    return HttpResponse(json.dumps(content), content_type="application/json")

            if 'aidtype' in request.GET:
                aidtype = request.GET['aidtype']
                kwargs['aidtype'] = aidtype

            if 'communityuuids' in request.GET:
                # 附近一公里搜索，前端传回一公里内的小区uuid
                # （APP首页获取到附近的小区之后，进行缓存，然后传到这里)
                communityuuids = request.GET['communityuuids']
                communityuuids = communityuuids.split(",")
                kwargs['community__uuid__in'] = communityuuids
            sort = "-date"  # 默认按照最新日期倒序
            if 'sort' in request.GET:
                sort = request.GET['sort']
                if sort == 'money':
                    # 按照佣金从高到底
                    sort = "-money"
                else:
                    sort = "-date"

            pagenum = request.GET['pagenum']
            page = request.GET['page']
            try:
                page = int(page) - 1
                pagenum = int(pagenum)
            except ValueError:
                page = 0
                pagenum = settings.PAGE_NUM
            total = Aid.objects.filter(**kwargs).count()
            aids = Aid.objects.filter(
                **kwargs).order_by(sort)[page * pagenum: (page + 1) * pagenum]

            for aid in aids:
                aids_list.append(single_aid(aid, user= None))
            content['status'] = SUCCESS
            content['msg'] = {
                "list": aids_list,
                "total": total
            }
        return HttpResponse(json.dumps(content), content_type="application/json")


class AidView(APIView):
    def get(self, request):
        # 获取自己的互助单
        content = {
            "status": ERROR
        }
        user = request.user
        if 'uuid' in request.GET:
            aiduuid = request.GET['uuid']
            try:
                content['status'] = SUCCESS
                content['msg'] = single_aid(
                    Aid.objects.get(user=user, uuid=aiduuid), user, need_detail=True)
            except Aid.DoesNotExist:
                content['msg'] = "没有找到互助单"
        elif "page" in request.GET and "pagenum" in request.GET:
            kwargs = {}
            aids_list = []
            user = request.user
            if 'title' in request.GET:
                title = request.GET['title']
                kwargs['title__icontains'] = title

            if 'status' in request.GET:
                status = request.GET['status']
                try:
                    kwargs['status'] = int(status)
                except ValueError:
                    content['status'] = ERROR
                    content['msg'] = "status参数不是int"
                    return HttpResponse(json.dumps(content), content_type="application/json")

            if 'communityuuids' in request.GET:
                # 附近一公里搜索，前端传回一公里内的小区uuid
                # （APP首页获取到附近的小区之后，进行缓存，然后传到这里)
                communityuuids = request.GET['communityuuids']
                communityuuids = communityuuids.split(",")
                kwargs['community__uuid__in'] = communityuuids

            if 'action' in request.GET:
                # 获取我的求助
                action = request.GET['action']
                if action == 'mine':
                    kwargs['user'] = user
                else:
                    kwargs['answer'] = user

            if 'aidtype' in request.GET:
                aidtype = request.GET['aidtype']
                kwargs['aidtype'] = aidtype

            sort = "-date"  # 默认按照最新日期倒序
            if 'sort' in request.GET:
                sort = request.GET['sort']
                if sort == 'money':
                    # 按照佣金从高到底
                    sort = "-money"
                else:
                    sort = "-date"

            pagenum = request.GET['pagenum']
            page = request.GET['page']
            try:
                page = int(page) - 1
                pagenum = int(pagenum)
            except ValueError:
                page = 0
                pagenum = settings.PAGE_NUM
            total = Aid.objects.filter(**kwargs).count()
            aids = Aid.objects.filter(
                **kwargs).order_by(sort)[page * pagenum: (page + 1) * pagenum]

            for aid in aids:
                aids_list.append(single_aid(aid, user, mine=True))
            content['status'] = SUCCESS
            content['msg'] = {
                "list": aids_list,
                "total": total
            }
        return HttpResponse(json.dumps(content), content_type="application/json")

    def post(self, request):
        """
        新建
        """
        result = {
            "status": ERROR
        }
        if 'method' in request.POST:
            method = request.POST['method'].lower()
            if method == 'put':  # 修改
                return self.put(request)
            elif method == 'delete':  # 删除
                return self.delete(request)

        data = request.POST
        if 'communityuuid' in data and 'title' in data and 'money' in data:
            user = request.user
            communityuuid = data['communityuuid']
            status, msg = verify_data(data)
            if status == SUCCESS:
                try:
                    community = Community.objects.get(uuid=communityuuid)
                    title = data['title'].strip()
                    money = data['money']
                    aid = Aid()
                    aid.uuid = uuid.uuid4()
                    aid.user = user
                    aid.title = title
                    if 'content' in data:
                        content = data['content']
                        aid.content = content
                    aid.community = community
                    aid.money = money
                    


                    if 'end_date' in data:
                        end_date = data['end_date']
                        end_date = end_date.replace("-", "/")
                        end_date = datetime.strptime(end_date, DATEFORMAT)
                        aid.end_date = end_date

                    if 'publich_myinfo' in data:
                        publich_myinfo = data['publich_myinfo']
                        aid.publich_myinfo = publich_myinfo

                    if 'secretinfo' in data:
                        secretinfo = data['secretinfo']
                        aid.secretinfo = secretinfo
                    if 'need_propertior' in data:
                        need_propertior = data['need_propertior']
                        aid.need_propertior = need_propertior
                    if 'status' in data:
                        status = data['status']
                        aid.status = int(status)
                    
                    if 'mode' in data:
                        mode = data['mode']
                        aid.mode = int(mode)

                    aid.save()
                     
                    if int(aid.need_propertior) == aid.YES:
                        # 添加选择的小区
                        if 'comminities' in data:
                            comminities = json.loads(data['comminities'])
                            for communityitem in comminities: 
                                itemuuid = communityitem['uuid']
                                try:
                                    communityinstance = Community.objects.get(uuid = itemuuid)
                                    AidCommunities.objects.create(aid = aid, community = communityinstance)
                                except Community.DoesNotExist:
                                    logger.error("add aid community Community.DoesNotExist, uuid:" +str(itemuuid))
                                 
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
                                                  'aid', str(user.id)),
                                              filename)
                            AidImgs.objects.create(aid=aid,
                                                   filepath=os.path.join(
                                                       'aid', str(user.id), filename),
                                                   filename=filename)
                    if aid.status == aid.OPEN:
                        # 新建 OPEN状态，创建订单，返回订单号
                        order = create_order(aid, user, aid.community)
                        result['status'] = SUCCESS
                        result['msg'] = {
                            "order_status": aid.status,
                            "billno": order.billno,
                            "uuid": str(aid.uuid),
                            "payed":aid.payed
                        }
                    else:
                        result['status'] = SUCCESS
                        result['msg'] = {
                            "order_status": aid.status,
                            "msg": "已保存",
                            "uuid": str(aid.uuid),
                            "payed":aid.payed
                        }
                except Community.DoesNotExist:
                    result['msg'] = "请在首页选择小区"
            else:
                result['msg'] = msg
        else:
            result['msg'] = "参数错误：title, community uuid"

        return HttpResponse(json.dumps(result), content_type="application/json")

    def put(self, request):
        """
        修改
        """
        result = {}
        result['status'] = ERROR
        user = request.user

        data = request.POST

        if 'uuid' in data:
            # 微信小程序单个文件上传
            aiduuid = data['uuid']
            try:
                if 'bill' in data:
                    #  # 抢单 或者 报名，抢单成功后，给求助人发通知：短信或者APP通知
                    #
                    aid = Aid.objects.get(uuid=aiduuid)
                elif 'finish' in data:
                    # 接单人提交完成结果
                    aid = Aid.objects.get(uuid=aiduuid, answer=user) 
                elif 'score' in data:
                    # 求助人完成结果
                    aid = Aid.objects.get(uuid=aiduuid, user=user)
                else:
                    aid = Aid.objects.get(user=user, uuid=aiduuid)
                if 'enrolluuid' in data:
                    # 求助人选取接单人
                    if aid.status == aid.OPEN and aid.payed == aid.YES and aid.mode == aid.SELECTED:
                        enrolluuid =  data['enrolluuid']
                        try:
                            entry = Entries.objects.get(id = enrolluuid, aid = aid)
                            answer_extra = {} 
                            answer_extra['servicetimes'] = entry.service_times
                            answer_extra['score'] = entry.score 
                            aid.answer_extra = json.dumps(answer_extra)
                            aid.answer = entry.user
                            aid.status = aid.ACCEPTED
                            aid.accepted_date = datetime.now()
                            aid.save()
                            result['msg'] = "选取成功"
                            result['status'] = SUCCESS
                            NoticeMgr.create(
                                title = "接单成功",
                                content = "{0}已选定您接单，请尽快完成".format(aid.user.username),
                                user = entry.user,
                                appurl = "/pages/aid/detail?uuid="+str(aid.uuid),
                                entity_type=  EntityType.AID
                            )
                            # 发送短信提醒                  
                        except Entries.DoesNotExist:
                            result['msg'] = "报名信息不存在"
                            result['status'] = ERROR 
                    else:
                        result['msg'] = "选取失败"
                        result['status'] = ERROR
                elif 'bill' in data:
                    # 抢单 或者 报名，抢单成功后，给求助人发通知：短信或者APP通知
                    if aid.status == aid.OPEN and aid.payed == aid.YES:
                        if aid.mode == aid.KNOCKED:
                            # 需要公开并已支付的+抢单模式
                            if aid.user == user:
                                result['msg'] = "不能抢自己的单"
                            else:
                                # step 1 验证接单人的信用程度，信用程度低的，不能接单
                                time.sleep(2)
                                answer_extra = {}
                                history = Aid.objects.filter(answer = user, status__in =[4,5]).\
                                aggregate(Sum("score"), Count('pk'))
                                logger.debug("history: "+ str(history))
                                score = history['score__sum'] # 如果没有数据，这是None
                                count = history['pk__count']

                                answer_extra['servicetimes'] = count
                                if score is None:
                                    answer_extra['score'] = None
                                else:
                                    answer_extra['score'] =  int(score / count)
                                
                                aid.answer_extra = json.dumps(answer_extra)

                                aid.answer = user 
                                aid.status = aid.ACCEPTED
                                aid.accepted_date = datetime.now()
                                aid.save()
                                result['msg'] = "抢单成功"
                                result['status'] = SUCCESS

                                NoticeMgr.create(
                                title = "{0}已接单".format(aid.user.username),
                                content = "您的求助：{0}，{1}已接单".format(aid.title, user.username),
                                user = aid.user,
                                entity_type=  EntityType.AID,
                                appurl = "/pages/aid/detail?uuid="+str(aid.uuid)
                            )
                        else:
                            # 报名
                            allow = False
                            enroll_community_name = ""
                            crts = list(Cert.objects.filter(user = user, role__code="yezhu").\
                                    values_list("uuid", "community__uuid","community__name"))
                            if aid.need_propertior == aid.YES:
                                # 要求必须是业主，需要验证业主身份  
                                if len(crts) == 0:
                                    # 没有任何认证信息
                                    result['msg'] = "仅业主可以接单"
                                    result['status'] = 2 # 前端拿到这2后，提示分享
                                    return HttpResponse(json.dumps(result), content_type="application/json")
                                else: 
                                    aidcommunities = list(AidCommunities.objects.filter(aid = aid).\
                                        values_list("community__uuid","community__name"))
                                     
                                    for aidcommunitiy in aidcommunities:
                                        for crt in crts:
                                            if aidcommunitiy[0] == crt[1]:
                                                allow = True
                                                enroll_community_name = aidcommunitiy[1]
                                                break 
                            else:
                                allow = True
                                if len(crts) > 0:
                                    enroll_community_name = crts[0][1]
                                  
                            if not allow:
                                result['msg'] = "仅限指定小区业主接单"
                                result['status'] = 2 # 前端拿到这2后，提示分享
                                return HttpResponse(json.dumps(result), content_type="application/json")
                            # 获取历史评分以及服务次数
                            history = Aid.objects.filter(answer = user, status__in =[4,5]).\
                                aggregate(Sum("score"), Count('pk'))
                            logger.debug("history: "+ str(history))
                            score = history['score__sum'] # 如果没有数据，这是None
                            count = history['pk__count']
                            logger.debug("user:{0}, score:{1},times :{2}".format(user.username, str(score), str(count)))
                            
                            try:
                                entry = Entries.objects.get(aid=aid, user=user)
                            except Entries.DoesNotExist:
                                entry = Entries()
                                entry.user = user
                                entry.aid = aid

                            entry.service_times = count 
                            entry.communityname = enroll_community_name
                            
                            if score is None:
                                entry.score = score
                            else:
                                entry.score = int(score / count)

                            entry.save()
                             
                            result['msg'] = "报名成功"
                            result['status'] = SUCCESS

                            NoticeMgr.create(
                                title = "{0}已报名".format(aid.user.username),
                                content = "您的求助：{0}，{1}已报名，请及时查看".format(aid.title, user.username),
                                user = aid.user,
                                entity_type=  EntityType.AID,
                                appurl = "/pages/aid/detail?uuid="+str(aid.uuid)
                            )
                    else:
                        result['msg'] = "抢单失败"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                elif 'finish' in data:
                    # 接单人提交完成结果
                    if 'comment' in data:
                        comment = data['comment']
                        aid.comment = comment
                    aid.finished_date = datetime.now()
                    aid.status = aid.FINISHED
                    aid.save()
                    # 修改收入记录。
                    result['msg'] = "提交成功"
                    result['status'] = SUCCESS
                    NoticeMgr.create(
                        title = "{0}求助已完成".format(aid.title),
                        content = "您的求助：{0}，{1}已完成，请及时查看".format(aid.title, user.username),
                        user = aid.user,
                        entity_type=  EntityType.AID,
                        appurl = "/pages/aid/detail?uuid="+str(aid.uuid)
                    )
                    return HttpResponse(json.dumps(result), content_type="application/json")
                elif 'score' in data:
                    # 求助人提交评价
                    score = data['score']
                    if aid.status != aid.FINISHED:
                        result['msg'] = "求助未完成"
                    elif aid.user != user:
                        result['msg'] = "只能求助人评价"
                    else:
                        aid.score = score
                        aid.status = aid.COMMENTED
                        aid.save()
                        result['msg'] = "评价成功"
                        result['status'] = SUCCESS
                        NoticeMgr.create(
                            title = "您收到了新的评价" ,
                            content = "求助单:{0}已完成评价，请及时查看".format(aid.title),
                            user = aid.answer,
                            entity_type=  EntityType.AID,
                            appurl = "/pages/aid/detail?uuid="+str(aid.uuid)
                        )
                    return HttpResponse(json.dumps(result), content_type="application/json")

                status, msg = verify_data(data)
                if status == ERROR:
                    result['msg'] = msg
                    return HttpResponse(json.dumps(result), content_type="application/json")
                if 'title' in data:
                    title = data['title']
                    aid.title = title

                if 'content' in data:
                    content = data['content']
                    aid.content = content

                if 'money' in data:
                    money = data['money']
                    if aid.payed == aid.NO:
                        # 只有未支付的订单可以修改佣金
                        aid.money = money

                if 'need_propertior' in data:
                    need_propertior = data['need_propertior']
                    aid.need_propertior = need_propertior

                if 'secretinfo' in data:
                    secretinfo = data['secretinfo']
                    aid.secretinfo = secretinfo

                if 'end_date' in data:
                    end_date = data['end_date']
                    end_date = end_date.replace("-", "/")
                    end_date = datetime.strptime(end_date, DATEFORMAT)
                    aid.end_date = end_date

                if 'publich_myinfo' in data:
                    publich_myinfo = data['publich_myinfo']
                    aid.publich_myinfo = publich_myinfo

                if 'status' in data:
                    status = int(data['status'])
                    aid.status = status
                if 'mode' in data:
                    mode = data['mode']
                    aid.mode = int(mode)
                    
                aid.save()
                if int(aid.need_propertior) == aid.YES:
                    # 添加选择的小区
                    if 'comminities' in data: 
                        comminities = json.loads(data['comminities'])
                        # 删除原来的
                        AidCommunities.objects.filter(aid = aid).delete()
                        for communityitem in comminities: 
                            itemuuid = communityitem['uuid']
                            try:
                                communityinstance = Community.objects.get(uuid = itemuuid)
                                AidCommunities.objects.create(aid = aid, community = communityinstance)
                            except Community.DoesNotExist:
                                logger.error("add aid community Community.DoesNotExist, uuid:" +str(itemuuid))
                else:
                    AidCommunities.objects.filter(aid = aid).delete()

                if 'deletedImagesIds' in data:
                    # 删除图片
                    deletedImagesIds = json.loads(data['deletedImagesIds'])
                    AidImgs.objects.filter(aid=aid,
                                           aid__user=user,
                                           id__in=deletedImagesIds).delete()  # 删除图片文件
                if len(request.FILES):
                    imgtype = AidImgs.FROMAID
                    if 'finish' in data:
                        #  接单人提交的完成图片
                        imgtype = AidImgs.FROMCOMMENT
                    for image in request.FILES:
                        # 获取附件对象
                        imagefile = request.FILES[image]
                        pre = datetime.now().strftime("%Y%m%d%H%M%S%f")
                        file_name, file_extension = os.path.splitext(
                            imagefile.name)
                        filename = pre+file_extension
                        FileUpload.upload(imagefile,
                                          os.path.join('aid', str(user.id)),
                                          filename)
                        AidImgs.objects.create(aid=aid,
                                               imgtype=imgtype,
                                               filepath=os.path.join(
                                                   'aid', str(user.id), filename),
                                               filename=filename)

                if aid.status == aid.OPEN and aid.payed == aid.NO:
                    # 新建 OPEN状态，创建订单，返回订单号
                    order = create_order(aid, user, aid.community)
                    result['msg'] = {
                        "order_status": aid.status,
                        "payed": aid.payed,
                        "billno": order.billno,
                        "uuid": str(aid.uuid)
                    }
                else:
                    result['msg'] = {
                        "order_status": aid.status,
                        "msg": "已保存",
                        "payed": aid.payed,
                        "uuid": str(aid.uuid)
                    }
                result['status'] = SUCCESS

            except Aid.DoesNotExist:
                result['msg'] = "未找到求助信息"
        else:
            result['msg'] = "ids参数为必需参数"
        return HttpResponse(json.dumps(result), content_type="application/json")

    def delete(self, request):
        """
        删除: 仅仅可以删除未支付的订单
        """
        result = {}
        if 'uuids' in request.POST:
            user = request.user
            aidsuuids = request.POST['uuids']
            aidsuuids = aidsuuids.split(",")
            AidImgs.objects.filter(aid__uuid__in=aidsuuids,
                                   aid__user=user,
                                   aid__payed=Aid.NO).delete()  # 删除图片文件
            AidOrders.objects.filter(
                aid__uuid__in=aidsuuids, status=AidOrders.NON_PAYMENT).delete()
            Aid.objects.filter(uuid__in=aidsuuids,
                               user=user,
                               payed=Aid.NO).delete()
            result['status'] = SUCCESS
            result['msg'] = "已删除"
        else:
            result['status'] = ERROR
            result['msg'] = "请发送ids参数"

        return HttpResponse(json.dumps(result), content_type="application/json")
