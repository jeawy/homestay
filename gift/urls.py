#! -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from gift.bill_view import BillView
from gift.views import CategoryView, GiftView, SpecificationsView, GiftAnonymousView 
from gift.purchase_way_views import PurchaseWayView
app_name = "gift"
urlpatterns = [
    # 礼品管理
    url(r'^gift/$', csrf_exempt(GiftView.as_view()), name='gift'),
    url(r'^bill/$', csrf_exempt(BillView.as_view()), name='bill'),
    url(r'^anonymous/$', csrf_exempt(GiftAnonymousView.as_view()), name='anonymous'),
    # 规格管理
    url(r'^specifications/$', csrf_exempt(SpecificationsView.as_view()), name='specifications'),
    # 分类管理
    url(r'^category/$', csrf_exempt(CategoryView.as_view()), name='category'), 
    url(r'^purchase_way/$', csrf_exempt(PurchaseWayView.as_view()), name='purchase_way'),
]