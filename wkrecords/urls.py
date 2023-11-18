from django.conf.urls import url 
from wkrecords.views import propertyView
from wkrecords.view_approve import WkApproveView
from django.views.decorators.csrf import csrf_exempt

app_name = "wkrecords"
urlpatterns = [  
    url(r'^record/$', csrf_exempt(propertyView.as_view()), name='record'),
    url(r'^approve/$', csrf_exempt(WkApproveView.as_view()), name='approve'),
]
