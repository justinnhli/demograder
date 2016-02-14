from collections import namedtuple

from .models import Submission

SubmissionDisplay = namedtuple('SubmissionDisplay', ('id', 'student', 'project', 'isoformat', 'score', 'max_score'))

def get_last_submissions(project):
    submissions = []
    for student in project.course.student_set.all():
        try:
            submission = Submission.objects.filter(student=student, project=project).latest('timestamp')
        except Submission.DoesNotExist:
            submission = SubmissionDisplay(0, student, project, 'N/A', 'N', 'A')
        submissions.append(submission)
    return submissions
