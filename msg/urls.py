from django.conf.urls import url 
from django.views.decorators.csrf import csrf_exempt
from msg.views import MsgRecordView, MsgAnonymousRecordView
from msg.views_msg import MsgProductView
from msg.views_msg_order import MsgOrderView
from msg.views_msg_record import OrganizeRecordView
app_name = "msg"
urlpatterns = [   
    url(r'^anonymous/$', csrf_exempt(MsgAnonymousRecordView.as_view()), name='msg'),
    url(r'^msg/$', csrf_exempt(MsgRecordView.as_view()), name='msg'),
    url(r'^product/$', csrf_exempt(MsgProductView.as_view()), name='product'),
    url(r'^order/$', csrf_exempt(MsgOrderView.as_view()), name='order'),
    url(r'^record/$', csrf_exempt(OrganizeRecordView.as_view()), name='record'),
]
