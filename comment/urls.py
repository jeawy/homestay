from django.conf.urls import url 
from django.views.decorators.csrf import csrf_exempt

from comment.views import CommentView, CommentAnonymousView

app_name = "comment"
urlpatterns = [
    url(r'^comment/$', csrf_exempt(CommentView.as_view()), name='comment'),
    url(r'^anonymous/$', csrf_exempt(CommentAnonymousView.as_view()), name='anonymous'),
]
