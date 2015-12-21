from django.shortcuts import render, render_to_response

from .common import get_context

def get_instructor_context(**kwargs):
    context = get_context(**kwargs)
    # FIXME check permissions for course or redirect to home page
    # FIXME check permissions for project or redirect to home page
    # FIXME check permissions for submission or redirect to home page
    return context

def index_view(request, **kwargs):
    context = get_instructor_context(**kwargs)
    return render(request, 'demograder/instructor/index.html', context)
