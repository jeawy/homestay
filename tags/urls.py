#! -*- coding: utf-8 -*-
from django.conf.urls import url 
from tags.views import TagsView 
app_name = "tags"
urlpatterns = [
    
    url(r'^tags/$', TagsView.as_view(), name='tags'),
]