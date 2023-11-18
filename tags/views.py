import json
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.views import APIView
from django.views import View
from tags.models import Tags
from property.code import SUCCESS, ERROR
from tags.comm import add

class TagsView(View):
    def get(self, request):
        tags = Tags.objects.filter()
        content = {}
        tags_ls = [(tag.name, tag.label) for tag in tags]
        add("特惠", "tehui")
        content['status'] = SUCCESS
        content['msg'] = tags_ls
        return HttpResponse(json.dumps(content), content_type="application/json")
