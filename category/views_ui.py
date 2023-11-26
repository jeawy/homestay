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
        categories = list(Category.objects.filter(level=1, visible =1).values(
            "name", "icon", "id", "categorytype"
        ))
        content['msg'] = categories
        content['status'] = SUCCESS
        return HttpResponse(json.dumps(content), content_type="application/json")
  