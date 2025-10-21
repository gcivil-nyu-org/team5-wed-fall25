from django.test import TestCase, Client
from django.urls import reverse
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from .models import User


# Create your tests here.
class UserModelTests(TestCase):
    def setUp(self):
        User.objects.create(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )

    def test_create_user(self):
        self.assertEqual(User.objects.filter(email="test@nyu.edu").count(), 1)

    def test_create_duplicate_user(self):
        with self.assertRaises(IntegrityError):
            User.objects.create(
                email="test@nyu.edu", username="differentuser", password="testpw0rd"
            )

    def test_create_duplicate_username(self):
        with self.assertRaises(IntegrityError):
            User.objects.create(
                email="test2@nyu.edu", username="testuser", password="testpw0rd"
            )

    def test_non_edu_email(self):
        user = User(email="test@nyu.com", username="differentuser")
        with self.assertRaises(ValidationError) as exc:
            user.full_clean()
        self.assertIn(
            "Please enter a valid .edu email address from your university",
            str(exc.exception),
        )


class UserViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse("register")
        self.verify_email_url = reverse("verify_email")
        self.resend_verification_url = reverse("resend_verification")
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.password_reset_request_url = reverse("password_reset_request")
        self.password_reset_confirm_url = reverse("password_reset_confirm")
