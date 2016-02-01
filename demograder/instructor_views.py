from collections import namedtuple

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render

from .models import Submission
from .views import get_context

SubmissionDisplay = namedtuple('SubmissionDisplay', ('id', 'student', 'project', 'isoformat', 'score', 'max_score'))

@login_required
def instructor_student_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    context['grades'] = []
    for course in context['student'].enrolled_course_set.all():
        for project in course.project_set.all():
            if not project.hidden:
                try:
                    submission = Submission.objects.filter(student=context['student'], project=project).latest('timestamp')
                except Submission.DoesNotExist:
                    submission = SubmissionDisplay(0, context['student'], project, 'N/A', 'N', 'A')
                context['grades'].append(submission)
    context['grades'] = sorted(context['grades'], key=(lambda s: s.project.name))
    context['submissions'] = context['student'].submission_set.order_by('-timestamp')
    return render(request, 'demograder/instructor/student.html', context)

@login_required
def instructor_project_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    submissions = []
    for student in context['course'].student_set.all():
        try:
            submission = Submission.objects.filter(student=student, project=context['project']).latest('timestamp')
        except Submission.DoesNotExist:
            submission = SubmissionDisplay(0, student, context['project'], 'N/A', 'N', 'A')
        submissions.append(submission)
    context['submissions'] = sorted(submissions, key=(lambda s: s.student.name))
    return render(request, 'demograder/instructor/project.html', context)
