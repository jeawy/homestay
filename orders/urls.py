from django.conf.urls import url  
from record.views import RecordView, RecordAnonymousView
from django.views.decorators.csrf import csrf_exempt
from record.views_userinfo import  RecordUserInfoView, RecordUserInfoAnonymousView
app_name = "record"
urlpatterns = [  
    url(r'^record/$', csrf_exempt(RecordView.as_view()), name='record'), 
    url(r'^anonymous/$', csrf_exempt(RecordAnonymousView.as_view()), name='anonymous'),

    url(r'^userinfo/$', csrf_exempt(RecordUserInfoView.as_view()), name='userinfo'),
    url(r'^userinfo/anonymous/$', csrf_exempt(RecordUserInfoAnonymousView.as_view()), name='userinfoanonymous'),
]
