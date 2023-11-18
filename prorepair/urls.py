from django.conf.urls import url 
from prorepair.views import ProRepairView 
from django.views.decorators.csrf import csrf_exempt
app_name = "prorepair"
urlpatterns = [  
    url(r'^prorepair/$', csrf_exempt(ProRepairView.as_view()), name='prorepair'),
    
]
