from django.conf.urls import url 
from coupon.views_buyers import CouponBuyerView, CoupinAnonynousView
from coupon.views_admin import CouponAdminView 
from django.views.decorators.csrf import csrf_exempt 
app_name = "coupon"

urlpatterns = [  
    url(r'^admin/$', csrf_exempt(CouponAdminView.as_view()), name='admin'),
    url(r'^buyers/$', csrf_exempt(CouponBuyerView.as_view()), name='buyers'),
    url(r'^anonynous/$', csrf_exempt(CoupinAnonynousView.as_view()), name='anonynous'), 
]
