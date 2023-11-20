#! -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
 
from content.views import   CategoryView, ProductView,  ProductAnonymousView 
app_name = "product"
urlpatterns = [
    # 管理
    url(r'^products/$', csrf_exempt(ProductView.as_view()), name='product'),
    url(r'^anonymous/$', csrf_exempt(ProductAnonymousView.as_view()), name='anonymous'),
    
 
    # 分类管理
    url(r'^category/$', csrf_exempt(CategoryView.as_view()), name='category'), 
]
