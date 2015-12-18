from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views import generic

from .forms import FileUploadForm
from .models import Course, Project, Submission, Student, Upload

# Create your views here.

class ParameterListView(generic.ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.kwargs)
        return context

class CourseListView(ParameterListView):
    model = Course
    def get_queryset(self):
        return Course.objects.all().order_by('-year', 'season', 'department__catalog_code', 'course_number')

class ProjectListView(ParameterListView):
    model = Project
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = Course.objects.get(id=self.kwargs['course_id'])
        return context
    def get_queryset(self):
        return Project.objects.filter(course=self.kwargs['course_id'])

def submit_project(request, **kwargs):
    project = Project.objects.get(id=kwargs['project_id'])
    course = project.course
    # FIXME authenticate somehow
    student = Student.objects.get(email='justinnhli@oxy.edu')
    # TODO check student is in course
    # Handle file upload
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # TODO check that student is in course
            submission = Submission(
                    project=project,
                    student=student,
            )
            submission.save()
            upload = Upload(
                    submission=submission,
                    file=request.FILES['file'],
            )
            upload.save()
            # TODO submit process to rq
            # find combination of all dependent files and submission
            return HttpResponseRedirect(reverse('Project Status View', kwargs=kwargs))
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
        'demograder/submit_project.html',
        context,
        context_instance=RequestContext(request)
    )
