from mimetypes import guess_type
from os.path import basename, getsize

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, render_to_response
from django.template import RequestContext

from ..forms import FileUploadForm
from ..models import Submission, Upload
from ..dispatcher import dispatch_submission

from .common import get_context, logged_in

def get_student_context(**kwargs):
    context = get_context(**kwargs)
    # FIXME check permissions for course or redirect to home page
    # FIXME check permissions for project or redirect to home page
    # FIXME check permissions for submission or redirect to home page
    return context

@logged_in
def index_view(request, **kwargs):
    context = get_student_context(**kwargs)
    return render(request, 'demograder/student/index.html', context)

@logged_in
def course_view(request, **kwargs):
    context = get_student_context(**kwargs)
    return render(request, 'demograder/student/course.html', context)

@logged_in
def project_view(request, **kwargs):
    context = get_student_context(**kwargs)
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
    return render(request, 'demograder/student/project.html', context)

@logged_in
def project_upload_view(request, **kwargs):
    context = get_student_context(**kwargs)
    context.update(kwargs)
    context['form'] = FileUploadForm()
    # TODO load student's previous test results
    # Render list page with the documents and the form
    return render_to_response(
        'demograder/student/project_upload.html',
        context,
        context_instance=RequestContext(request)
    )

@logged_in
def project_submit_handler(request, **kwargs):
    context = get_student_context(**kwargs)
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

@logged_in
def result_view(request, **kwargs):
    context = get_student_context(**kwargs)
    print(context['result'].resultdependency_set.all())
    for dependency in context['result'].resultdependency_set.all():
        for upload in dependency.producer.upload_set.all():
            print(upload.id, upload.basename)
    return render(request, 'demograder/student/result.html', context)

@logged_in
def download_view(request, **kwargs):
    context = get_student_context(**kwargs)
    file_full_path = context['upload'].file.name
    with open(file_full_path) as fd:
        data = fd.read()
    response = HttpResponse(data, content_type=guess_type(file_full_path)[0])
    response['Content-Disposition'] = "attachment; filename={0}".format(basename(file_full_path))
    response['Content-Length'] = getsize(file_full_path)
    return response
