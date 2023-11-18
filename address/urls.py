#! -*- coding:utf-8 -*-
from django.conf.urls import url 
from django.views.decorators.csrf import csrf_exempt

from .views  import AddressView

app_name = "address"
urlpatterns = [  
    url(r'^address/$', csrf_exempt(AddressView.as_view()), name='address')
]
