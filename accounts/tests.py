from django.test import TestCase, Client
from django.urls import reverse
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.core import mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sessions.models import Session
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


class RegistrationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse("register")

    def test_register_view_get(self):
        """Test GET request to registration page"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")
        self.assertIn("form", response.context)

    def test_register_valid_user(self):
        """Test successful user registration"""
        response = self.client.post(
            self.register_url,
            {
                "email": "newuser@columbia.edu",
                "username": "newuser",
                "first_name": "New",
                "last_name": "User",
                "password1": "TestPassword123!",
                "password2": "TestPassword123!",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.register_url)

        # Check user was created
        user = User.objects.get(email="newuser@columbia.edu")
        self.assertFalse(user.is_verified)
        self.assertTrue(user.is_active)

        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Verify Your CampusNest Account", mail.outbox[0].subject)
        self.assertIn("newuser@columbia.edu", mail.outbox[0].to)

    def test_register_invalid_form(self):
        """Test registration with invalid data"""
        response = self.client.post(
            self.register_url,
            {
                "email": "invalid@gmail.com",  # Not .edu
                "username": "testuser",
                "password1": "pass",
                "password2": "pass",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="invalid@gmail.com").exists())


class EmailVerificationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@nyu.edu",
            username="testuser",
            password="TestPassword123!",
            first_name="Test",
            is_verified=False,
        )

    def test_verify_email_valid_token(self):
        """Test email verification with valid token"""
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        url = reverse("verify_email", kwargs={"uidb64": uid, "token": token})

        response = self.client.get(url)
        self.assertRedirects(response, reverse("login"))

        # Check user is now verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified)

    def test_verify_email_invalid_token(self):
        """Test email verification with invalid token"""
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        url = reverse("verify_email", kwargs={"uidb64": uid, "token": "invalid-token"})

        response = self.client.get(url)
        self.assertRedirects(response, reverse("resend_verification"))

        # Check user is still not verified
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_verified)

    def test_verify_email_invalid_uid(self):
        """Test email verification with invalid UID"""
        token = default_token_generator.make_token(self.user)
        url = reverse("verify_email", kwargs={"uidb64": "invalid-uid", "token": token})

        response = self.client.get(url)
        self.assertRedirects(response, reverse("resend_verification"))


class LoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse("login")
        self.verified_user = User.objects.create_user(
            email="verified@nyu.edu",
            username="verified",
            password="TestPassword123!",
            first_name="Verified",
            is_verified=True,
        )
        self.unverified_user = User.objects.create_user(
            email="unverified@nyu.edu",
            username="unverified",
            password="TestPassword123!",
            first_name="Unverified",
            is_verified=False,
        )

        # Create profile for verified user (required for view_profile redirect)
        from profiles.models import Profile
        Profile.objects.create(user=self.verified_user, university="nyu")

    def test_login_view_get(self):
        """Test GET request to login page"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_login_verified_user_success(self):
        """Test login with verified user"""
        response = self.client.post(
            self.login_url,
            {"username": "verified@nyu.edu", "password": "TestPassword123!"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_unverified_user(self):
        """Test login with unverified user"""
        response = self.client.post(
            self.login_url,
            {"username": "unverified@nyu.edu", "password": "TestPassword123!"},
        )
        self.assertRedirects(response, reverse("resend_verification"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        response = self.client.post(
            self.login_url,
            {"username": "verified@nyu.edu", "password": "WrongPassword"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class LogoutViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.logout_url = reverse("logout")
        self.user = User.objects.create_user(
            email="test@nyu.edu",
            username="testuser",
            password="TestPassword123!",
            is_verified=True,
        )

    def test_logout(self):
        """Test user logout"""
        self.client.login(username="test@nyu.edu", password="TestPassword123!")
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, reverse("login"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class ResendVerificationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.resend_url = reverse("resend_verification")
        self.unverified_user = User.objects.create_user(
            email="unverified@nyu.edu",
            username="unverified",
            password="TestPassword123!",
            first_name="Unverified",
            is_verified=False,
        )
        self.verified_user = User.objects.create_user(
            email="verified@nyu.edu",
            username="verified",
            password="TestPassword123!",
            is_verified=True,
        )

    def test_resend_verification_get(self):
        """Test GET request to resend verification page"""
        response = self.client.get(self.resend_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/resend_verification.html")

    def test_resend_verification_unverified_user(self):
        """Test resending verification email to unverified user"""
        response = self.client.post(self.resend_url, {"email": "unverified@nyu.edu"})
        self.assertRedirects(response, self.resend_url)

        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Verify Your CampusNest Account", mail.outbox[0].subject)

    def test_resend_verification_verified_user(self):
        """Test resending verification to already verified user"""
        response = self.client.post(self.resend_url, {"email": "verified@nyu.edu"})
        self.assertRedirects(response, reverse("login"))

    def test_resend_verification_nonexistent_email(self):
        """Test resending verification to non-existent email"""
        response = self.client.post(
            self.resend_url, {"email": "nonexistent@nyu.edu"}
        )
        self.assertEqual(response.status_code, 200)

    def test_resend_verification_with_session_email(self):
        """Test resend page pre-fills email from session"""
        session = self.client.session
        session["unverified_email"] = "unverified@nyu.edu"
        session.save()

        response = self.client.get(self.resend_url)
        self.assertEqual(response.context["initial_email"], "unverified@nyu.edu")
        self.assertNotIn("unverified_email", self.client.session)


class PasswordResetRequestViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.reset_url = reverse("password_reset_request")
        self.user = User.objects.create_user(
            email="test@nyu.edu",
            username="testuser",
            password="TestPassword123!",
            first_name="Test",
            is_verified=True,
        )

    def test_password_reset_request_get(self):
        """Test GET request to password reset page"""
        response = self.client.get(self.reset_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/password_reset_request.html")

    def test_password_reset_existing_user(self):
        """Test password reset for existing user"""
        response = self.client.post(self.reset_url, {"email": "test@nyu.edu"})
        self.assertRedirects(response, self.reset_url)

        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Reset Your CampusNest Password", mail.outbox[0].subject)

    def test_password_reset_nonexistent_user(self):
        """Test password reset for non-existent user (no info leak)"""
        response = self.client.post(
            self.reset_url, {"email": "nonexistent@nyu.edu"}
        )
        self.assertRedirects(response, self.reset_url)
        # No email should be sent but same message shown
        self.assertEqual(len(mail.outbox), 0)


class PasswordResetConfirmViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@nyu.edu",
            username="testuser",
            password="OldPassword123!",
            first_name="Test",
            is_verified=True,
        )

    def test_password_reset_confirm_get_valid_token(self):
        """Test GET request to password reset confirm with valid token"""
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        url = reverse(
            "password_reset_confirm", kwargs={"uidb64": uid, "token": token}
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/password_reset_confirm.html")
        self.assertIn("form", response.context)

    def test_password_reset_confirm_post_valid(self):
        """Test password reset with valid token and password"""
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        url = reverse(
            "password_reset_confirm", kwargs={"uidb64": uid, "token": token}
        )

        response = self.client.post(
            url,
            {"new_password1": "NewPassword123!", "new_password2": "NewPassword123!"},
        )
        self.assertRedirects(response, reverse("login"))

        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPassword123!"))

        # Check confirmation email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Password Has Been Changed", mail.outbox[0].subject)

    def test_password_reset_confirm_invalid_token(self):
        """Test password reset with invalid token"""
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        url = reverse(
            "password_reset_confirm", kwargs={"uidb64": uid, "token": "invalid-token"}
        )

        response = self.client.get(url)
        self.assertRedirects(response, reverse("password_reset_request"))

    def test_password_reset_terminates_sessions(self):
        """Test that password reset terminates all user sessions"""
        # Create a session for the user by logging in
        self.client.force_login(self.user)

        # Save the session
        self.client.session.save()
        session_key = self.client.session.session_key

        # Verify session exists
        self.assertTrue(Session.objects.filter(pk=session_key).exists())

        # Reset password using a different client
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        url = reverse(
            "password_reset_confirm", kwargs={"uidb64": uid, "token": token}
        )

        new_client = Client()
        response = new_client.post(
            url,
            {"new_password1": "NewPassword123!", "new_password2": "NewPassword123!"},
        )

        # Verify redirect (password reset succeeded)
        self.assertEqual(response.status_code, 302)

        # Verify old session was deleted
        self.assertFalse(Session.objects.filter(pk=session_key).exists())


class TerminateUserSessionsTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            email="user1@nyu.edu",
            username="user1",
            password="TestPassword123!",
            is_verified=True,
        )
        self.user2 = User.objects.create_user(
            email="user2@nyu.edu",
            username="user2",
            password="TestPassword123!",
            is_verified=True,
        )

    def test_terminate_only_target_user_sessions(self):
        """Test that only the target user's sessions are terminated"""
        # Create sessions for both users
        client1 = Client()
        client2 = Client()

        client1.login(username="user1@nyu.edu", password="TestPassword123!")
        client2.login(username="user2@nyu.edu", password="TestPassword123!")

        session_key1 = client1.session.session_key
        session_key2 = client2.session.session_key

        # Verify both sessions exist
        self.assertTrue(Session.objects.filter(pk=session_key1).exists())
        self.assertTrue(Session.objects.filter(pk=session_key2).exists())

        # Terminate user1's sessions
        from accounts.views import terminate_user_sessions

        terminate_user_sessions(self.user1)

        # Verify only user1's session was deleted
        self.assertFalse(Session.objects.filter(pk=session_key1).exists())
        self.assertTrue(Session.objects.filter(pk=session_key2).exists())


class RegistrationFormTests(TestCase):
    """Test RegistrationForm validation"""

    def test_form_with_duplicate_email(self):
        """Test that form rejects duplicate email"""
        # Create existing user
        User.objects.create_user(
            email="existing@nyu.edu",
            username="existing",
            password="TestPassword123!",
        )

        from accounts.forms import RegistrationForm

        form_data = {
            "email": "existing@nyu.edu",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "password1": "TestPassword123!",
            "password2": "TestPassword123!",
        }
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertIn("already registered", str(form.errors["email"]))
