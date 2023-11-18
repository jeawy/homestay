from django.conf.urls import url 
from area.views import AreaView
from django.views.decorators.csrf import csrf_exempt

app_name = "area"
urlpatterns = [  
    url(r'^area/$', csrf_exempt(AreaView.as_view()), name='area'),
]
