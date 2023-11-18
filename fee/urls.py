from django.conf.urls import url 
from django.views.decorators.csrf import csrf_exempt 
from fee.views_fixed import FixedFeeView 
from fee.views_dynamic import DynamicFeeView

app_name = "fee"
urlpatterns = [  
    url(r'^fixed/$', csrf_exempt(FixedFeeView.as_view()), name='fixed'),
    url(r'^dynamic/$', csrf_exempt(DynamicFeeView.as_view()), name='dynamic') 
]
