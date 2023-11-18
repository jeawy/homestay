from django.conf.urls import url 
from notice.views import NoticeView, NoticeAnonymousView
from django.views.decorators.csrf import csrf_exempt
app_name = "notice"
urlpatterns = [  
    url(r'^notice/$', csrf_exempt(NoticeView.as_view()), name='notice'),
    url(r'^anonymous/$', csrf_exempt(NoticeView.as_view()), name='notice'),
]
