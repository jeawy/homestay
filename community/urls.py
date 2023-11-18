from django.conf.urls import  url 
from community.views import CommunityView, CommunityAnonymousView
from community.views_info import CommunityInfoView
from community.views_proprietor import CommunityProprietorView
from community.views_statistics import CommunityStatView
from django.views.decorators.csrf import csrf_exempt

app_name = "community"
urlpatterns = [  
    url(r'^community/$', csrf_exempt(CommunityView.as_view()), name='community'),
    url(r'^info/$', csrf_exempt(CommunityInfoView.as_view()), name='info'),
    url(r'^anonymous/$', csrf_exempt(CommunityAnonymousView.as_view()), name='anonymous'),
    url(r'^proprietor/$', csrf_exempt(CommunityProprietorView.as_view()), name='proprietor'),
    url(r'^stat/$', csrf_exempt(CommunityStatView.as_view()), name='stat'),
]
