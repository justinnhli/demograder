from collections import namedtuple

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render

from .models import Course, Assignment, Project, Submission
from .views import get_context
from .dispatcher import enqueue_submission_dispatch

SubmissionDisplay = namedtuple('SubmissionDisplay', ('id', 'student', 'project', 'isoformat', 'score', 'max_score'))

AssignmentSummaryRow = namedtuple('AssignmentSummaryRow', ('student', 'submissions', 'grade'))


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
    for course in context['student'].enrolled_courses().all():
        for project in course.projects().all():
            if project.visible:
                try:
                    submission = context['student'].latest_submission(project=project)
                    if not submission:
                        submission = SubmissionDisplay(0, context['student'], project, 'N/A', 'N', 'A')
                except Submission.DoesNotExist:
                    submission = SubmissionDisplay(0, context['student'], project, 'N/A', 'N', 'A')
                context['grades'].append(submission)
    context['grades'] = sorted(context['grades'], key=(lambda s: (s.project.assignment.name, s.project.name)))
    context['submissions'] = context['student'].submissions().order_by('-timestamp')
    return render(request, 'demograder/instructor/student.html', context)


@login_required
def instructor_course_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    context['students'] = context['course'].enrolled_students().order_by('user__first_name', 'user__last_name')
    assignments = set(Project.objects.filter(assignment__course=context['course']).values_list('assignment', flat=True))
    assignments = [Assignment.objects.get(pk=id) for id in assignments]
    context['assignments'] = sorted(assignments, key=(lambda a: -a.id))
    return render(request, 'demograder/instructor/course.html', context)


@login_required
def instructor_assignment_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    context['projects'] = context['assignment'].projects().filter(visible=True)
    context['student_scores'] = []
    for student in context['course'].enrolled_students():
        submissions = []
        for project in context['projects']:
            # FIXME deal with other submission types
            if project.submission_type == Project.LATEST:
                submission = student.latest_submission(project=project)
                if submission and submission.max_score > 0:
                    submissions.append(submission)
                else:
                    submissions.append(None)
        context['student_scores'].append(AssignmentSummaryRow(student, submissions, '{:.2%}'.format(student.get_assignment_score(context['assignment']))))
    return render(request, 'demograder/instructor/assignment.html', context)


@login_required
def instructor_project_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    submissions = []
    for student in context['course'].enrolled_students().all():
        try:
            submission = student.latest_submission(project=context['project'])
            if not submission:
                submission = SubmissionDisplay(0, student, context['project'], 'N/A', 'N', 'A')
        except Submission.DoesNotExist:
            submission = SubmissionDisplay(0, student, context['project'], 'N/A', 'N', 'A')
        submissions.append(submission)
    context['submissions'] = sorted(submissions, key=(lambda s: s.student.last_name))
    return render(request, 'demograder/instructor/project.html', context)


@login_required
def instructor_submission_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    context['submissions'] = context['student'].submissions(project=context['project']).order_by('-timestamp')
    if 'submission' not in context:
        context['submission'] = context['submissions'][0]
    return render(request, 'demograder/project.html', context)


@login_required
def instructor_project_regrade_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    for student in context['project'].course.enrolled_students():
        try:
            submission = student.latest_submission(project=context['project'])
            submission.result_set.all().delete()
            enqueue_submission_dispatch(submission)
        except Submission.DoesNotExist:
            pass
    return HttpResponseRedirect(
        reverse('instructor_assignment', kwargs={'assignment_id': context['project'].assignment.id})
    )


@login_required
def instructor_submission_regrade_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    context['submission'].result_set.all().delete()
    enqueue_submission_dispatch(context['submission'].id)
    return HttpResponseRedirect(reverse('submission', kwargs=kwargs))
