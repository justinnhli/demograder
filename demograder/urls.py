from django.conf.urls import url

from .views import student

urlpatterns = [
    url(r'^$', student.index_view, name='index'),
    url(r'^courses/(?P<course_id>[0-9]+)/$', student.course_view, name='course'),
    url(r'^projects/(?P<project_id>[0-9]+)/$', student.project_view, name='project'),
    url(r'^projects/(?P<project_id>[0-9]+)/upload/$', student.project_upload_view, name='project_upload'),
    url(r'^projects/(?P<project_id>[0-9]+)/submit/$', student.project_submit_handler, name='project_submit'),
    url(r'^submissions/(?P<submission_id>[0-9]+)/$', student.project_view, name='submission'),
    url(r'^download/(?P<upload_id>[0-9]+)/$', student.download_view, name='download'),
    url(r'^results/(?P<result_id>[0-9]+)/$', student.result_view, name='result'),
]
