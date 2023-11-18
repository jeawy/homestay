from django.conf.urls import url  
from excel.views import ExcelView
from django.views.decorators.csrf import csrf_exempt

app_name = "excel"
urlpatterns = [   
    url(r'^excel/$', csrf_exempt(ExcelView.as_view()), name='excel'),
    #url(r'^save_excel/$', csrf_exempt(SaveExcelView.as_view()), name='save_excel'),
]
