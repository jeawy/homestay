from django.conf.urls import url 
from django.views.decorators.csrf import csrf_exempt
from menu.views import ConfigMenuView 

app_name = "menu"
urlpatterns = [ 
    url(r'^menu/$', csrf_exempt(ConfigMenuView.as_view()), name='menu'),
]