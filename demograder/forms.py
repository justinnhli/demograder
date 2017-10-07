from django import forms


class SubmissionUploadForm(forms.Form):

    def __init__(self, *args, **kwargs):
        assert 'project' in kwargs
        project = kwargs.pop('project')
        super().__init__(*args, **kwargs)
        for file_field, filename in zip(project.file_fields, project.filenames):
            self.fields[file_field] = forms.FileField(label=filename)
