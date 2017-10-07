from django import forms


class SubmissionUploadForm(forms.Form):

    def __init__(self, *args, **kwargs):
        has_filenames = ('filenames' in kwargs)
        if has_filenames:
            filenames = kwargs.pop('filenames')
        super().__init__(*args, **kwargs)
        if has_filenames:
            for i, filename in enumerate(filenames):
                file_field = 'file_{}'.format(i)
                self.fields[file_field] = forms.FileField(label=filename)
