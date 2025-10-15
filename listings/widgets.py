from django.forms.widgets import FileInput

class MultipleFileInput(FileInput):
    allow_multiple_selected = True
