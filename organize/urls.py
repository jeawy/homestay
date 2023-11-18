from django.conf.urls import  url 
from organize.views import OrganizeView
from django.views.decorators.csrf import csrf_exempt

app_name = "organize"
urlpatterns = [  
    url(r'^organize/$', csrf_exempt(OrganizeView.as_view()), name='organize'), 
]
