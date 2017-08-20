from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/login'}, name='logout'),
    url(r'^oauth/', include('social_django.urls', namespace='social')),

    url(r'^$', RedirectView.as_view(url='demograder')),
    url(r'^demograder/', include('demograder.urls'), name='demograder'),

    url(r'^django-rq/', include('django_rq.urls')),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^accounts/login/$', auth_views.login, name='admin_login'),
    url(r'^accounts/logout/$', auth_views.logout, {'next_page': '/demograder/'}, name='admin_logout'),
]
urlpatterns += staticfiles_urlpatterns()
