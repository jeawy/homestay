from django.conf.urls import url 
from wktemplate.views import WkTemplateView
from wktemplate.views_v2 import WkTemplateView_V2
from wktemplate.extra_work_view import ExtraWorkRuleView
from django.views.decorators.csrf import csrf_exempt
app_name = "dept"
urlpatterns = [
    url(r'^wktemplate/$', csrf_exempt(WkTemplateView.as_view()), name='wktemplate'),
    url(r'^wktemplate_v2/$', csrf_exempt(WkTemplateView_V2.as_view()), name='wktemplate_v2'),
    url(r'^extral_work_rule/$', csrf_exempt(ExtraWorkRuleView.as_view()), name='extral_work_rule'),
]
