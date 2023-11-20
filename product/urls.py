#! -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from product.bill_view import BillView
from product.views import CategoryView, GiftView, SpecificationsView, GiftAnonymousView 
from product.purchase_way_views import PurchaseWayView
app_name = "product"
urlpatterns = [
    # 礼品管理
    url(r'^product/$', csrf_exempt(GiftView.as_view()), name='product'),
    url(r'^bill/$', csrf_exempt(BillView.as_view()), name='bill'),
    url(r'^anonymous/$', csrf_exempt(GiftAnonymousView.as_view()), name='anonymous'),
    # 规格管理
    url(r'^specifications/$', csrf_exempt(SpecificationsView.as_view()), name='specifications'),
    # 分类管理
    url(r'^category/$', csrf_exempt(CategoryView.as_view()), name='category'), 
    url(r'^purchase_way/$', csrf_exempt(PurchaseWayView.as_view()), name='purchase_way'),
]