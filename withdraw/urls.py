#! -*- coding:utf-8 -*-
from django.conf.urls import url 
from django.views.decorators.csrf import csrf_exempt 
from withdraw.views import WithDrawView

app_name = "withdraw"
urlpatterns = [  
    url(r'^withdraw/$', csrf_exempt(WithDrawView.as_view()), name='withdraw'), 
]