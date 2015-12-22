from django.conf.urls import url

from .views import common, student, instructor

urlpatterns = [
    url(r'^$', common.index_view, name='index'),
    url(r'^login/$', common.login_view, name='login'), # TODO this should direct to an Kerberos login page
    # student pages
    url(r'^student/$', student.index_view, name='student'),
    url(r'^courses/(?P<course_id>[0-9]+)/$', student.course_view, name='course'),
    url(r'^projects/(?P<project_id>[0-9]+)/$', student.project_view, name='project'),
    url(r'^projects/(?P<project_id>[0-9]+)/upload/$', student.project_upload_view, name='project_upload'),
    url(r'^projects/(?P<project_id>[0-9]+)/submit/$', student.project_submit_handler, name='project_submit'),
    url(r'^submissions/(?P<submission_id>[0-9]+)/$', student.project_view, name='submission'),
    url(r'^download/(?P<upload_id>[0-9]+)/$', student.download_view, name='download'),
    url(r'^results/(?P<result_id>[0-9]+)/$', student.result_view, name='result'),
    # instructor pages
    url(r'^instructor/$', instructor.index_view, name='instructor'),
    url(r'^instructor/course_create/$', instructor.CourseCreate.as_view(), name='course_create'),
    url(r'^instructor/course_edit/(?P<course_id>[0-9]+)/$', instructor.CourseEdit.as_view(), name='course_edit'),
    url(r'^instructor/course/(?P<course_id>[0-9]+)/$', instructor.course_view, name='instructor_course'),
    url(r'^instructor/course_delete/(?P<course_id>[0-9]+)/$', instructor.CourseDelete.as_view(), name='course_delete'),
]
