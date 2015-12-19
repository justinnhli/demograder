from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.template import RequestContext

from .forms import FileUploadForm
from .models import Course, Project, Submission, Student, Upload
from .dispatcher import dispatch_submission

# FIXME this should become a hierarchy of views
# Student > Course > Project
# so they can call each other's get_context_data()

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
    context['submissions'] = Submission.objects.filter(student=context['student']).order_by('-timestamp')
    context['submission'] = Submission.objects.filter(student=context['student']).order_by('timestamp').latest('timestamp')
    context['most_recent'] = True
    return render(request, 'demograder/project.html', context)

def project_upload_view(request, **kwargs):
    project = Project.objects.get(id=kwargs['project_id'])
    course = project.course
    # FIXME authenticate somehow
    student = Student.objects.get(email='justinnhli@oxy.edu')
    # FIXME check student is in course
    # Collect context
    context = get_student_context(**kwargs)
    context.update(kwargs)
    context['form'] = FileUploadForm()
    # TODO load student's previous test results
    context['course'] = course
    context['project'] = project
    # Render list page with the documents and the form
    return render_to_response(
        'demograder/project_upload.html',
        context,
        context_instance=RequestContext(request)
    )

def project_submit_handler(request, **kwargs):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('project', kwargs=kwargs))
    project = Project.objects.get(id=kwargs['project_id'])
    course = project.course
    # FIXME authenticate somehow
    student = Student.objects.get(email='justinnhli@oxy.edu')
    # FIXME check student is in course
    # Handle file upload
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
        # find combination of all dependent files and submission and submit to RQ
        dispatch_submission(student, project, submission)
        return HttpResponseRedirect(reverse('project', kwargs=kwargs))
    return HttpResponseRedirect(reverse('project', kwargs=kwargs))

def submission_view(request, **kwargs):
    context = get_student_context(**kwargs)
    context['submission'] = Submission.objects.get(id=kwargs['submission_id'])
    context['project'] = context['submission'].project
    if context['submission'] == Submission.objects.filter(student=context['student']).order_by('timestamp').latest('timestamp'):
        return HttpResponseRedirect(reverse('project', kwargs={'project_id':context['project'].id}))
    context['submissions'] = Submission.objects.filter(student=context['student']).order_by('-timestamp')
    context['most_recent'] = False
    return render(request, 'demograder/project.html', context)
