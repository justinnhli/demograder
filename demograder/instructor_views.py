from collections import namedtuple

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404

from .models import Submission
from .views import get_context

@login_required
def project_grade_view(request, **kwargs):
    Grade = namedtuple('Grade', ('name', 'timestamp', 'score', 'uploads'))
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    submissions = []
    for enrollment in context['course'].enrollment_set.all():
        student = enrollment.student
        name = '{} {}'.format(student.user.first_name, student.user.last_name)
        submission = Submission.objects.filter(student=student, project=context['project']).latest('timestamp')
        if bool(submission):
            timestamp = submission.isoformat()
            score = '{}/{}'.format(submission.score, submission.max_score)
            uploads = list(submission.upload_set.all())
        else:
            timestamp = 'N/A'
            score = 'N/A'
            uploads = []
        submissions.append(Grade(name, timestamp, score, uploads))
    context['submissions'] = sorted(submissions, key=(lambda g: g.name))
    return HttpResponseRedirect(reverse('index', kwargs=kwargs))
