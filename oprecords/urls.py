from django.conf.urls import include, url

from django.views.decorators.csrf import csrf_exempt

from oprecords.views import TestView, opRecordsView

app_name = "oprecords"
urlpatterns = [
    url(r'^oprecords/$', csrf_exempt(opRecordsView.as_view()), name='oprecords'),
    url(r'^test/$', csrf_exempt(TestView.as_view()), name='test'),
]
