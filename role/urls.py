from django.conf.urls import url 
from role.views import RoleView, PermsView, RoleInitView
from django.views.decorators.csrf import csrf_exempt
from role.views_crt import RoleCrtView
app_name = "role"
urlpatterns = [
    url(r'^role/$', csrf_exempt(RoleView.as_view()), name='role'),
    url(r'^init/$', csrf_exempt(RoleInitView.as_view()), name='initrole'),
    url(r'^crt/$', csrf_exempt(RoleCrtView.as_view()), name='crt'),
    url(r'^permissions/$', csrf_exempt(PermsView.as_view()), name='permissions'),
]
