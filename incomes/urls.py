from django.conf.urls import url 
from incomes.views import IncomesView 
from django.views.decorators.csrf import csrf_exempt
app_name = "incomes"
urlpatterns = [  
    url(r'^incomes/$', csrf_exempt(IncomesView.as_view()), name='incomes'), 
]
