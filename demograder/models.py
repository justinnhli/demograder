from datetime import datetime
from os.path import basename, dirname, join as join_path

from django.contrib.auth.models import User
from django.db import models
from pytz import timezone

UPLOAD_PATH = 'uploads'

# Create your models here.

class Person(models.Model):
    class Meta:
        ordering = ('user__last_name', 'user__first_name',)
        verbose_name_plural = 'People'
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    @property
    def username(self):
        return self.user.username
    @property
    def full_name(self):
        return '{} {}'.format(self.user.first_name, self.user.last_name)
    @property
    def first_name(self):
        return self.user.first_name
    @property
    def last_name(self):
        return self.user.last_name
    def instructing_courses(self):
        return Course.objects.filter(instructor=self)
    def enrolled_courses(self):
        return Course.objects.filter(enrollment__student=self)
    def submissions(self):
        return Submission.objects.filter(student=self)
    def latest_submission(self)
        return Submission.objects.filter(student=self).latest()
    def may_submit(self):
        return (self.latest_submission.num_tbd == 0)
    def __str__(self):
        # human readable, used by Django admin displays
        return self.username

def _current_year():
    return datetime.today().year

class Year(models.Model):
    value = models.IntegerField(default=_current_year, unique=True)
    def __str__(self):
        # human readable, used by Django admin displays
        return str(self.value)

class Department(models.Model):
    class Meta:
        ordering = ('name',)
    name = models.CharField(max_length=200)
    catalog_code = models.CharField(max_length=10, unique=True)
    def __str__(self):
        # human readable, used by Django admin displays
        return self.name

class Course(models.Model):
    class Meta:
        ordering = ('-year', '-season', 'department', 'course_number',)
    WINTER = 0
    SPRING = 1
    SUMMER = 2
    FALL = 3
    SEASONS = (
            (WINTER, 'Winter'),
            (SPRING, 'Spring'),
            (SUMMER, 'Summer'),
            (FALL, 'Fall'),
    )
    year = models.ForeignKey(Year)
    season = models.IntegerField(choices=SEASONS)
    department = models.ForeignKey(Department)
    course_number = models.IntegerField()
    title = models.CharField(max_length=200)
    instructor = models.ForeignKey(Person)
    @property
    def season_str(self):
        return self.SEASONS[self.season][1]
    @property
    def semester_str(self):
        return '{} {}'.format(self.season_str, self.year)
    @property
    def catalog_id_str(self):
        return '{} {}'.format(self.department.catalog_code, self.course_number)
    def enrolled_students(self):
        return Person.objects.filter(enrollment__course=self)
    def assignments(self):
        return Assignment.objects.filter(course=self)
    def __str__(self):
        # human readable, used by Django admin displays
        return self.semester_str + ' ' + self.catalog_id_str

class Enrollment(models.Model):
    class Meta:
        unique_together = ('course', 'student',)
    course = models.ForeignKey(Course)
    student = models.ForeignKey(Person)
    @property
    def semester_str(self):
        return self.course.semester_str
    @property
    def title(self):
        return self.course.title
    @property
    def username(self):
        return self.student.username
    @property
    def full_name(self):
        return self.student.full_name
    @property
    def first_name(self):
        return self.student.first_name
    @property
    def last_name(self):
        return self.student.last_name

