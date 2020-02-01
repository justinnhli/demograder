from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import RedirectView
from django.contrib.auth.views import LoginView, LogoutView

from .views import index_view, course_view, project_view, project_submit_handler, result_view, download_view, display_view
from .instructor_views import instructor_view, instructor_tbd_view, instructor_submissions_view, instructor_student_view, instructor_course_view, instructor_assignment_view, instructor_project_view
from .instructor_views import instructor_assignment_regrade_view, instructor_project_regrade_view, instructor_submission_regrade_view, instructor_result_regrade_view

urlpatterns = [
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^logout/$', LogoutView.as_view(next_page='/login'), name='logout'),
    url(r'^oauth/', include('social_django.urls', namespace='social')),
    url(r'^$', RedirectView.as_view(url='demograder/')),
    url(r'^demograder/$', index_view, name='index'),
    url(r'^demograder/course/(?P<course_id>[0-9]+)/$', course_view, name='course'),
    url(r'^demograder/project/(?P<project_id>[0-9]+)/$', project_view, name='project'),
    url(r'^demograder/project/(?P<project_id>[0-9]+)/submit/$', project_submit_handler, name='project_submit'),
    url(r'^demograder/submission/(?P<submission_id>[0-9]+)/$', project_view, name='submission'),
    url(r'^demograder/result/(?P<result_id>[0-9]+)/$', result_view, name='result'),
    url(r'^demograder/download/(?P<upload_id>[0-9]+)/$', download_view, name='download'),
    url(r'^demograder/display/(?P<upload_id>[0-9]+)/$', display_view, name='display'),
    url(r'^demograder/display_test/(?P<upload_id>[0-9]+)/$', display_test_view, name='display_test'),
    url(r'^demograder/instructor/$', instructor_view, name='instructor_index'),
    url(r'^demograder/instructor/submissions/$', instructor_submissions_view, name='instructor_submissions'),
    url(r'^demograder/instructor/tbd/$', instructor_tbd_view, name='instructor_tbd'),
    url(r'^demograder/instructor/student/(?P<student_id>[0-9]+)/$', instructor_student_view, name='instructor_student'),
    url(r'^demograder/instructor/course/(?P<course_id>[0-9]+)/$', instructor_course_view, name='instructor_course'),
    url(
        r'^demograder/instructor/assignment/(?P<assignment_id>[0-9]+)/$',
        instructor_assignment_view,
        name='instructor_assignment'
    ),
    url(r'^demograder/instructor/project/(?P<project_id>[0-9]+)/$', instructor_project_view, name='instructor_project'),
    url(
        r'^demograder/instructor/assignment-regrade/(?P<assignment_id>[0-9]+)$',
        instructor_assignment_regrade_view,
        name='instructor_assignment_regrade',
    ),
    url(
        r'^demograder/instructor/project-regrade/(?P<project_id>[0-9]+)$',
        instructor_project_regrade_view,
        name='instructor_project_regrade',
    ),
    url(
        r'^demograder/instructor/submission-regrade/(?P<submission_id>[0-9]+)$',
        instructor_submission_regrade_view,
        name='instructor_submission_regrade',
    ),
    url(
        r'^demograder/instructor/result-regrade/(?P<result_id>[0-9]+)$',
        instructor_result_regrade_view,
        name='instructor_result_regrade',
    ),
    url(r'^django-rq/', include('django_rq.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/login/$', LoginView.as_view(), name='admin_login'),
    url(r'^accounts/logout/$', LogoutView.as_view(next_page='/login'), name='admin_logout'),
]
urlpatterns += staticfiles_urlpatterns()
