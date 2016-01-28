from collections import namedtuple
from mimetypes import guess_type
from os.path import basename, getsize

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render, render_to_response, get_object_or_404
from django.template import RequestContext

from .forms import FileUploadForm
from .models import Course, Enrollment, Project, Submission, Upload, Result, StudentDependency
from .dispatcher import dispatch_submission
from .views import get_context

@login_required
def project_grade_view(request, **kwargs):
    Grade = namedTuple('Grade', ('name', 'timestamp', 'score', 'uploads'))
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    submissions = []
    for enrollment in course.enrollment_set.all():
        student = enrollment.student
        name = '{} {}'.format(student.user.first_name, student.user.last_name)
        submission = Submission.objects.filter(student=student, project=project).latest('timestamp')
        if bool(submission):
            timestamp = submission.isoformat()
            score = '{}/{}'.format(submission.score, submission.max_score)
            uploads = list(submission.upload_set.all())
        else:
            timestamp = 'N/A'
            score = 'N/A'
            uploads = 'N/A'
        submissions.append(Grade(name, timestamp, score, uploads))
    context['submissions'] = sorted(submissions, key=(lambda g: g.name))
    return HttpResponseRedirect(reverse('index', kwargs=kwargs))
