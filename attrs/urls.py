from django.conf.urls import url 
from django.views.decorators.csrf import csrf_exempt

from attrs.views import AttrsView, AttrsBindView, AttrsInstancesView, TestView

app_name = "attrs"
urlpatterns = [  
    url(r'^attrs/$', csrf_exempt(AttrsView.as_view()), name='attrs'),
    url(r'^bind/$', csrf_exempt(AttrsBindView.as_view()), name='bind'),
    url(r'^instance/$', csrf_exempt(AttrsInstancesView.as_view()), name='instance'),
    url(r'^test/$', csrf_exempt(TestView.as_view()), name='test'),
]
