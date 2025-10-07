from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'university', 'profile_photo', 'visibility']
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4, 'placeholder': 'Tell us about yourself... (10–500 chars)'
            }),
        }

    def clean_bio(self):
        bio = self.cleaned_data.get('bio', '')
        if not (10 <= len(bio) <= 500):
            raise forms.ValidationError("Bio must be between 10–500 characters.")
        return bio

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo:
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size cannot exceed 5MB.")
            if photo.content_type not in ['image/jpeg', 'image/png', 'image/webp']:
                raise forms.ValidationError("Only JPG, PNG, and WebP formats allowed.")
        return photo
