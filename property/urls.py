"""property URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^api/$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^api/$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^api/blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings 

urlpatterns = [
    url(r'^api/admin/', admin.site.urls),
    # api
    url(r'^api/users/', include('appuser.urls', namespace="users")),
    url(r'^api/ckeditor/', include('ckeditor_uploader.urls' )),
    url(r'^api/category/', include('category.urls', namespace="category")),
    url(r'^api/organize/', include('organize.urls', namespace="organize")),
    url(r'^api/dept/', include('dept.urls', namespace="dept")), 
    #url(r'^api/ws/chat/', include('chat.urls')), 
    url(r'^api/role/', include('role.urls', namespace="role")),
    url(r'^api/wktemplate/', include('wktemplate.urls', namespace="wktemplate")),
    url(r'^api/appfile/', include('appfile.urls', namespace="appfile")), 
    url(r'^prx/api/appfile/', include('appfile.urls', namespace="prxappfile")), 
    url(r'^api/api/appfile/', include('appfile.urls', namespace="_appfile")), # should use re
    url(r'^api/attrs/', include('attrs.urls', namespace="attrs")), 
    url(r'^api/comment/', include('comment.urls', namespace="comment")),
    url(r'^api/oprecords/', include('oprecords.urls', namespace="oprecords")),  
    url(r'^api/notice/', include('notice.urls', namespace="notice")), 
    url(r'^api/excel/', include('excel.urls', namespace="excel")),
    url(r'^api/wkconfig/', include('wkconfig.urls', namespace="wkconfig")), 
    url(r'^api/statistic/', include('statistic.urls', namespace="statistic")),
    url(r'^api/worktime/', include('worktime.urls', namespace="worktime")),  
    url(r'^api/menu/', include('menu.urls', namespace="menu")),
    url(r'^api/spread/', include('spread.urls', namespace="spread")), 
    url(r'^api/record/', include('record.urls', namespace="record")),
    url(r'^api/tags/', include('tags.urls', namespace="tags")),
    url(r'^api/content/', include('content.urls', namespace="content")),
    url(r'^api/address/', include('address.urls', namespace="address")),
    url(r'^api/area/', include('area.urls', namespace="area")),
    url(r'^api/community/', include('community.urls', namespace="community")),
    url(r'^api/building/', include('building.urls', namespace="building")), 
    url(r'^api/fee/', include('fee.urls', namespace="fee")),
    url(r'^api/pay/', include('pay.urls', namespace="pay")),
    url(r'^api/msg/', include('msg.urls', namespace="msg")),
    url(r'^api/orders/', include('orders.urls', namespace="orders")),
    url(r'^api/repair/', include('repair.urls', namespace="repair")),
    url(r'^api/paidservice/', include('paidservice.urls', namespace="paidservice")),
    url(r'^api/feedback/', include('feedback.urls', namespace="feedback")),
    url(r'^api/prorepair/', include('prorepair.urls', namespace="prorepair")),
    url(r'^api/webcoin/', include('webcoin.urls', namespace="webcoin")),

    url(r'^api/cart/', include('cart.urls', namespace="cart")), 
    url(r'^api/like/', include('like.urls', namespace="like")), 
    url(r'^api/incomes/', include('incomes.urls', namespace="incomes")),
    url(r'^api/withdraw/', include('withdraw.urls', namespace="withdraw")), 
    url(r'^api/backlog/', include('backlog.urls', namespace="backlog")),   
    url(r'^api/appshare/', include('appshare.urls', namespace="appshare")),
    url(r'^api/wx/', include('wx.urls', namespace="wx")),    
    url(r'^api/product/', include('product.urls', namespace="product")),  
    url(r'^api/bills/', include('bills.urls', namespace="bills")),
    url(r'^api/card/', include('card.urls', namespace="card")),     
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

