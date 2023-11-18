from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from wx.views import  WxMsgView

app_name = "wx"
urlpatterns = [
    url(r'^msg/$', csrf_exempt(WxMsgView.as_view()), name='msg'),
]
