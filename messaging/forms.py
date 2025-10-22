from django import forms
from django.core.exceptions import ValidationError
from .models import Message

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body']
        widgets = {'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write a message...'})}

    def clean_body(self):
        body = (self.cleaned_data.get('body') or '').strip()
        if not body:
            raise ValidationError("Message cannot be empty.")
        if len(body) > 2000:
            raise ValidationError("Message is too long (max 2000 characters).")
        return body
