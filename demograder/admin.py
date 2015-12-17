from django.contrib import admin

# Register your models here.

from .models import Year
from .models import Department, Course
from .models import Student
from .models import Enrollment
from .models import Project, Submission
from .models import Upload

admin.site.register(Year)

admin.site.register(Department)

class CourseAdmin(admin.ModelAdmin):
    list_display = ('semester', 'catalog_id', 'title', 'students')
admin.site.register(Course, CourseAdmin)

class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'courses')
admin.site.register(Student, StudentAdmin)

admin.site.register(Enrollment)

admin.site.register(Project)

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('project', 'student', 'timestamp', 'uploads')
admin.site.register(Submission, SubmissionAdmin)

admin.site.register(Upload)
