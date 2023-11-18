from django.conf.urls import url 
from aid.views import AidView, AnonymousAidView
from aid.views_order import AidOrderView
from django.views.decorators.csrf import csrf_exempt
app_name = "aid"
urlpatterns = [  
    url(r'^aid/$', csrf_exempt(AidView.as_view()), name='aid'), 
    url(r'^anonymous/$', csrf_exempt(AnonymousAidView.as_view()), name='anonymous'), 
    url(r'^order/$', csrf_exempt(AidOrderView.as_view()), name='order'), 
]
