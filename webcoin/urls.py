#! -*- coding:utf-8 -*-
from django.conf.urls import url 
from django.views.decorators.csrf import csrf_exempt
 
from webcoin.invite_views import InviteCodeView 
from webcoin.views import WebCoinView

app_name = "webcoin"
urlpatterns = [  
    url(r'^webcoin/$', csrf_exempt(WebCoinView.as_view()), name='webcoin'),
    url(r'^invite/$', csrf_exempt(InviteCodeView.as_view()), name='invite'), 
]