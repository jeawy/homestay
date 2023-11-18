#! -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
 
from card.views import CardView 
from card.views_admin import CardAdminView
app_name = "card"
urlpatterns = [  
    url(r'^admin/$', csrf_exempt(CardAdminView.as_view()), name='admin'), 
    url(r'^card/$', csrf_exempt(CardView.as_view()), name='card'), 
]