#! -*- coding:utf-8 -*-
import json
import pdb

from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from django.http import HttpResponse
from decorators.login import login_check
from common.logutils import getLogger
from property.code import *
from webcoin.comm import activation_code, get_id, add_webcoin
from webcoin.models import InviteCode, WebCoin

logger = getLogger(True, 'invite', False)

class InviteCodeView(APIView): 
    def get(self, request):
        """
        返回邀请码
        """
        result = {}
        user = request.user
       
        return HttpResponse(json.dumps(result), content_type="application/json")
 
    def post(self, request):
        """
        生成邀请码
        """
        result = {}
        user = request.user

        if len(request.POST) == 0:
            data = request.data
        else:
            data = request.POST

        if 'method' in request.POST:
            method = request.POST['method'].lower()
            if method == 'put':
                return self.put(request)
            elif method == 'delete':
                return self.delete(request)
        invite_code = InviteCode()
        code = activation_code(user.id)
        invite_code.code = code
        invite_code.user = user
        invite_code.save()
        result['status'] = SUCCESS
        result['code'] = code
        result['msg'] = '邀请码生成成功'

        return HttpResponse(json.dumps(result), content_type="application/json")
