from django.conf.urls import include, url
from django.contrib import admin 
from appuser import views_api   
from appuser import views_ui
from appuser.views_api import UserView, UserRoleView,PhoneCodeView
from appuser.views_batch import UserBatchView
from django.views.decorators.csrf import csrf_exempt
from appuser.views_wx import WeixinView
from appuser.views_community import UserCommunityView
from appuser.views_ui import UserPortrait
from appuser.views_contact import UserContactView


app_name = "appuser"
urlpatterns = [
    #url(r'^$', views.index, name='index'),
    url(r'^usernames/(?P<username>\w{1,1024})$', views_api.usernames, name='usernames'),
    url(r'^emails/(?P<email>[\w.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4})$', views_api.email, name='email'),
    url(r'^emailscode/(?P<email>[\w.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4})$', views_api.emailscode, name='emailscode'),
    url(r'^emailscode/(?P<email>[\w.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4})/(?P<code>[A-Z0-9a-z]{3,5})$', views_api.verify, name='verify'),
    url(r'^portrait/$', views_api.portrait, name='portrait'),
    url(r'^newgroup/$', views_api.newgroup, name='newgroup'),
    url(r'^grouplist/$', views_api.grouplist, name='grouplist'),
    url(r'^(?P<groupid>\d+)/modify_group/$', views_api.modify_group, name='modify_group'),
    #url(r'^modify_user/$', views_api.modify_user, name='modify_user'),
    url(r'^(?P<userid>\d+)/modify_user/$', views_api.modify_user, name='modify_user'),
    url(r'^(?P<userid>\d+)/(?P<super>\d{1})/admin/$', views_api.admin, name='admin'),
    url(r'^(?P<userid>\d+)/(?P<staff>\d{1})/staff/$', views_api.staff, name='staff'),
    url(r'^list_users/$', views_api.list_users, name='list_users'),
    url(r'^admin_list_users/$', views_api.admin_list_users, name='admin_list_users'),
    url(r'^upload_fake_portrait/$', views_api.upload_fake_portrait, name='upload_fake_portrait'), 

    url(r'^phonecode/', csrf_exempt(PhoneCodeView.as_view()), name='phonecode'),
     
    url(r'^alter_usertype/(?P<phone>[0-9.-]{3,11})/(?P<usertype>[0-9])$', views_api.alter_usertype, name='alter_usertype'),

    url(r'^oauth2/authorize/$', views_api.authorize, name='authorize'), 
    url(r'^login/$', views_ui.login, name='login'),  
    url(r'^logout/$', views_ui.logout, name='logout'),  
    url(r'^register/$', views_ui.register, name='register'),  
    url(r'^find_password/$', views_ui.find_password, name='find_password'), 
    #url(r'^save_portrait/$', views.save_portrait, name='save_portrait'),#save portrait
    url(r'^org_user_list/$', csrf_exempt(UserView.as_view()), name='org_user_list'),

    # 用户角色
    url(r'^role/$', csrf_exempt(UserRoleView.as_view()), name='role'),  

    # 用户列表
    url(r'^list/$',csrf_exempt(UserView.as_view()), name='list'), 
    # 物业管理
    url(r'^community/$',csrf_exempt(UserCommunityView.as_view()), name='community'), 
    #用户批量添加
    url(r'^batch/$',csrf_exempt(UserBatchView.as_view()), name='batch'),
    url(r'^wx/$',csrf_exempt(WeixinView.as_view()), name='Weixin'),
    url(r'^contact/$',csrf_exempt(UserContactView.as_view()), name='contact'), 
    # 单独修改用户头像或背景图
    url(r'^portrait_backimage/$',csrf_exempt(UserPortrait.as_view()), name='userportrait'),
]
