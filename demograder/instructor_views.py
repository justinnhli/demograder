from collections import namedtuple

import django_rq
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render

from .models import Course, Assignment, Project, Submission, Result
from .views import get_context, get_last_submission_display
from .dispatcher import enqueue_submission_dispatch, enqueue_submission_evaluation

AssignmentSummaryRow = namedtuple('AssignmentSummaryRow', ('student', 'submissions', 'grade'))


def is_superuser_or_instructor(context):
    if context['user'].is_superuser:
        return True
    if 'course' in context:
        return context['course'].instructor == context['user']
    else:
        return bool(Course.objects.filter(instructor=context['user']).count())


@login_required
def instructor_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if context['user'].is_superuser:
        context['courses'] = Course.objects.all()
    else:
        context['courses'] = Course.objects.filter(instructor=context['user'])
        if not context['courses']:
            raise Http404
    return render(request, 'demograder/instructor/index.html', context)


@login_required
def instructor_submissions_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    context['queue_size'] = django_rq.get_queue('evaluation').count
    context['tbd_size'] = Result.objects.filter(return_code=None).count
    context['submissions'] = Submission.objects.filter(project__visible=True)[:100]
    return render(request, 'demograder/instructor/submissions.html', context)


@login_required
def instructor_tbd_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    context['queue_size'] = django_rq.get_queue('evaluation').count
    context['tbd_results'] = Result.objects.filter(return_code=None)
    return render(request, 'demograder/instructor/tbd.html', context)


@login_required
def instructor_tbd_regrade_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not context['user'].is_superuser:
        raise Http404
    for result in Result.objects.filter(return_code=None):
        enqueue_submission_evaluation(result.id)
    return HttpResponseRedirect(reverse('instructor_tbd'))


@login_required
def instructor_student_view(request, **kwargs):
    context = get_context(request, **kwargs)
    # FIXME instructor should only see submissions for their courses
    if not context['user'].is_superuser:
        raise Http404
    context['grades'] = []
    for course in context['student'].enrolled_courses().all():
        for project in course.projects().all():
            if project.visible:
                context['grades'].append(get_last_submission_display(context['student'], project))
    # must write long-form accessors because submission could be SubmissionDisplay
    context['grades'] = sorted(
        context['grades'],
        key=(lambda s: (
            -s.project.assignment.course.year.value,
            -s.project.assignment.course.season,
            s.project.course.catalog_id_str,
            s.project.assignment.name,
            s.project.name))
    )
    context['submissions'] = context['student'].submissions()
    return render(request, 'demograder/instructor/student.html', context)


@login_required
def instructor_course_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not is_superuser_or_instructor(context):
        raise Http404
    context['students'] = context['course'].enrolled_students()
    context['assignments'] = Assignment.objects.filter(course=context['course'])
    context['submissions'] = Submission.objects.filter(project__assignment__course=context['course'])
    return render(request, 'demograder/instructor/course.html', context)


@login_required
def instructor_assignment_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not is_superuser_or_instructor(context):
        raise Http404
    context['projects'] = context['assignment'].projects().filter(visible=True)
    context['student_scores'] = []
    for student in context['course'].enrolled_students():
        submissions = []
        for project in context['projects']:
            # FIXME deal with other submission types
            if project.submission_type == Project.LATEST:
                submissions.append(get_last_submission_display(student, project))
        context['student_scores'].append(AssignmentSummaryRow(
            student,
            submissions,
            '{:.2%}'.format(student.get_assignment_score(context['assignment']))
        ))
    context['submissions'] = Submission.objects.filter(project__assignment=context['assignment'])
    return render(request, 'demograder/instructor/assignment.html', context)


@login_required
def instructor_project_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not is_superuser_or_instructor(context):
        raise Http404
    context['scores'] = [
        get_last_submission_display(student, context['project'])
        for student in context['course'].enrolled_students()
    ]
    context['submissions'] = Submission.objects.filter(project=context['project'])
    return render(request, 'demograder/instructor/project.html', context)


@login_required
def instructor_submission_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not is_superuser_or_instructor(context):
        raise Http404
    context['submissions'] = context['student'].submissions(project=context['project'])
    if 'submission' not in context:
        context['submission'] = context['submissions'][0]
    return render(request, 'demograder/project.html', context)


def regrade_assignment(assignment):
    for project in assignment.projects():
        regrade_project(project)


@login_required
def instructor_assignment_regrade_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not is_superuser_or_instructor(context):
        raise Http404
    regrade_assignment(context['assignment'])
    return HttpResponseRedirect(
        reverse('instructor_assignment', kwargs={'assignment_id': context['project'].assignment.id})
    )


def regrade_project(project):
    for student in project.course.enrolled_students():
        submission = student.latest_submission(project=project)
        if submission:
            regrade_submission(submission)


@login_required
def instructor_project_regrade_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not is_superuser_or_instructor(context):
        raise Http404
    regrade_project(context['project'])
    return HttpResponseRedirect(
        reverse('instructor_assignment', kwargs={'assignment_id': context['project'].assignment.id})
    )


def regrade_submission(submission):
    submission.result_set.all().delete()
    enqueue_submission_dispatch(submission.id)


@login_required
def instructor_submission_regrade_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not is_superuser_or_instructor(context):
        raise Http404
    regrade_submission(context['submission'])
    return HttpResponseRedirect(reverse('submission', kwargs=kwargs))


def regrade_result(result):
    enqueue_submission_evaluation(result.id, timeout=result.project.timeout + 1)


@login_required
def instructor_result_regrade_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if not is_superuser_or_instructor(context):
        raise Http404
    regrade_result(context['result'])
    return HttpResponseRedirect(reverse('result', kwargs=kwargs))
