from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index_view, name='index'),
    url(r'^courses/(?P<course_id>[0-9]+)/$', views.course_view, name='course'),
    url(r'^projects/(?P<project_id>[0-9]+)/$', views.project_view, name='project'),
    url(r'^projects/(?P<project_id>[0-9]+)/upload/$', views.project_upload_view, name='project_upload'),
    url(r'^projects/(?P<project_id>[0-9]+)/submit/$', views.project_submit_handler, name='project_submit'),
    url(r'^submissions/(?P<submission_id>[0-9]+)/$', views.project_view, name='submission'),
    url(r'^download/(?P<upload_id>[0-9]+)/$', views.download_view, name='download'),
]
