#! -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
 
from appshare.views import ShareView 
app_name = "appshare"
urlpatterns = [
    # 管理
    url(r'^appshare/$', csrf_exempt(ShareView.as_view()), name='appshare'), 
]
