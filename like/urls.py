from django.conf.urls import   url 
from django.views.decorators.csrf import csrf_exempt 
from like.views import LikeView, LikeAnonymousView, CountAnonymousView

app_name = "like"
urlpatterns = [
    url(r'^like/$', csrf_exempt(LikeView.as_view()), name='like'),
    url(r'^anonymous/$', csrf_exempt(LikeAnonymousView.as_view()), name='anonymous'), 
    url(r'^count/$', csrf_exempt(CountAnonymousView.as_view()), name='count'), 
]
