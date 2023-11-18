from django.conf.urls import include, url
from appfile.views import AppfileView
from django.views.decorators.csrf import csrf_exempt

app_name = "appfile"
urlpatterns = [  
    url(r'^appfile/$', csrf_exempt(AppfileView.as_view()), name='appfile'),
]