class Assignment(models.Model):
    class Meta:
        ordering = ('-deadline',)
        unique_together = ('course', 'name')
    course = models.ForeignKey(Course)
    name = models.CharField(max_length=200)
    deadline = models.DateTimeField()
    @property
    def iso_format(self):
        return self.deadline.astimezone(timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M')
    @property
    def us_format(self):
        return self.deadline.astimezone(timezone('US/Pacific')).strftime('%b %d, %Y %I:%M %p')
    def projects(self):
        return Project.objects.filter(assignment=self)
    def __str__(self):
        # human readable, used by Django admin displays
        return '({}) {}'.format(self.course, self.name)

def _project_path(instance, filename):
    return join_path(instance.directory,
            'script',
            filename,
    )

class Project(models.Model):
    class Meta:
        ordering = ('assignment', 'name')
        unique_together = ('assignment', 'name')
    LATEST = 0
    ALL = 1
    MULTIPLE = 2
    SUBMISSION_TYPES = (
            (LATEST, 'Latest'),
            (ALL, 'All'),
            (MULTIPLE, 'Student Selected'),
    )
    assignment = models.ForeignKey(Assignment)
    name = models.CharField(max_length=200)
    filename = models.CharField(max_length=200)
    timeout = models.IntegerField(default=5)
    submission_type = models.IntegerField(choices=SUBMISSION_TYPES)
    script = models.FileField(upload_to=_project_path, blank=True)
    visible = models.BooleanField(default=False)
    locked = models.BooleanField(default=False)
    @property
    def course(self):
        return self.assignment.course
    @property
    def deadline(self):
        return self.assignment.deadline
    @property
    def directory(self):
        context = (
            UPLOAD_PATH, # root
            str(self.course.year), # year
            self.course.get_season_display(), # season
            self.course.department.catalog_code, # department
            str(self.course.course_number), # number
            str(self.id), # project
        )
        return join_path(*context)
    def upstream_dependencies(self):
        return ProjectDependency.objects.filter(project=self)
    def downstream_dependencies(self):
        return ProjectDependency.objects.filter(producer=self)
    def __str__(self):
        # human readable, used by Django admin displays
        return '{}: {}'.format(self.assignment, self.name)

class ProjectDependency(models.Model):
    class Meta:
        verbose_name_plural = 'ProjectDependencies'
        unique_together = ('project', 'producer')
    SELF = 0
    INSTRUCTOR = 1
    CLIQUE = 2
    CUSTOM = 3
    DEPENDENCY_TYPES = (
        (SELF, 'Self'),
        (INSTRUCTOR, 'All to Instructor'),
        (CLIQUE, 'All to All'),
        (CUSTOM, 'Custom Groups'),
    )
    producer = models.ForeignKey(Project, related_name='downstream_set')
    project = models.ForeignKey(Project)
    dependency_structure = models.IntegerField(choices=DEPENDENCY_TYPES)
    keyword = models.CharField(max_length=20)
    def __str__(self):
        return '({} {}) {} --> {}'.format(
                self.project.assignment.course,
                self.project.assignment.name,
                self.producer.name,
                self.project.name)

class Submission(models.Model):
    class Meta:
        get_latest_by = 'timestamp'
        ordering = ('-timestamp',)
    project = models.ForeignKey(Project)
    student = models.ForeignKey(Person)
    timestamp = models.DateTimeField(auto_now_add=True)
    @property
    def directory(self):
        return join_path(
                self.project.directory,
                'submissions',
                self.student.user.username,
                datetime.today().strftime('%Y%m%d%H%M%S%f'),
        )
    @property
    def num_passed(self):
        return len(self.result_set.filter(return_code=0))
    @property
    def num_failed(self):
        return len(self.result_set.exclude(return_code=0).exclude(return_code__isnull=True))
    @property
    def num_tbd(self):
        return len(self.result_set.filter(return_code__isnull=True))
    @property
    def score(self):
        return self.num_passed
    @property
    def max_score(self):
        return self.num_passed + self.num_failed + self.num_tbd
    @property
    def uploads_str(self):
        return ', '.join(sorted(u.file.name for u in self.upload_set.all()))
    @property
    def iso_format(self):
        return self.timestamp.astimezone(timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S')
    @property
    def us_format(self):
        return self.timestamp.astimezone(timezone('US/Pacific')).strftime('%b %d, %Y %I:%M:%S %p')
    def uploads(self):
        return Upload.objects.filter(submission=self)

def _upload_path(instance, filename):
    return join_path(instance.submission.directory, instance.submission.project.filename)

class Upload(models.Model):
    submission = models.ForeignKey(Submission)
    file = models.FileField(upload_to=_upload_path)
    @property
    def dirname(self):
        return dirname(self.file.name)
    @property
    def basename(self):
        return basename(self.file.name)
    @property
    def filename(self):
        return self.file.name
    @property
    def iso_format(self):
        return self.submission.iso_format
    @property
    def us_format(self):
        return self.submission.us_format
    @property
    def project(self):
        return self.submission.project
    @property
    def student(self):
        return self.submission.student

class Result(models.Model):
    submission = models.ForeignKey(Submission)
    timestamp = models.DateTimeField(auto_now_add=True)
    stdout = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    return_code = models.IntegerField(null=True, blank=True)
    @property
    def submission_iso_format(self):
        return self.submission.iso_format
    @property
    def submission_us_format(self):
        return self.submission.us_format
    @property
    def result_iso_format(self):
        return self.timestamp.astimezone(timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S')
    @property
    def result_us_format(self):
        return self.timestamp.astimezone(timezone('US/Pacific')).strftime('%b %d, %Y %I:%M:%S %p')
    @property
    def project(self):
        return self.submission.project
    @property
    def student(self):
        return self.submission.student

class StudentDependency(models.Model):
    class Meta:
        verbose_name_plural = 'StudentDependencies'
        unique_together = ('student', 'dependency', 'producer')
    student = models.ForeignKey(Person)
    dependency = models.ForeignKey(ProjectDependency)
    producer = models.ForeignKey(Person, related_name='downstream_set')
    @property
    def project(self):
        return self.dependency.project

class ResultDependency(models.Model):
    class Meta:
        verbose_name_plural = 'ResultDependencies'
    result = models.ForeignKey(Result)
    project_dependency = models.ForeignKey(ProjectDependency)
    producer = models.ForeignKey(Submission, related_name='downstream_set')
