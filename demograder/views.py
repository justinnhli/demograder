from mimetypes import guess_type
from os.path import basename, getsize

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, render_to_response, get_object_or_404
from django.template import RequestContext

from .forms import FileUploadForm
from .models import Course, Enrollment, Project, Submission, Upload, Result
from .dispatcher import dispatch_submission

def get_context(request, **kwargs):
    context = {}
    context['user'] = request.user
    if 'upload_id' in kwargs:
        context['upload'] = get_object_or_404(Upload, id=kwargs['upload_id'])
    if 'result_id' in kwargs:
        context['result'] = get_object_or_404(Result, id=kwargs['result_id'])
    if 'upload' in context:
        context['submission'] = context['upload'].submission
    elif 'result' in context:
        context['submission'] = context['result'].submission
    elif 'submission_id' in kwargs:
        context['submission'] = get_object_or_404(Submission, id=kwargs['submission_id'])
    if 'submission' in context:
        context['project'] = context['submission'].project
    elif 'project_id' in kwargs:
        context['project'] = get_object_or_404(Project, id=kwargs['project_id'])
    if 'project' in context:
        context['course'] = context['project'].course
    elif 'course_id' in kwargs:
        context['course'] = get_object_or_404(Course, id=kwargs['course_id'])
    if 'course' in context:
        try:
            Enrollment.objects.get(student=context['user'].person, course=context['course'])
        except Enrollment.DoesNotExist:
            raise PermissionDenied
    # FIXME check result permissions
    # FIXME check upload permissions
    return context

@login_required
def index_view(request, **kwargs):
    context = get_context(request, **kwargs)
    return render(request, 'demograder/index.html', context)

@login_required
def course_view(request, **kwargs):
    context = get_context(request, **kwargs)
    return render(request, 'demograder/course.html', context)

@login_required
def project_view(request, **kwargs):
    context = get_context(request, **kwargs)
    submissions = Submission.objects.filter(project=context['project'], student=context['user'])
    submissions_exist = bool(submissions)
    if submissions_exist:
        context['submissions'] = submissions.order_by('-timestamp')
        if 'submission' not in context:
            context['submission'] = context['submissions'][0]
            context['most_recent'] = True
        else:
            context['most_recent'] = (context['submission'] == context['submissions'][0])
        context['results'] = context['submission'].result_set.all()
    return render(request, 'demograder/project.html', context)

@login_required
def project_upload_view(request, **kwargs):
    context = get_context(request, **kwargs)
    context.update(kwargs)
    context['form'] = FileUploadForm()
    # TODO load student's previous test results
    # Render list page with the documents and the form
    return render_to_response(
        'demograder/project_upload.html',
        context,
        context_instance=RequestContext(request)
    )

@login_required
def project_submit_handler(request, **kwargs):
    context = get_context(request, **kwargs)
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('project', kwargs=kwargs))
    # Handle file upload
    form = FileUploadForm(request.POST, request.FILES)
    if form.is_valid():
        submission = Submission(
                project=context['project'],
                student=context['user'],
        )
        submission.save()
        # TODO handle multiple files per submission
        upload = Upload(
                submission=submission,
                file=request.FILES['file'],
        )
        upload.save()
        # find combination of all dependent files and submission and submit to RQ
        dispatch_submission(context['user'], context['project'], submission)
    return HttpResponseRedirect(reverse('project', kwargs=kwargs))

@login_required
def result_view(request, **kwargs):
    context = get_context(request, **kwargs)
    print(context['result'].resultdependency_set.all())
    for dependency in context['result'].resultdependency_set.all():
        for upload in dependency.producer.upload_set.all():
            print(upload.id, upload.basename)
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
