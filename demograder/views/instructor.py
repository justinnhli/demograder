import re

from django.shortcuts import render, render_to_response
from django.utils.decorators import method_decorator
from django.views.generic.base import ContextMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from ..models import Course

from .common import get_context, logged_in

def split_at_upper(string):
    return re.sub(r'([A-Z])', r' \1', string).split()

def get_instructor_context(**kwargs):
    context = get_context(**kwargs)
    # FIXME check permissions for course or redirect to home page
    # FIXME check permissions for project or redirect to home page
    # FIXME check permissions for submission or redirect to home page
    return context

@logged_in
def index_view(request, **kwargs):
    context = get_instructor_context(**kwargs)
    return render(request, 'demograder/instructor/index.html', context)

class InstructorMixin(ContextMixin):
    SUBMIT_VERB = {
        'Create': 'Create',
        'Edit': 'Save',
        'Delete': 'Delete',
    }
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_context(**kwargs))
        context['form_object_type'] = self.model.__name__
        context['form_title_verb'] = split_at_upper(type(self).__name__)[-1]
        context['form_submit_verb'] = InstructorMixin.SUBMIT_VERB[split_at_upper(type(self).__name__)[-1]]
        return context

@method_decorator(logged_in, name='dispatch')
class CourseCreate(CreateView, InstructorMixin):
    model = Course
    template_name = 'demograder/instructor/course_form.html'
    fields = ['year', 'season', 'department', 'course_number', 'title']

@method_decorator(logged_in, name='dispatch')
class CourseEdit(UpdateView, InstructorMixin):
    model = Course
    template_name = 'demograder/instructor/course_form.html'
    fields = ['year', 'season', 'department', 'course_number', 'title']
    pk_url_kwarg = 'course_id'

@method_decorator(logged_in, name='dispatch')
class CourseDelete(DeleteView, InstructorMixin):
    model = Course
    template_name = 'demograder/instructor/course_form.html'
    fields = ['year', 'season', 'department', 'course_number', 'title']
    pk_url_kwarg = 'course_id'

@logged_in
def course_view(request, **kwargs):
    context = get_instructor_context(**kwargs)
    return render(request, 'demograder/instructor/course.html', context)
