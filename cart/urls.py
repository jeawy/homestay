from django.conf.urls import url 
from cart.views import CartView
from django.views.decorators.csrf import csrf_exempt
app_name = "cart"
urlpatterns = [  
    url(r'^cart/$', csrf_exempt(CartView.as_view()), name='cart'),
]
