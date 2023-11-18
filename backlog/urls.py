#! -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
 
from backlog.views import BacklogView 
app_name = "backlog"
urlpatterns = [
    # 管理
    url(r'^backlogs/$', csrf_exempt(BacklogView.as_view()), name='backlog'), 
]
