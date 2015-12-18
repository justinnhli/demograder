from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.CourseListView.as_view(), name='Course List View'),
    url(r'^courses/(?P<course_id>[0-9]+)/$', views.ProjectListView.as_view(), name='Project List View'),
    url(r'^projects/(?P<project_id>[0-9]+)/$', views.submit_project, name='Project Status View'),
]
