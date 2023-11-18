#! -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from product.bill_view import BillView
from product.views import CategoryView, ProductView, \
    SpecificationsView, ProductAnonymousView
from product.purchase_way_views import PurchaseWayView
app_name = "product"
urlpatterns = [
    # 管理
    url(r'^products/$', csrf_exempt(ProductView.as_view()), name='product'),
    url(r'^anonymous/$', csrf_exempt(ProductAnonymousView.as_view()), name='anonymous'),
    url(r'^bill/$', csrf_exempt(BillView.as_view()), name='bill'),
    # 规格管理
    url(r'^specifications/$', csrf_exempt(SpecificationsView.as_view()),
        name='specifications'),
    # 分类管理
    url(r'^category/$', csrf_exempt(CategoryView.as_view()), name='category'),
    # 里程榜前三赠送管理

    url(r'^purchase_way/$', csrf_exempt(PurchaseWayView.as_view()), name='purchase_way'),
]
