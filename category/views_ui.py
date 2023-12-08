#! -*- coding:utf-8 -*-
import json
import pdb
from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from category.models import Category
from django.http import QueryDict
from property.code import *


class CategoryView(View):

    def get(self, request):
        content = {}
        
        kwargs = {
            "level":1,
            "visible" : 1
        }
        if 'categorytype' in request.GET:
            categorytype = request.GET['categorytype']
            kwargs['categorytype'] = categorytype


        if 'categoryid' in request.GET:
            categoryid = request.GET['categoryid']
            categories = list(Category.objects.filter(parent__id= categoryid, visible =1).values(
                "name", "icon", "id", "categorytype", "sort"
            ))
        else: 
            categories = list(Category.objects.filter(**kwargs).values(
                "name", "icon", "id", "categorytype", "sort"
            ))
        content['msg'] = categories
        content['status'] = SUCCESS
        return HttpResponse(json.dumps(content), content_type="application/json")
  