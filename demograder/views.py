from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.template import RequestContext

from .forms import FileUploadForm
from .models import Course, Project, Submission, Student, Upload
from .dispatcher import dispatch_submission

def get_context(**kwargs):
    context = {}
    # FIXME get logged in student or redirect to log in
    context['student'] = Student.objects.get(email='justinnhli@oxy.edu')
    if 'submission_id' in kwargs:
        context['submission'] = Submission.objects.get(id=kwargs['submission_id'])
    if 'submission' in context:
        context['project'] = context['submission'].project
    elif 'project_id' in kwargs:
        context['project'] = Project.objects.get(id=kwargs['project_id'])
    if 'project' in context:
        context['course'] = context['project'].course
    elif 'course_id' in kwargs:
        context['course'] = Course.objects.get(id=kwargs['course_id'])
    # FIXME check permissions or redirect to home page
    return context

def index_view(request, **kwargs):
    context = get_context(**kwargs)
    return render(request, 'demograder/index.html', context)

def course_view(request, **kwargs):
    context = get_context(**kwargs)
    return render(request, 'demograder/course.html', context)

def project_view(request, **kwargs):
    context = get_context(**kwargs)
    if Submission.objects.filter(project=context['project'],student=context['student']).exists():
        context['submissions'] = Submission.objects.filter(project=context['project'],student=context['student']).order_by('-timestamp')
        context['submission'] = Submission.objects.filter(project=context['project'],student=context['student']).latest('timestamp')
    else:
        context['submissions'] = []
        context['submission'] = None
    context['most_recent'] = True
    return render(request, 'demograder/project.html', context)

def project_upload_view(request, **kwargs):
    # Collect context
    context = get_context(**kwargs)
    context.update(kwargs)
    context['form'] = FileUploadForm()
    # TODO load student's previous test results
    # Render list page with the documents and the form
    return render_to_response(
        'demograder/project_upload.html',
        context,
        context_instance=RequestContext(request)
    )

def project_submit_handler(request, **kwargs):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('project', kwargs=kwargs))
    # Handle file upload
    form = FileUploadForm(request.POST, request.FILES)
    if form.is_valid():
        submission = Submission(
                project=context['project'],
                student=context['student'],
        )
        submission.save()
        # TODO handle multiple files per submission
        upload = Upload(
                submission=submission,
                file=request.FILES['file'],
        )
        upload.save()
        # find combination of all dependent files and submission and submit to RQ
        dispatch_submission(context['student'], context['project'], submission)
    return HttpResponseRedirect(reverse('project', kwargs=kwargs))

def submission_view(request, **kwargs):
    if context['submission'] == Submission.objects.filter(student=context['student']).latest('timestamp'):
        return HttpResponseRedirect(reverse('project', kwargs={'project_id':context['project'].id}))
    context['submissions'] = Submission.objects.filter(student=context['student']).order_by('-timestamp')
    context['most_recent'] = False
    return render(request, 'demograder/project.html', context)
