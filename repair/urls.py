from django.conf.urls import url 
from repair.views import RepairView
from django.views.decorators.csrf import csrf_exempt
app_name = "repair"
urlpatterns = [  
    url(r'^repair/$', csrf_exempt(RepairView.as_view()), name='repair'),
]
