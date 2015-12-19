from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.template import RequestContext

from .forms import FileUploadForm
from .models import Course, Project, Submission, Student, Upload
from .dispatcher import dispatch_submission

def get_student_context(**kwargs):
    # FIXME get logged in student
    context = {}
    context['student'] = Student.objects.get(email='justinnhli@oxy.edu')
    return context

def index_view(request, **kwargs):
    context = get_student_context(**kwargs)
    return render(request, 'demograder/index.html', context)

def course_view(request, **kwargs):
    context = get_student_context(**kwargs)
    context['course'] = Course.objects.get(id=kwargs['course_id'])
    return render(request, 'demograder/course.html', context)

def project_view(request, **kwargs):
    context = get_student_context(**kwargs)
    context['project'] = Project.objects.get(id=kwargs['project_id'])
    return render(request, 'demograder/project.html', context)

def project_submit_view(request, **kwargs):
    project = Project.objects.get(id=kwargs['project_id'])
    course = project.course
    # FIXME authenticate somehow
    student = Student.objects.get(email='justinnhli@oxy.edu')
    # FIXME check student is in course
    # Handle file upload
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            submission = Submission(
                    project=project,
                    student=student,
            )
            submission.save()
            # TODO handle multiple files per submission
            upload = Upload(
                    submission=submission,
                    file=request.FILES['file'],
            )
            upload.save()
            # TODO submit process to rq
            # find combination of all dependent files and submission
            dispatch_submission(student, project, submission)
            return HttpResponseRedirect(reverse('course', kwargs=kwargs))
    else:
        form = FileUploadForm()
    # Collect context
    context = {}
    context.update(kwargs)
    context['form'] = form
    # TODO load student's previous test results
    context['course'] = course
    context['project'] = project
    context['student'] = student
    # Render list page with the documents and the form
    return render_to_response(
        'demograder/project_submit.html',
        context,
        context_instance=RequestContext(request)
    )
