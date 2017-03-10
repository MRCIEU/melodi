from django.conf.urls import url

from . import views

urlpatterns = [
    	url(r'^$', views.index, name='index'),
	url(r'^jobs/', views.jobs, name='jobs'),
	url(r'^about', views.about, name='about'),
	url(r'^results/', views.results, name='results'),
	url(r'^complete/(?P<backend>[^/]+)/$', views.AuthComplete.as_view()),
    	url(r'^login-error/$', views.LoginError.as_view()),
	url(r'^database/$', views.OrderListJson.as_view(), name='order_list_json'),
	url(r'^pubs/',views.pubDetails, name='publication_details'),
	url(r'^ajax_searchset/$', views.ajax_searchset.as_view(), name='ajax_searchset'),
	url(r'^ajax_compare/$', views.ajax_compare.as_view(), name='ajax_compare'),
]
