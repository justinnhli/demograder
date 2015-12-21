from django.contrib import admin

# Register your models here.

from .models import Year
from .models import Department, Course
from .models import Person
from .models import Enrollment, Offering
from .models import Project
from .models import Submission, Upload, Result
from .models import ProjectDependency, StudentDependency, ResultDependency

admin.site.register(Year)

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'catalog_code')
admin.site.register(Department, DepartmentAdmin)

class CourseAdmin(admin.ModelAdmin):
    list_display = ('semester', 'catalog_id', 'title', 'students')
admin.site.register(Course, CourseAdmin)

class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')
admin.site.register(Person, PersonAdmin)

class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('semester', 'course', 'student')
admin.site.register(Enrollment, EnrollmentAdmin)

class OfferingAdmin(admin.ModelAdmin):
    list_display = ('semester', 'course', 'instructor')
admin.site.register(Offering, OfferingAdmin)

admin.site.register(Project)

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('project', 'student', 'timestamp', 'uploads_str')
admin.site.register(Submission, SubmissionAdmin)

class UploadAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'project', 'student', 'filename')
admin.site.register(Upload, UploadAdmin)

class ResultAdmin(admin.ModelAdmin):
    list_display = (
        'submission_timestamp',
        'project',
        'student',
        'return_code',
    )
admin.site.register(Result, ResultAdmin)

admin.site.register(ProjectDependency)

class StudentDependencyAdmin(admin.ModelAdmin):
    list_display = ('project', 'student', 'producer')
admin.site.register(StudentDependency, StudentDependencyAdmin)

admin.site.register(ResultDependency)
