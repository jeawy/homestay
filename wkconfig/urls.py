from django.conf.urls import url 
from django.views.decorators.csrf import csrf_exempt
from wkconfig.views import SysConfigView, ExtranetBindView

app_name = "wkconfig"
urlpatterns = [
    url(r'^sysconfig/$', csrf_exempt(SysConfigView.as_view()), name='sysconfig'),
    url(r'^bind/$', csrf_exempt(ExtranetBindView.as_view()), name='bind'),
]