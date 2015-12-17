from datetime import datetime
from os.path import join as join_path

from django.db import models

PROJECT_PATH = 'projects'
UPLOAD_PATH = 'uploads'

# Create your models here.

class Student(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField(primary_key=True)
    @property
    def courses(self):
        return ','.join(sorted(e.course.catalog_id for e in Enrollment.objects.filter(student__email=self.email)))
    def __str__(self):
        return self.name

def current_year():
    return datetime.today().year

class Year(models.Model):
    value = models.IntegerField(default=current_year, unique=True)
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
    def students(self):
        return ','.join(sorted(e.student.name for e in Enrollment.objects.filter(course=self)))
    def __str__(self):
        return '[{}] ({}) {}'.format(self.semester, self.catalog_id, self.title)

class Enrollment(models.Model):
    course = models.ForeignKey(Course)
    student = models.ForeignKey(Student)

def _project_path(instance, filename):
    return join_path(instance.directory,
            filename)

class Project(models.Model):
    course = models.ForeignKey(Course)
    name = models.CharField(max_length=200)
    script = models.FileField(upload_to=_project_path)
    @property
    def directory(self):
        context = (
            PROJECT_PATH, # root
            str(self.project.course.year), # year
            self.project.course.get_season_display(), # season
            self.project.course.department.catalog_code, # department
            str(self.project.course.course_number), # number
            str(self.project.id), # project
        )
        return join_path(*context)
    def __str__(self):
        return self.name

class Dependency(models.Model):
    consumer = models.ForeignKey(Project, related_name='consumers')
    producer = models.ForeignKey(Project, related_name='producers')

class Match(models.Model):
    dependency = models.ForeignKey(Dependency)
    consumer = models.ForeignKey(Student, related_name='consumers')
    producer = models.ForeignKey(Student, related_name='producers')

class Submission(models.Model):
    project = models.ForeignKey(Project)
    student = models.ForeignKey(Student)
    timestamp = models.DateTimeField(auto_now_add=True)
    @property
    def directory(self):
        return join_path(
                self.project.directory,
                'submissions',
                self.student.email[:self.student.email.find('@')],
        )
        return join_path(*context)
    @property
    def uploads(self):
        return '\n'.join(sorted(u.file.url for u in Upload.objects.filter(submission=self)))

def _upload_path(instance, filename):
    return join_path(instance.submission.directory,
            datetime.today().strftime('%Y%m%d%H%M%S%f'),
            filename)

class Upload(models.Model):
    submission = models.ForeignKey(Submission)
    file = models.FileField(upload_to=_upload_path)
