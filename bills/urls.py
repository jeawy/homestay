#! -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
 
from bills.views import OrderView, OrderConsumerView, CancelOrderView
from bills.views_card import CardView
from bills.views_admin import BillAdminView

app_name = "bills"
urlpatterns = [ 
    url(r'^bills/$', csrf_exempt(OrderView.as_view()), name='bills'),
    url(r'^card/$', csrf_exempt(CardView.as_view()), name='card'),
    url(r'^admin/$', csrf_exempt(BillAdminView.as_view()), name='admin'),
    url(r'^cancel/$', csrf_exempt(CancelOrderView.as_view()), name='cancel'),
    url(r'^anonymous/$', csrf_exempt(OrderConsumerView.as_view()), name='anonymous'),
]