from datetime import datetime
from os.path import basename, dirname, join as join_path

from django.contrib.auth.models import User
from django.db import models
from pytz import timezone

UPLOAD_PATH = 'uploads'

# Create your models here.

class Person(models.Model):
    class Meta:
        verbose_name_plural = 'People'
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    @property
    def name(self):
        return '{} {}'.format(self.user.first_name, self.user.last_name)
    @property
    def enrolled_course_set(self):
        return Course.objects.filter(enrollment__student=self)
    @property
    def enrolled_course_str(self):
        return ','.join(sorted(course.catalog_id for course in self.course_set.all()))
    def __str__(self):
        return self.user.username

def _current_year():
    return datetime.today().year

class Year(models.Model):
    value = models.IntegerField(default=_current_year, unique=True)
    def __str__(self):
        return str(self.value)

class Department(models.Model):
    name = models.CharField(max_length=200)
    catalog_code = models.CharField(max_length=10, unique=True)
    def __str__(self):
        return self.name

class Course(models.Model):
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
    course_number = models.IntegerField(default=0)
    title = models.CharField(max_length=200)
    class Meta:
        ordering = ('-year', 'season', 'department__catalog_code', 'course_number')
    @property
    def season_string(self):
        return self.SEASONS[self.season][1]
    @property
    def semester(self):
        return '{} {}'.format(self.year, self.season_string)
    @property
    def catalog_id(self):
        return '{} {}'.format(self.department.catalog_code, self.course_number)
    @property
    def projects(self):
        return ','.join(sorted(p.name for p in self.project_set.all()))
    @property
    def student_set(self):
        return Person.objects.filter(enrollment__course=self)
    @property
    def students(self):
        return ','.join(sorted(student.name for student in self.student_set))
        #return ','.join(self.student_set.values_list('student__name', flat=True).order_by('name'))
    def __str__(self):
        return '[{}] ({}) {}'.format(self.semester, self.catalog_id, self.title)

class Enrollment(models.Model):
    course = models.ForeignKey(Course)
    student = models.ForeignKey(Person)
    @property
    def semester(self):
        return self.course.semester

def _project_path(instance, filename):
    return join_path(instance.directory,
            'script',
            filename,
    )

class Project(models.Model):
    course = models.ForeignKey(Course)
    assignment = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    script = models.FileField(upload_to=_project_path, blank=True)
    filename = models.CharField(max_length=200)
    hidden = models.BooleanField(default=False)
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
    def __str__(self):
        return self.name

class Submission(models.Model):
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
    def score(self):
        return len(self.result_set.filter(return_code=0))
    @property
    def max_score(self):
        return len(self.result_set.all())
    @property
    def uploads_str(self):
        return ', '.join(sorted(u.file.name for u in self.upload_set.all()))
    @property
    def isoformat(self):
        return self.timestamp.astimezone(timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S')
    @property
    def us_format(self):
        return self.timestamp.astimezone(timezone('US/Pacific')).strftime('%b %d, %Y %I:%M:%S %p')
    def __str__(self):
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S") + self.student.user.username

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
    def timestamp(self):
        return self.submission.timestamp
    @property
    def project(self):
        return self.submission.project
    @property
    def student(self):
        return self.submission.student
    def __str__(self):
        return self.file.name

class Result(models.Model):
    submission = models.ForeignKey(Submission)
    stdout = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    return_code = models.IntegerField(null=True, blank=True)
    @property
    def submission_timestamp(self):
        return self.submission.timestamp
    @property
    def project(self):
        return self.submission.project
    @property
    def student(self):
        return self.submission.student

class ProjectDependency(models.Model):
    class Meta:
        verbose_name_plural = 'ProjectDependencies'
    project = models.ForeignKey(Project)
    producer = models.ForeignKey(Project, related_name='downstream_set')
    keyword = models.CharField(max_length=20)
    def __str__(self):
        return '{} <- {}'.format(self.project, self.producer)

class StudentDependency(models.Model):
    class Meta:
        verbose_name_plural = 'StudentDependencies'
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
    producer = models.ForeignKey(Submission, related_name='downstream_set')
