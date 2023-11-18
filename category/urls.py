from django.conf.urls import url 
from category.views_ui import CategoryView
from category.views_rest import CategoryRestView
from django.views.decorators.csrf import csrf_exempt
app_name = "category"
urlpatterns = [  
    url(r'^categories/$', csrf_exempt(CategoryView.as_view()), name='categories'),   
    url(r'^categories/api$', csrf_exempt(CategoryRestView.as_view()), name='categories_rest'),   
]
