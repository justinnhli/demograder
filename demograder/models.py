from datetime import datetime, timedelta
from os.path import basename, dirname, join as join_path

from django.contrib.auth.models import User
from django.db import models
from django.db.models.functions import Lower
from pytz import timezone, UTC

UPLOAD_PATH = 'uploads'

# Create your models here.


class Person(models.Model):

    class Meta:
        ordering = (
            'user__last_name',
            'user__first_name',
        )
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
        return Course.objects.filter(instructor=self).order_by(
            '-year__value', '-season', 'department__catalog_code', 'course_number'
        )

    def enrolled_courses(self):
        return Course.objects.filter(enrollment__student=self).order_by(
            '-year__value', '-season', 'department__catalog_code', 'course_number'
        )

    def get_assignment_score(self, assignment):
        total = 0
        num_projects = 0
        for project in Project.objects.filter(assignment=assignment, visible=True):
            num_projects += 1
            submission = self.latest_submission(project)
            if submission and submission.max_score > 0:
                total += submission.score / submission.max_score
        if num_projects == 0:
            return 0
        else:
            return total / num_projects

    def submissions(self, project=None):
        if project:
            return Submission.objects.filter(student=self, project=project)
        else:
            return Submission.objects.filter(student=self)

    def latest_submission(self, project=None):
        submissions = self.submissions(project=project)
        if submissions:
            return submissions.latest()
        else:
            return None

    def may_submit(self, project):
        """Determines if the student is allowed to submit to a project

        The motivation behind stopping student submissions is to prevent
        overloading the system, and (in theory) to instill a more thorough
        manual debugging process. This means there are three trivial cases when
        the student can submit:

        * they are a superuser
        * they have not submitted anything before
        * this project does not have testcases

        If they are not a superuser, have previous submissions, and is trying to
        submit to a project with testcases, then all of the following must be
        true for the student to submit:

        * the project is not locked
        * all their previous submissions for all projects have finished running
        * 300 seconds has passed since their last submission to this project

        This function returns different string constants to reflect which of the
        above two conditions have been violated, so that an appropriate error
        can be displayed.

        Args:
            project (Project): the project to determine submission status for

        Returns:
            string: one of three string constants
                'yes': the student may submit again
                'locked': the project is locked
                'submission': the student is blocked by their last submission
                'timeout': it has been less than 300 seconds since their last
                           submission to this project
        """

        if self.user.is_superuser:
            return 'yes'
        if project.locked:
            return 'locked'
        submissions = self.submissions()
        if not submissions:
            return 'yes'
        if self.latest_submission().num_tbd != 0:
            return 'submission'
        if not project.upstream_dependencies():
            return 'yes'
        submissions = self.submissions(project=project)
        if submissions:
            last_submission = submissions.latest()
            current_time = UTC.normalize(datetime.now(last_submission.timestamp.tzinfo))
            submit_time = UTC.normalize(last_submission.timestamp)
            if last_submission and current_time - submit_time < timedelta(seconds=300):
                return 'timeout'
        return 'yes'

    def __str__(self):
        # human readable, used by Django admin displays
        return '{} {} ({})'.format(self.first_name, self.last_name, self.username)


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
        ordering = (
            '-year__value',
            '-season',
            'department',
            'course_number',
        )

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
    year = models.ForeignKey(Year, on_delete=models.CASCADE)
    season = models.IntegerField(choices=SEASONS)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    course_number = models.IntegerField()
    title = models.CharField(max_length=200)
    instructor = models.ForeignKey(Person, on_delete=models.CASCADE)

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
        return Person.objects.filter(enrollment__course=self).order_by(Lower('last_name'))

    def assignments(self):
        return Assignment.objects.filter(course=self)

    def projects(self):
        return Project.objects.filter(assignment__course=self)

    def __str__(self):
        # human readable, used by Django admin displays
        return self.semester_str + ' ' + self.catalog_id_str


class Enrollment(models.Model):

    class Meta:
        unique_together = (
            'course',
            'student',
        )

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey(Person, on_delete=models.CASCADE)

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

    def __str__(self):
        # human readable, used by Django admin displays
        return str(self.student) + ' in ' + str(self.course)


