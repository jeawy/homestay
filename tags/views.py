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
        if 'label' in request.GET:
            label = request.GET['label']
            tags = Tags.objects.filter(label = label).values("id", "name", "label")
           
            content = {}
            content['status'] = SUCCESS
            content['msg'] = list(tags)
            return HttpResponse(json.dumps(content), content_type="application/json")
