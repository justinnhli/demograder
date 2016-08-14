from django.contrib import admin

# Register your models here.

from .models import Year
from .models import Department, Course
from .models import Person
from .models import Enrollment
from .models import Assignment, Project
from .models import Submission, Upload, Result
from .models import ProjectDependency, StudentDependency, ResultDependency

admin.site.register(Year)

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'catalog_code')
admin.site.register(Department, DepartmentAdmin)

class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'semester_str', 'catalog_id_str', 'title')
admin.site.register(Course, CourseAdmin)

class PersonAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'full_name')
admin.site.register(Person, PersonAdmin)

class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'semester_str', 'title', 'username')
admin.site.register(Enrollment, EnrollmentAdmin)

class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'course', 'name', 'deadline')
admin.site.register(Assignment, AssignmentAdmin)

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'assignment', 'name', 'visible', 'locked')
admin.site.register(Project, ProjectAdmin)

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'student', 'iso_format', 'uploads_str')
admin.site.register(Submission, SubmissionAdmin)

class UploadAdmin(admin.ModelAdmin):
    list_display = ('id', 'iso_format', 'project', 'student', 'filename')
admin.site.register(Upload, UploadAdmin)

class ResultAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'submission_iso_format',
        'project',
        'student',
        'return_code',
    )
admin.site.register(Result, ResultAdmin)

class ProjectDependencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'producer')
admin.site.register(ProjectDependency, ProjectDependencyAdmin)

class StudentDependencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'student', 'producer')
admin.site.register(StudentDependency, StudentDependencyAdmin)

class ResultDependencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'result', 'producer')
admin.site.register(ResultDependency, ResultDependencyAdmin)
