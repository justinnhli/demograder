from django.conf.urls import url

from .views import index_view, course_view, project_view, project_submit_handler, result_view, download_view, display_view
from .instructor_views import instructor_view, instructor_submissions_view, instructor_student_view, instructor_course_view, instructor_assignment_view, instructor_project_view, instructor_submission_view
from .instructor_views import instructor_project_regrade_view, instructor_submission_regrade_view

urlpatterns = [
    url(r'^$', index_view, name='index'),
    url(r'^course/(?P<course_id>[0-9]+)/$', course_view, name='course'),
    url(r'^project/(?P<project_id>[0-9]+)/$', project_view, name='project'),
    url(r'^project/(?P<project_id>[0-9]+)/submit/$', project_submit_handler, name='project_submit'),
    url(r'^submission/(?P<submission_id>[0-9]+)/$', project_view, name='submission'),
    url(r'^result/(?P<result_id>[0-9]+)/$', result_view, name='result'),
    url(r'^download/(?P<upload_id>[0-9]+)/$', download_view, name='download'),
    url(r'^display/(?P<upload_id>[0-9]+)/$', display_view, name='display'),

    url(r'^instructor/$', instructor_view, name='instructor_index'),
    url(r'^instructor/submissions/$', instructor_submissions_view, name='instructor_submissions'),
    url(r'^instructor/student/(?P<student_id>[0-9]+)/$', instructor_student_view, name='instructor_student'),
    url(r'^instructor/course/(?P<course_id>[0-9]+)/$', instructor_course_view, name='instructor_course'),
    url(r'^instructor/assignment/(?P<assignment_id>[0-9]+)/$', instructor_assignment_view, name='instructor_assignment'),
    url(r'^instructor/project/(?P<project_id>[0-9]+)/$', instructor_project_view, name='instructor_project'),
    url(r'^instructor/submission/(?P<submission_id>[0-9]+)/$', instructor_submission_view, name='instructor_submission'),
    url(r'^instructor/project-regrade/(?P<project_id>[0-9]+)$', instructor_project_regrade_view, name='instructor_project_regrade'),
    url(r'^instructor/submission-regrade/(?P<submission_id>[0-9]+)$', instructor_submission_regrade_view, name='instructor_submission_regrade'),
]
