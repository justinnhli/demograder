from collections import namedtuple

import django_rq
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.http import HttpResponseRedirect, FileResponse
from django.shortcuts import render, get_object_or_404

from .forms import SubmissionUploadForm
from .models import Course, Enrollment, Person, Assignment, Project, Submission, Upload, Result, ProjectDependency
from .dispatcher import enqueue_submission_dispatch


def get_context(request, **kwargs):
    context = {}
    context['user'] = request.user
    if not hasattr(context['user'], 'person'):
        Person(user=context['user']).save()
    context['person'] = context['user'].person
    # upload
    if 'upload_id' in kwargs:
        context['upload'] = get_object_or_404(Upload, id=kwargs['upload_id'])
    # result
    if 'result_id' in kwargs:
        context['result'] = get_object_or_404(Result, id=kwargs['result_id'])
    # submission
    if 'upload' in context:
        context['submission'] = context['upload'].submission
    elif 'result' in context:
        context['submission'] = context['result'].submission
    elif 'submission_id' in kwargs:
        context['submission'] = get_object_or_404(Submission, id=kwargs['submission_id'])
    # project and student
    if 'submission' in context:
        context['project'] = context['submission'].project
        context['student'] = context['submission'].student
    elif 'project_id' in kwargs:
        context['project'] = get_object_or_404(Project, id=kwargs['project_id'])
        context['student'] = context['person']
    elif 'student_id' in kwargs:
        context['student'] = get_object_or_404(Person, id=kwargs['student_id'])
    # assignment
    if 'assignment_id' in kwargs:
        context['assignment'] = get_object_or_404(Assignment, id=kwargs['assignment_id'])
    elif 'project' in context:
        context['assignment'] = context['project'].assignment
    # course
    if 'assignment' in context:
        context['course'] = context['assignment'].course
    elif 'course_id' in kwargs:
        context['course'] = get_object_or_404(Course, id=kwargs['course_id'])
    context['is_instructor'] = (
        context['user'].is_superuser
        or (
            'course' in context
            and context['course'].instructor == context['person']
        )
    )
    if not context['is_instructor']:
        if 'course' in context:
            if Enrollment.objects.filter(student=context['person'], course=context['course']).count() == 0:
                raise PermissionDenied
        if 'upload' in context:
            if context['person'] != context['student']:
                if ProjectDependency.objects.filter(producer=context['project'], project__visible=True).count() == 0:
                    raise PermissionDenied
        else:
            if 'project' in context:
                if not context['project'].visible:
                    raise PermissionDenied
            if 'submission' in context:
                if context['submission'].student != context['person']:
                    raise PermissionDenied
    return context


@login_required
def index_view(request, **kwargs):
    context = get_context(request, **kwargs)
    context['submissions'] = context['person'].submissions()[:20]
    return render(request, 'demograder/index.html', context)


SubmissionDisplay = namedtuple(
    'SubmissionDisplay',
    [
        'student',
        'project',
        'iso_format',
        'num_passed',
        'num_tbd',
        'num_failed',
        'max_score',
        'score_str',
    ],
)


def get_last_submission_display(submitter, project):
    submission = submitter.latest_submission(project)
    if submission:
        return submission
    else:
        return SubmissionDisplay(submitter, project, '', 0, 0, 0, 0, '')


@login_required
def course_view(request, **kwargs):
    context = get_context(request, **kwargs)
    assignments = []
    for assignment in context['course'].assignments():
        if assignment.has_visible_projects or context['is_instructor']:
            submissions = []
            for project in assignment.projects():
                if project.visible or context['is_instructor']:
                    submissions.append(get_last_submission_display(context['person'], project))
            assignments.append([
                assignment,
                '{:.2%}'.format(context['person'].get_assignment_score(assignment)),
                submissions,
            ])
    context['assignments'] = assignments
    return render(request, 'demograder/course.html', context)


@login_required
def project_view(request, **kwargs):
    context = get_context(request, **kwargs)
    submissions = context['student'].submissions(project=context['project'])
    if bool(submissions):
        context['submissions'] = submissions.order_by('-timestamp')
        if 'submission' not in context:
            context['submission'] = context['submissions'][0]
        # FIXME select the latest submission using the django last filter instead
        # see https://docs.djangoproject.com/en/1.11/ref/templates/builtins/#last
        context['project_latest'] = context['submissions'][0]
        context['results'] = context['submission'].result_set.all()
    context['may_submit'] = context['person'].may_submit(context['project'])
    # FIXME select the latest submission using the django last filter instead
    # see https://docs.djangoproject.com/en/1.11/ref/templates/builtins/#last
    if context['person'].submissions():
        context['latest'] = context['person'].latest_submission()
    else:
        context['latest'] = None
    context['form'] = SubmissionUploadForm(project=context['project'])
    context['queue_size'] = django_rq.get_queue('evaluation').count
    return render(request, 'demograder/project.html', context)


@login_required
def project_submit_handler(request, **kwargs):
    context = get_context(request, **kwargs)
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('project', kwargs=kwargs))
    if context['person'].may_submit(context['project']) != 'yes':
        return HttpResponseRedirect(reverse('project', kwargs=kwargs))
    form = SubmissionUploadForm(request.POST, request.FILES, project=context['project'])
    if form.is_valid():
        submission = Submission(
            project=context['project'],
            student=context['person'],
        )
        submission.save()
        for file_field, project_file in zip(context['project'].file_fields, context['project'].files):
            if file_field in request.FILES:
                Upload(
                    submission=submission,
                    project_file=project_file,
                    file=request.FILES[file_field],
                ).save()
        enqueue_submission_dispatch(submission.id)
    return HttpResponseRedirect(reverse('project', kwargs=kwargs))


@login_required
def result_view(request, **kwargs):
    context = get_context(request, **kwargs)
    return render(request, 'demograder/result.html', context)


@login_required
def download_view(request, **kwargs):
    context = get_context(request, **kwargs)
    return FileResponse(
        open(context['upload'].file.name, 'rb'),
        as_attachment=True,
    )


@login_required
def display_view(request, **kwargs):
    context = get_context(request, **kwargs)
    file_full_path = context['upload'].file.name
    with open(file_full_path) as fd:
        context['contents'] = fd.read()
    return render(request, 'demograder/display.html', context)
