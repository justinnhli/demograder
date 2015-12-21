from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response, get_object_or_404

from ..models import Course, Project, Result, Person, Submission, Upload

def logged_in(fn):
    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Person.DoesNotExist as e:
            return HttpResponseRedirect(reverse('login'))
    return inner

def get_user_context(**kwargs):
    context = {}
    context['user'] = Person.objects.get(email='justinnhli@oxy.edu')
    return context

def get_context(**kwargs):
    context = get_user_context(**kwargs)
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
    return context

@logged_in
def index_view(request, **kwargs):
    context = get_context(**kwargs)
    return render(request, 'demograder/index.html')

def login_view(request, **kwargs):
    return render(request, 'demograder/login.html')
