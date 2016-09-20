from collections import namedtuple
from mimetypes import guess_type
from os.path import basename, getsize

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, render_to_response, get_object_or_404
from django.template import RequestContext

from .forms import FileUploadForm
from .models import Course, Enrollment, Person, Assignment, Project, Submission, Upload, Result, StudentDependency
from .dispatcher import enqueue_submission_dispatch

AssignmentInfo = namedtuple('AssignmentInfo', ('name', 'max_id', 'projects'))

def get_context(request, **kwargs):
    context = {}
    context['user'] = request.user
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
    if 'course' in context:
        context['is_instructor'] = (context['course'].instructor == context['person'])
    if not context['user'].is_superuser:
        if 'course' in context:
            try:
                Enrollment.objects.get(student=context['person'], course=context['course'])
            except Enrollment.DoesNotExist:
                raise PermissionDenied
        if 'upload' in context:
            if context['person'] != context['student']:
                try:
                    # FIXME update for new dependency shortcuts
                    StudentDependency.objects.get(
                            producer=context['student'],
                            student=context['person'],
                            dependency__producer=context['project'],
                    )
                except StudentDependency.DoesNotExist:
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
    context['submissions'] = Submissions.objects.filter(student=context['student'])
    return render(request, 'demograder/index.html', context)

@login_required
def course_view(request, **kwargs):
    context = get_context(request, **kwargs)
    if context['course'].instructor == context['person']:
        context['assignments'] = context['course'].assignments()
    else:
        context['assignments'] = [a for a in context['course'].assignments() if any(p.visible for p in a.projects())]
    return render(request, 'demograder/course.html', context)

@login_required
def project_view(request, **kwargs):
    context = get_context(request, **kwargs)
    submissions = Submission.objects.filter(project=context['project'], student=context['student'])
    if bool(submissions):
        context['submissions'] = submissions.order_by('-timestamp')
        if 'submission' not in context:
            context['submission'] = context['submissions'][0]
        context['project_latest'] = context['submissions'][0]
        context['results'] = context['submission'].result_set.all()
    context['allow_submit'] = context['person'].may_submit()
    context['latest'] = context['person'].latest_submission()
    context['form'] = FileUploadForm()
    return render(request, 'demograder/project.html', context, context_instance=RequestContext(request))

@login_required
def project_submit_handler(request, **kwargs):
    context = get_context(request, **kwargs)
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('project', kwargs=kwargs))
    if not context['person'].may_submit():
        return HttpResponseRedirect(reverse('project', kwargs=kwargs))
    # Handle file upload
    form = FileUploadForm(request.POST, request.FILES)
    if form.is_valid():
        submission = Submission(
                project=context['project'],
                student=context['person'],
        )
        submission.save()
        # TODO handle multiple files per submission
        upload = Upload(
                submission=submission,
                file=request.FILES['file'],
        )
        upload.save()
        enqueue_submission_dispatch(submission)
    return HttpResponseRedirect(reverse('project', kwargs=kwargs))

@login_required
def result_view(request, **kwargs):
    context = get_context(request, **kwargs)
    return render(request, 'demograder/result.html', context)

@login_required
def download_view(request, **kwargs):
    context = get_context(request, **kwargs)
    file_full_path = context['upload'].file.name
    with open(file_full_path) as fd:
        data = fd.read()
    response = HttpResponse(data, content_type=guess_type(file_full_path)[0])
    response['Content-Disposition'] = "attachment; filename={0}".format(basename(file_full_path))
    response['Content-Length'] = getsize(file_full_path)
    return response

@login_required
def display_view(request, **kwargs):
    context = get_context(request, **kwargs)
    file_full_path = context['upload'].file.name
    with open(file_full_path) as fd:
        data = fd.read()
    return HttpResponse(data, content_type='text/plain')
