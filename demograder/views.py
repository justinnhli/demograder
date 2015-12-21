from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response, get_object_or_404
from django.template import RequestContext

from .forms import FileUploadForm
from .models import Course, Project, Submission, Student, Upload
from .dispatcher import dispatch_submission

def get_context(**kwargs):
    context = {}
    # FIXME get logged in student or redirect to log in
    context['student'] = Student.objects.get(email='justinnhli@oxy.edu')
    if 'submission_id' in kwargs:
        context['submission'] = get_object_or_404(Submission, id=kwargs['submission_id'])
    if 'submission' in context:
        context['project'] = context['submission'].project
    elif 'project_id' in kwargs:
        context['project'] = get_object_or_404(Project, id=kwargs['project_id'])
    if 'project' in context:
        context['course'] = context['project'].course
    elif 'course_id' in kwargs:
        context['course'] = get_object_or_404(Course, id=kwargs['course_id'])
    # FIXME check permissions for course or redirect to home page
    # FIXME check permissions for project or redirect to home page
    # FIXME check permissions for submission or redirect to home page
    return context

def index_view(request, **kwargs):
    context = get_context(**kwargs)
    return render(request, 'demograder/index.html', context)

def course_view(request, **kwargs):
    context = get_context(**kwargs)
    return render(request, 'demograder/course.html', context)

def project_view(request, **kwargs):
    context = get_context(**kwargs)
    submissions = Submission.objects.filter(project=context['project'], student=context['student'])
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

def project_upload_view(request, **kwargs):
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
    context = get_context(**kwargs)
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
