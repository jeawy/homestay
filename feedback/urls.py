from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from feedback.views import FeedbackView, FeedbackEmail
from django.views.decorators.csrf import csrf_exempt
app_name = "feedback"
urlpatterns = [  
    url(r'^feedback/$', csrf_exempt(FeedbackView.as_view()), name='feedback'),
    url(r'^email/$', csrf_exempt(FeedbackEmail.as_view()), name='email'),
]
