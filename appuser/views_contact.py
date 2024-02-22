# -*- coding: utf-8 -*-  
from django.http import HttpResponse    
from appuser.models import MyContaces  
import json 
from rest_framework.views import APIView   
from property.code import *
 
class UserContactView(APIView):
 
    def get(self, request): 
        user = request.user
        kwargs = {
            "user" : user
        } 
        
        users = MyContaces.objects.filter(**kwargs).values(
            "id", "username", "number"
        )  
        
        result = {
            "status":SUCCESS,
            "msg" :  list(users)
        }
        return HttpResponse(json.dumps(result), content_type='application/json')
 
    def post(self, request):
        """
        新建常用用户
        """
        content = {
            'status': ERROR
        }
        user = request.user

        data = request.POST

        if 'method' in data:
            method = data['method'].lower().strip() 
            if method == 'delete':  # 删除
                return self.delete(request)

         
        if 'username' in data and 'number' in data:
            # 创建用户
            contact = MyContaces()
            username = data['username'].strip()
            number = data['number'].strip()
            
            if username == '' or number == '':
                content['msg'] = '请输入名字和身份证号码'
                return HttpResponse(json.dumps(content), content_type="application/json")
            
            contact.user  = user 
            contact.number  = number 
            contact.username  = username    
            contact.save()
            
            content['status'] = SUCCESS
            content['msg'] = '添加成功'
            return HttpResponse(json.dumps(content), content_type="application/json")
        else:
            # 支持批量创建
            content['status'] = ERROR
            content['msg'] = '参数错误'
        return HttpResponse(json.dumps(content), content_type="application/json")

     
    def delete(self, request):
        """
        用户删除
        """
        content = {
            'status': ERROR,
            'msg': ''
        }
        # 处理前端发送数据 
        data = request.POST

        user = request.user
         
        if 'ids' in data:
            userids = data['ids'].split(",")
            MyContaces.objects.filter(user=user, id__in=userids).delete()
            
            content['status'] = SUCCESS
            content['msg'] = '删除成功'
            return HttpResponse(json.dumps(content), content_type="application/json")
        else:
            content['msg'] = '缺少ids参数'
            return HttpResponse(json.dumps(content), content_type="application/json")
        