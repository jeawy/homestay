from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from worktime.views import  HolidaysView

app_name = "worktime"
urlpatterns = [
    url(r'^holidays/$', csrf_exempt(HolidaysView.as_view()), name='holidays'),
]
