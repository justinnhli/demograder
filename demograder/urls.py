from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.CourseListView.as_view(), name='Course List View'),
    url(r'^(?P<department>[A-Z]{3,4})/(?P<year>[0-9]{4})/(?P<season>[A-Za-z]+)/(?P<course_id>[0-9]+)/$', views.ProjectListView.as_view(), name='Project List View'),
    url(r'^(?P<department>[A-Z]{3,4})/(?P<year>[0-9]{4})/(?P<season>[A-Za-z]+)/(?P<course_id>[0-9]+)/(?P<project_id>[0-9]+)/$', views.submit_project, name='Project Status View'),
]
