from django.conf.urls import url 
from django.views.decorators.csrf import csrf_exempt
from statistic.views import  StatisticView, StatisticAnonymousView

app_name = "statistic"
urlpatterns = [  
    url(r'^stat/$', csrf_exempt(StatisticView.as_view()), name='stat'),
    url(r'^anonymous/$', csrf_exempt(StatisticAnonymousView.as_view()), name='anonymous'),
]
