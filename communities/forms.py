"""
Forms for communities app.
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import Community, CommunityMember, Post, Comment, ChatMessage, Event


class MultipleFileInput(forms.ClearableFileInput):
    """Custom widget to allow multiple file uploads"""

    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Custom field to handle multiple file uploads"""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class CommunityForm(forms.ModelForm):
    """Form for creating and editing communities."""

    class Meta:
        model = Community
        fields = ["name", "description", "privacy", "university", "cover_image"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Community Name",
                    "maxlength": "100",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Describe your community...",
                    "rows": 4,
                    "maxlength": "1000",
                }
            ),
            "privacy": forms.Select(attrs={"class": "form-control"}),
            "university": forms.Select(attrs={"class": "form-control"}),
            "cover_image": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
        }
        help_texts = {
            "name": "Choose a unique name for your community (max 100 characters)",
            "description": "Describe what your community is about (max 1000 characters)",
            "privacy": "Public: Anyone can join | Private: Requires approval | University: Restricted to university students",
            "university": "Required for university-restricted communities",
            "cover_image": "Optional: Upload a cover image for your community",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make university field not required by default (will validate in clean())
        self.fields["university"].required = False
        self.fields["cover_image"].required = False

    def clean(self):
        """Validate that university is set for university-restricted communities."""
        cleaned_data = super().clean()
        # Note: Validation is also done in the model's clean() method
        # We rely on model validation instead of duplicating it here
        return cleaned_data


class JoinRequestForm(forms.ModelForm):
    """Form for requesting to join a private community."""

    class Meta:
        model = CommunityMember
        fields = ["request_message"]
        widgets = {
            "request_message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Tell us why you want to join this community (optional)...",
                    "rows": 3,
                    "maxlength": "500",
                }
            )
        }
        help_texts = {
            "request_message": "Optional: Add a message with your join request (max 500 characters)"
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["request_message"].required = False


class PostForm(forms.ModelForm):
    """Form for creating and editing community posts."""

    # Multiple image uploads
    images = MultipleFileField(
        required=False, help_text="Optional: Upload up to 5 images"
    )

    # Multiple file uploads
    files = MultipleFileField(
        required=False, help_text="Optional: Attach files (PDF, docs, etc.)"
    )

    class Meta:
        model = Post
        fields = ["title", "content"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Post Title (optional)",
                    "maxlength": "200",
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "What would you like to share?",
                    "rows": 6,
                    "maxlength": "10000",
                }
            ),
        }
        help_texts = {
            "title": "Optional: Add a title to your post (max 200 characters)",
            "content": "Share your thoughts with the community (max 10,000 characters)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].required = False


class CommentForm(forms.ModelForm):
    """Form for creating and editing comments."""

    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Write a comment...",
                    "rows": 3,
                    "maxlength": "2000",
                }
            )
        }
        help_texts = {"content": "Max 2,000 characters"}


class ChatMessageForm(forms.ModelForm):
    """Form for sending chat messages in community threads."""

    class Meta:
        model = ChatMessage
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "form-control chat-input",
                    "placeholder": "Type your message...",
                    "rows": 2,
                    "maxlength": "2000",
                    "id": "chat-message-input",
                }
            )
        }
        help_texts = {"content": "Max 2,000 characters"}


class EventForm(forms.ModelForm):
    """Form for creating and editing community events."""

    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "start_datetime",
            "end_datetime",
            "location",
            "location_details",
            "latitude",
            "longitude",
            "cover_image",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Event title",
                    "maxlength": "200",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Describe your event...",
                    "rows": 5,
                    "maxlength": "2000",
                }
            ),
            "start_datetime": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "end_datetime": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Event location (address, venue name, etc.)",
                    "maxlength": "300",
                }
            ),
            "location_details": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Additional location details (room number, landmarks, parking info, etc.)",
                    "rows": 3,
                    "maxlength": "500",
                }
            ),
            "latitude": forms.HiddenInput(attrs={"id": "id_latitude"}),
            "longitude": forms.HiddenInput(attrs={"id": "id_longitude"}),
            "cover_image": forms.FileInput(attrs={"class": "form-control"}),
        }
        help_texts = {
            "title": "Max 200 characters",
            "description": "Max 2,000 characters",
            "location_details": "Optional. Max 500 characters",
            "cover_image": "Optional event cover image",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert datetime fields from UTC to local timezone for display
        from django.utils import timezone

        if self.instance and self.instance.pk:
            # When editing an existing event, convert UTC to local time
            if self.instance.start_datetime:
                local_start = timezone.localtime(self.instance.start_datetime)
                self.initial['start_datetime'] = local_start.strftime('%Y-%m-%dT%H:%M')
            if self.instance.end_datetime:
                local_end = timezone.localtime(self.instance.end_datetime)
                self.initial['end_datetime'] = local_end.strftime('%Y-%m-%dT%H:%M')

    def clean(self):
        """Validate that end_datetime is after start_datetime and both are in the future"""
        cleaned_data = super().clean()
        start = cleaned_data.get("start_datetime")
        end = cleaned_data.get("end_datetime")

        if start and end:
            # Validate that event times are in the future
            from django.utils import timezone

            if start < timezone.now():
                raise ValidationError(
                    {"start_datetime": "Event cannot start in the past."}
                )

            if end < timezone.now():
                raise ValidationError(
                    {"end_datetime": "Event cannot end in the past."}
                )

            if end <= start:
                raise ValidationError(
                    {"end_datetime": "End time must be after start time."}
                )

        return cleaned_data
