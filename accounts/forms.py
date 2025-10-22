from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TelInput(attrs={"placeholder": "First Name"}),
    )

    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Last Name"}),
    )

    email = forms.EmailField(
        required=True, widget=forms.EmailInput(attrs={"placeholder": "Your .edu Email"})
    )

    class Meta:
        model = User
        fields = [
            "email",
            "username",
            "first_name",
            "last_name",
            "password1",
            "password2",
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered")
        return email
