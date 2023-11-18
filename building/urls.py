from django.conf.urls import url 
from building.batch_view import BatchView
from building.views_building import BuildingView
from building.views_room import RoomView
from building.views_msgrecord import MsgRecordView
from building.views_fee_cal import RoomFeeCalculateView
from building.views_fee_order import  RoomFeeOrderView, RoomFeeOrderOrgView
from django.views.decorators.csrf import csrf_exempt
from building.views_feerate import RoomFeeRateCalView, RoomFeeRateView
app_name = "building"

urlpatterns = [  
    url(r'^batch/$', csrf_exempt(BatchView.as_view()), name='batch'),
    url(r'^building/$', csrf_exempt(BuildingView.as_view()), name='building'),
    url(r'^room/$', csrf_exempt(RoomView.as_view()), name='room'),
    url(r'^org/$', csrf_exempt(RoomFeeOrderOrgView.as_view()), name='org'),
    url(r'^record/$', csrf_exempt(MsgRecordView.as_view()), name='record'), 
    url(r'^order/$', csrf_exempt(RoomFeeOrderView.as_view()), name='order'),
    url(r'^feerate/$', csrf_exempt(RoomFeeRateView.as_view()), name='feerate'),
    url(r'^feeratecal/$', csrf_exempt(RoomFeeRateCalView.as_view()), name='feeratecal'),
    url(r'^cal/$', csrf_exempt(RoomFeeCalculateView.as_view()), name='cal'),
]
