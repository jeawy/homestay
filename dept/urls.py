from django.conf.urls import url 
from dept.views import DeptView,DeptUserView
from django.views.decorators.csrf import csrf_exempt

app_name = "dept"
urlpatterns = [  
    url(r'^dept/$', csrf_exempt(DeptView.as_view()), name='dept'),
    url(r'^dept_user/$', csrf_exempt(DeptUserView.as_view()), name='dept_user'),
]
