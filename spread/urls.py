from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from spread.views import SpreadView ,SpreadAuthView
app_name = "spread"
urlpatterns = [ 
    url(r'^spread/$', csrf_exempt(SpreadView.as_view()), name='spreadtat'),
    url(r'^auth/$', csrf_exempt(SpreadAuthView.as_view()), name='spreadauth'), 
]
