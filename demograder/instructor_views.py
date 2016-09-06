from collections import namedtuple
from statistics import mean

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render

from .models import Course, Project, Submission
from .views import get_context, AssignmentInfo
from .util import SubmissionDisplay

@login_required
def instructor_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    context['courses'] = Course.objects.all()
    return render(request, 'demograder/instructor/index.html', context)

@login_required
def instructor_submissions_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    context['submissions'] = Submission.objects.filter(project__visible=True).order_by('-timestamp')[:100]
    return render(request, 'demograder/instructor/submissions.html', context)

@login_required
def instructor_student_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    context['grades'] = []
    for course in context['student'].enrolled_course_set.all():
        for project in course.project_set.all():
            if project.visible:
                try:
                    submission = Submission.objects.filter(student=context['student'], project=project).latest('timestamp')
                except Submission.DoesNotExist:
                    submission = SubmissionDisplay(0, context['student'], project, 'N/A', 'N', 'A')
                context['grades'].append(submission)
    context['grades'] = sorted(context['grades'], key=(lambda s: (s.project.assignment, s.project.name)))
    context['submissions'] = context['student'].submission_set.order_by('-timestamp')
    return render(request, 'demograder/instructor/student.html', context)

@login_required
def instructor_course_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    context['students'] = context['course'].student_set.order_by('user__first_name', 'user__last_name')
    assignments = []
    for assignment in set(Project.objects.values_list('assignment', flat=True)):
        projects = Project.objects.filter(assignment=assignment).order_by('name')
        if context['user'].is_superuser or any(p.visible for p in projects):
            assignments.append(AssignmentInfo(assignment, max(p.id for p in projects), projects))
    context['assignments'] = sorted(assignments, key=(lambda a: -a.max_id))
    return render(request, 'demograder/instructor/course.html', context)

AssignmentSummaryRow = namedtuple('AssignmentSummaryRow', ('student', 'submissions', 'grade'))

@login_required
def instructor_assignment_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    context['projects'] = context['assignment'].projects().filter(visible=True)
    context['student_scores'] = []
    for student in context['course'].enrolled_students():
        submissions = []
        scores = []
        for project in context['projects']:
            # FIXME deal with other submission types
            if project.submission_type == Project.LATEST:
                try:
                    submission = Submission.objects.filter(student=student, project=project).latest('timestamp')
                    submissions.append(submission)
                    scores.append(submission.score / submission.max_score)
                except Submission.DoesNotExist:
                    submissions.append(None)
                    scores.append(0)
        context['student_scores'].append(AssignmentSummaryRow(student, submissions, '{:.2%}'.format(mean(scores))))
    return render(request, 'demograder/instructor/assignment.html', context)

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

@login_required
def instructor_submission_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    context['submissions'] = Submission.objects.filter(project=context['project'], student=context['student']).order_by('-timestamp')
    if 'submission' not in context:
        context['submission'] = context['submissions'][0]
    return render(request, 'demograder/project.html', context)

@login_required
def instructor_regrade_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    for submission in get_last_submissions(context['project']):
        submission.result_set.all().delete()
        dispatch_submission(submission)
    return HttpResponseRedirect(reverse('index', kwargs=kwargs))

@login_required
def instructor_single_dependencies_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    # FIXME put student dependency code here
    # eventually a GUI will be built for this
    return HttpResponseRedirect(reverse('index', kwargs=kwargs))

@login_required
def instructor_multiple_dependencies_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    # FIXME put student dependency code here
    # eventually a GUI will be built for this
    return HttpResponseRedirect(reverse('index', kwargs=kwargs))