class Assignment(models.Model):

    class Meta:
        ordering = ('-deadline',)
        unique_together = ('course', 'name')

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    deadline = models.DateTimeField()

    @property
    def iso_format(self):
        return self.deadline.astimezone(timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M')

    @property
    def us_format(self):
        return self.deadline.astimezone(timezone('US/Pacific')).strftime('%b %d, %Y %I:%M:%S %p').replace(' 0', ' ')

    def projects(self):
        return Project.objects.filter(assignment=self)

    def has_visible_projects(self):
        return any(project.visible for project in self.projects())

    def __str__(self):
        # human readable, used by Django admin displays
        return '({}) {}'.format(self.course, self.name)


def _project_path(instance, filename):
    return join_path(instance.directory, 'script', filename)


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
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    timeout = models.IntegerField(default=5)
    submission_type = models.IntegerField(choices=SUBMISSION_TYPES)
    script = models.FileField(upload_to=_project_path, blank=True, max_length=500)
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

    @property
    def files(self):
        return ProjectFile.objects.filter(project=self)

    @property
    def file_fields(self):
        return ['file_{}'.format(i) for i in range(ProjectFile.objects.filter(project=self).count())]

    @property
    def filenames(self):
        return [project_file.filename for project_file in ProjectFile.objects.filter(project=self)]

    def upstream_dependencies(self):
        return ProjectDependency.objects.filter(project=self)

    def downstream_dependencies(self):
        return ProjectDependency.objects.filter(producer=self)

    def __str__(self):
        # human readable, used by Django admin displays
        return '{}: {}'.format(self.assignment, self.name)


class ProjectDependency(models.Model):

    class Meta:
        unique_together = ('project', 'producer')
        verbose_name_plural = 'ProjectDependencies'

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
    producer = models.ForeignKey(Project, related_name='downstream_set', on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    dependency_structure = models.IntegerField(choices=DEPENDENCY_TYPES)
    keyword = models.CharField(max_length=20)

    def __str__(self):
        return '({} {}) {} --> {}'.format(
            self.project.assignment.course, self.project.assignment.name, self.producer.name, self.project.name
        )


class ProjectFile(models.Model):

    class Meta:
        ordering = ('project', 'filename')
        unique_together = ('project', 'filename')
        verbose_name_plural = 'ProjectFiles'

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    filename = models.CharField(max_length=50)

    def __str__(self):
        return self.filename


class Submission(models.Model):

    class Meta:
        get_latest_by = 'timestamp'
        ordering = ('-timestamp',)

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    student = models.ForeignKey(Person, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    @property
    def course(self):
        return self.project.assignment.course

    @property
    def assignment(self):
        return self.project.assignment

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
    def score_str(self):
        return '{}/{}'.format(self.score, self.max_score)

    @property
    def uploads_str(self):
        return ', '.join(sorted(u.file.name for u in self.upload_set.all()))

    @property
    def iso_format(self):
        return self.timestamp.astimezone(timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S')

    @property
    def us_format(self):
        return self.timestamp.astimezone(timezone('US/Pacific')).strftime('%b %d, %Y %I:%M:%S %p').replace(' 0', ' ')

    def uploads(self):
        return Upload.objects.filter(submission=self)


def _upload_path(instance, filename):
    return join_path(instance.submission.directory, filename)


class Upload(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    project_file = models.ForeignKey(ProjectFile, on_delete=models.CASCADE)
    file = models.FileField(upload_to=_upload_path, max_length=500)

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
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    stdout = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    return_code = models.IntegerField(null=True, blank=True)

    @property
    def course(self):
        return self.submission.project.assignment.course

    @property
    def assignment(self):
        return self.submission.project.assignment

    @property
    def project(self):
        return self.submission.project

    @property
    def student(self):
        return self.submission.student

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
        return self.timestamp.astimezone(timezone('US/Pacific')).strftime('%b %d, %Y %I:%M:%S %p').replace(' 0', ' ')

    @property
    def is_tbd(self):
        return self.return_code is None

    @property
    def passed(self):
        return self.return_code == 0

    @property
    def failed(self):
        return not self.passed


class StudentDependency(models.Model):

    class Meta:
        unique_together = ('student', 'dependency', 'producer')
        verbose_name_plural = 'StudentDependencies'

    student = models.ForeignKey(Person, on_delete=models.CASCADE)
    dependency = models.ForeignKey(ProjectDependency, on_delete=models.CASCADE)
    producer = models.ForeignKey(Person, related_name='downstream_set', on_delete=models.CASCADE)

    @property
    def project(self):
        return self.dependency.project


class ResultDependency(models.Model):

    class Meta:
        verbose_name_plural = 'ResultDependencies'

    result = models.ForeignKey(Result, on_delete=models.CASCADE)
    project_dependency = models.ForeignKey(ProjectDependency, on_delete=models.CASCADE)
    producer = models.ForeignKey(Submission, related_name='downstream_set', on_delete=models.CASCADE)
