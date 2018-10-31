"""melodi URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.views import logout, login
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from django.core.urlresolvers import reverse_lazy
from browser.views import *
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'sets', SearchSets, base_name="SetList")
#router.register(r'set', SearchSetDetail, base_name="Set")

urlpatterns = [
	url(r'^api/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
	#url(r'^api/set/(?P<pk>[0-9]+)/$', SearchSetDetail.as_view()),
    #url(r'^browser/', include('browser.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('social_auth.urls')),
    url(r'^about', about, name='about'),
    url(r'^citation', citation, name='citation'),
    url(r'^help', help, name='help'),
    url(r'^contact', contact, name='contact'),
    url(r'^logout/', logout, {'next_page': reverse_lazy('home')}, name='logout'),
    url(r'^login/', login, name='login'),
    #url(r'^login-error/$', TemplateView.as_view(template_name="login-error.html")),
    url(r'^$', index, name='home'),
    url(r'^jobs/', jobs, name='jobs'),
    url(r'^results/(?P<num>[0-9a-z-]+)/$', results, name='results'),
    url(r'^complete/(?P<backend>[^/]+)/$', AuthComplete.as_view()),
    url(r'^login-error/$', LoginError.as_view()),
    url(r'^database/$', OrderListJson.as_view(), name='order_list_json'),
    url(r'^pubs/(?P<num>[0-9]+_[0-9])/$',pubDetails, name='pubs'),
	url(r'^pubss/(?P<num>.*_[0-9]+_[0-9])/$',pubSingle, name='pubss'),
    url(r'^ajax_searchset/$', ajax_searchset.as_view(), name='ajax_searchset'),
    url(r'^ajax_compare/$', ajax_compare.as_view(), name='ajax_compare'),
    url(r'^get_semmed_items/',get_semmed_items, name='get_semmed_items'),
    url(r'^articles/(?P<num>[0-9]+)/$',articleDetails, name='articles'),
    url(r'^ajax_overlap/$', ajax_overlap.as_view(), name='ajax_overlap'),
	url(r'^dt_test_page/$', dt_test_page, name='dt_test_page'),
    url(r'^ajax_graph_metrics/$', ajax_graph_metrics, name='ajax_graph_metrics'),
    url(r'^ajax_share/$', ajax_share, name='ajax_share'),
    url(r'^ajax_delete/$', ajax_delete, name='ajax_delete'),
    url(r'^download_result/$', download_result, name='download_result'),
    url(r'^download_filter/$', download_filter, name='download_filter'),
    url(r'^upload_filter/$', upload_filter, name='upload_filter'),
    url(r'^save_filter/$', save_filter, name='save_filter'),
    url(r'^temmpo/$', temmpo, name='temmpo'),
    url(r'^temmpo_res/$', temmpo_res, name='temmpo_res')
]
