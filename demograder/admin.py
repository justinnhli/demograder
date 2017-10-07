from django.contrib import admin

# Register your models here.

from .models import Year
from .models import Department, Course
from .models import Person
from .models import Enrollment
from .models import Assignment, Project, ProjectFile
from .models import Submission, Upload, Result
from .models import ProjectDependency, StudentDependency, ResultDependency


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'catalog_code')


class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'semester_str', 'catalog_id_str', 'title')


class PersonAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'full_name')


class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'semester_str', 'title', 'username')


class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'course', 'name', 'deadline')


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'assignment', 'name', 'visible', 'locked')


class ProjectFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'filename')


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'student', 'iso_format', 'uploads_str')


class UploadAdmin(admin.ModelAdmin):
    list_display = ('id', 'iso_format', 'project', 'student', 'filename')


class ResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'submission_iso_format', 'project', 'student', 'return_code')


class ProjectDependencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'producer')


class StudentDependencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'student', 'producer')


class ResultDependencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'result', 'producer')


admin.site.register(Year)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectFile, ProjectFileAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Upload, UploadAdmin)
admin.site.register(Result, ResultAdmin)
admin.site.register(ProjectDependency, ProjectDependencyAdmin)
admin.site.register(StudentDependency, StudentDependencyAdmin)
admin.site.register(ResultDependency, ResultDependencyAdmin)
