from django.conf.urls import url 
from pay import views
from pay.views_alipay import PayAlipayView
from pay.views import PayView
from pay.views_wxpay import PayWxView
from django.views.decorators.csrf import csrf_exempt


app_name="pay"
urlpatterns = [     
    url(r'^weixin/', csrf_exempt(PayWxView.as_view()), name='weixin'),    
    url(r'^alipay/', PayAlipayView.as_view(), name='alipay'),  
    url(r'^pay/', PayView.as_view(), name='pay'),     
]
