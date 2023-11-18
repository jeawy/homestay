import time
from datetime import datetime
from common.logutils import getLogger
import os
import pdb  
import uuid
from django.db.models import Sum
from community.models import Community
from rest_framework.views import APIView
from django.http import HttpResponse 
from withdraw.models import WithDraw, WithdrawImgs
from django.views import View 
import json 
from django.conf import settings
from common.fileupload import FileUpload
from incomes.comm import statisticsMoney, statisticsMoneyOrg
from community.comm import getUserCommunities
from community.comm_statistics import community_statatics
from withdraw.comm import has_submit_withdraw, single_withdraw
from property.code import ERROR, SUCCESS  
from notice.comm import NoticeMgr
from property.entity import EntityType
from organize.models import Organize
logger = getLogger(True, 'like', False)
 
 
class WithDrawView(APIView): 
    def get(self, request):
        """
        查询
        """
        # 
        content = {
            'status':ERROR
        }  
        workday = 1 # 一个工作日内到账
        kwargs = {}
        user = request.user
        page = 0
        pagenum = settings.PAGE_NUM 
        if "page" in request.GET and "pagenum" in request.GET:
            pagenum = request.GET['pagenum']
            page = request.GET['page']
            try:
                page = int(page) - 1
                pagenum = int(pagenum)
            except ValueError:
                pass 
        if 'communityuuids' in request.GET:
            # 物业pc端首页获取总览     
            communityuuids = getUserCommunities(user)
            kwargs['community__uuid__in'] = list(communityuuids)
        elif 'communityuuid' in request.GET:
            # 小区物业提现
            communityuuid = request.GET['communityuuid']
            communityuuids = getUserCommunities(user)
            if communityuuid not in list(communityuuids):
                content['msg'] = "您无权查看"
                return HttpResponse(json.dumps(content), content_type="application/json")
            else:
                kwargs['community__uuid'] = communityuuid
                if 'sum' in request.GET:
                    # 统计正在提现和已提现金额
                    status0_meney = WithDraw.objects.filter(**kwargs, status=0).aggregate(Sum('money'))['money__sum']
                    status2_meney = WithDraw.objects.filter(**kwargs, status=1).aggregate(Sum('money'))['money__sum']
                    content['status'] = SUCCESS
                    content['msg'] ={
                        "status0_meney":status0_meney,
                        "status2_meney" : status2_meney, 
                    } 
                    return HttpResponse(json.dumps(content), content_type="application/json")
        else:
            # 非平台管理用户，获取自己的提现单
            kwargs['user'] = user    
            kwargs['community__isnull'] = True
        if 'username' in request.GET:
            username = request.GET['username']
            kwargs['user__username__icontains'] = username

        if 'status' in request.GET:
            status = request.GET['status']
            kwargs['status'] = status

        if 'phone' in request.GET:
            phone = request.GET['phone']
            kwargs['user__phone__icontains'] = phone

        total = WithDraw.objects.filter(**kwargs).count()
        withdraws = WithDraw.objects.filter(**kwargs)[page*pagenum: (page+1)*pagenum] 
        withdraw_ls = []
        for withdraw in withdraws:
            withdraw_ls.append(single_withdraw(withdraw))
        content['status'] = SUCCESS
        content['msg'] ={
            "list":withdraw_ls,
            "workday" : workday,
            "minmoney": settings.MINMONEY,
            "total":total
        } 
        return HttpResponse(json.dumps(content), content_type="application/json")

    def post(self, request):
        """
        提交取现申请
        """
        result = {
            "status" :ERROR
        }
        if 'method' in request.POST:
            method = request.POST['method'].lower()
            if method == 'put':  # 支付
                return self.put(request)
            if method == 'delete':  # 删除
                return self.delete(request) 

        user = request.user
        withdraw = WithDraw()  
        withdraw.uuid = uuid.uuid4()
        if 'communityuuid' in request.POST:
            # 小区物业提现
            communityuuid = request.POST['communityuuid']
            communityuuids = getUserCommunities(user)
            if communityuuid not in list(communityuuids):
                # 无权限
                result['msg'] = "无权在本小区申请提现"
                return HttpResponse(json.dumps(result), content_type="application/json")
            try:
                community = Community.objects.get(uuid = communityuuid)
                if has_submit_withdraw(community = community) :
                    result['msg'] = "每月只能申请一次提现"
                    return HttpResponse(json.dumps(result), content_type="application/json")
                community_statatics(community=community) # 重新统计
                if community.money_left < settings.MINMONEY:
                    result['msg'] = "余额不足{0}元，无法提现".format(str(settings.MINMONEY))
                    return HttpResponse(json.dumps(result), content_type="application/json")
                
                withdraw.money = community.money_left
                withdraw.community = community
                withdraw.user = user
                withdraw.save() 
                # 申请提现之后，再次统计
                community_statatics(community=community) # 重新统计
                content =  community.name+"发起了提现申请，请尽快处理"
            except Community.DoesNotExist:
                result['msg'] = "小区不存在"
                return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            withdraw.user = user
            # 普通业主申请提现
            if has_submit_withdraw(user = user) :
                result['msg'] = "每月只能申请一次提现"
                return HttpResponse(json.dumps(result), content_type="application/json")

            income_total,expend_total,left = statisticsMoney(user)
            if left < settings.MINMONEY:
                result['msg'] = "余额不足{0}元，无法提现".format(str(settings.MINMONEY))
                return HttpResponse(json.dumps(result), content_type="application/json")
            content =  user.username+"发起了提现申请，请尽快处理" 
            withdraw.money = left
            withdraw.save() 
        result['status'] = SUCCESS
        result['msg'] = '申请已提交'
        # 发通知给平台
        title = "新提现申请"
        
        pcurl = "/withdraw/list"
        NoticeMgr.create(title =title,content = content,platform=1, pcurl=pcurl)
        return HttpResponse(json.dumps(result), content_type="application/json")

    def put(self, request):
        # 平台管理人员进行支付
        user = request.user
        if not user.has_perms("withdraw.withdraw.platform_manage_withdraw"):
            return HttpResponse('Unauthorized', status=401)
        content = {
            "status":ERROR
        }
        if 'uuid' in request.POST:
            withdrawuuid = request.POST['uuid']
            withdraw = WithDraw.objects.get(uuid = withdrawuuid)

            if len(request.FILES) : 
                # 上传支付凭证
                for image in request.FILES:
                    # 获取附件对象 
                    imagefile = request.FILES[image]
                    pre = datetime.now().strftime("%Y%m%d%H%M%S%f")
                    file_name, file_extension = os.path.splitext(imagefile.name)
                    filename = pre+file_extension
                    FileUpload.upload(imagefile, 
                                os.path.join('withdraw', str(user.id)), 
                                filename )
                    WithdrawImgs.objects.create(withdraw=withdraw,
                    filepath= os.path.join('withdraw', str( user.id), filename) ,
                                    filename=filename)
            if 'status' in request.POST:
                status = request.POST['status'] 
                withdraw.status = status
            
            if 'remark' in request.POST:
                remark = request.POST['remark'] 
                withdraw.remark = remark

            withdraw.save() 
            content['status'] = SUCCESS
            content['msg'] = "提现单已更新"
        else:
            content['msg'] = "缺少uuid"
        return HttpResponse(json.dumps(content), content_type="application/json")
    
    def delete(self, request):
        # 删除
        user = request.user 
        content = {
            "status":ERROR
        }
        if 'uuid' in request.POST:
            withdrawuuid = request.POST['uuid']
            try: 
                if 'communityuuid' in request.POST:
                    # 物业删除
                    communityuuid = request.POST['communityuuid']
                    try:
                        community = Community.objects.get(uuid = communityuuid)
                        communityuuids = getUserCommunities(user)
                        if communityuuid in list(communityuuids)  :  
                            withdraw = WithDraw.objects.get(uuid = withdrawuuid,
                                    community__uuid = communityuuid) 
                            if withdraw.status == withdraw.PAYED:
                                # 已支付不能删除
                                content['msg'] = "已支付不能删除" 
                            else:
                                withdraw.delete()
                                community_statatics(community=community) # 重新统计
                                content['msg'] = "已删除"
                                content['status'] = SUCCESS
                        else:
                            # 无权限
                            content['msg'] = "无权在本小区申请提现" 
                            return HttpResponse(json.dumps(content), content_type="application/json")
                    except Community.DoesNotExist:
                        content['msg'] = "小区不存在" 
                        return HttpResponse(json.dumps(content), content_type="application/json") 
                else:
                    # 业主申请
                    withdraw = WithDraw.objects.get(uuid = withdrawuuid, user = user) 
                    if withdraw.status == withdraw.PAYED:
                        # 已支付不能删除
                        content['msg'] = "已支付不能删除" 
                    else:
                        withdraw.delete()
                        content['msg'] = "已删除"
                        content['status'] = SUCCESS
                return HttpResponse(json.dumps(content), content_type="application/json")
            except WithDraw.DoesNotExist:  
                content['msg'] = "申请不存在"
        else:
            content['msg'] = "缺少uuid"
        return HttpResponse(json.dumps(content), content_type="application/json")
 

        


