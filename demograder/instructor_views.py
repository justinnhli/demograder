from collections import namedtuple

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render

from .models import Submission
from .views import get_context

@login_required
def instructor_student_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    context['grades'] = []
    for course in context['student'].enrolled_course_set.all():
        for project in course.project_set().all();
            context['grades'].append(Submission.objects.filter(student=student, project=project).latest('timestamp'))
    context['grades'] = sorted(context['grades'], key=(lambda s: s.project.name))
    context['submissions'] = context['student'].submission_set.order_by('-timestamp')
    return render(request, 'demograder/instructor/student.html', context)

@login_required
def instructor_project_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    SubmissionDisplay = namedtuple('SubmissionDisplay', ('id', 'student', 'isoformat', 'score', 'max_score'))
    submissions = []
    for student in context['course'].student_set.all():
        try:
            submission = Submission.objects.filter(student=student, project=context['project']).latest('timestamp')
            sid = submission.id
            timestamp = submission.isoformat
            score = submission.score
            max_score = submission.max_score
        except Submission.DoesNotExist:
            sid = 0
            timestamp = 'N/A'
            score = 'N'
            max_score = 'A'
        submissions.append(SubmissionDisplay(sid, student, timestamp, score, max_score))
    context['submissions'] = sorted(submissions, key=(lambda s: s.student.name))
    return render(request, 'demograder/instructor/project.html', context)
