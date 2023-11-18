from django.conf.urls import url  
from paidservice.views import PaidServiceView, PaidServiceAnonymousView
from django.views.decorators.csrf import csrf_exempt 
from paidservice.views_order import PaidOrderView

app_name = "paidservice"
urlpatterns = [  
    url(r'^paidservice/$', csrf_exempt(PaidServiceView.as_view()), name='paidservice'), 
    url(r'^anonymous/$', csrf_exempt(PaidServiceAnonymousView.as_view()), name='anonymous'), 
    url(r'^order/$', csrf_exempt(PaidOrderView.as_view()), name='order'), 
]
