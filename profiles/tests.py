from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.db.utils import IntegrityError
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image
from .models import Profile
from accounts.models import User


# Create your tests here.
def create_image(image_mode="RGB", size=(5, 5), color="white", image_format="PNG"):
    data = BytesIO()
    Image.new(image_mode, size, color=color).save(data, image_format)
    image_bytes = data.getvalue()
    mock_image = SimpleUploadedFile(
        name="test.png", content=image_bytes, content_type=f"image/{image_format}"
    )
    return mock_image


class ProfileModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.profile = Profile.objects.create(
            user=self.user,
            bio="test bio",
            university="New York University",
            profile_photo="pfp/images.jpg",
            visibility=True,
            eating_habit="no_preference",
            smoking_preference="non_smoker",
            sharing_preference="no_preference",
            drinking_preference="no_preference",
        )

    def test_create_profile_success(self):
        profile = self.profile
        self.assertIsNotNone(profile)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.bio, "test bio")
        self.assertEqual(profile.university, "New York University")
        self.assertEqual(profile.profile_photo, "pfp/images.jpg")
        self.assertTrue(profile.visibility)
        self.assertEqual(profile.eating_habit, "no_preference")
        self.assertEqual(profile.smoking_preference, "non_smoker")
        self.assertEqual(profile.sharing_preference, "no_preference")
        self.assertEqual(profile.drinking_preference, "no_preference")
        self.assertEqual(Profile.objects.filter(user=self.user).count(), 1)

    def test_create_duplicate_profile(self):
        with self.assertRaises(IntegrityError):
            Profile.objects.create(
                user=self.user,
                bio="test bio",
                university="New York University",
                profile_photo="pfp/images.jpg",
                visibility=True,
            )

    def test_invalid_fields(self):
        cases = [
            {"field": "bio", "value": "a" * 501},
            {"field": "university", "value": "Fake University"},
            {"field": "eating_habit", "value": "Fake diet"},
            {"field": "smoking_preference", "value": "Super smoker"},
            {"field": "sharing_preference", "value": "Open to Chering"},
            {"field": "drinking_preference", "value": "Liver Failure"},
        ]
        for case in cases:
            with self.subTest():
                setattr(self.profile, case["field"], case["value"])
                with self.assertRaises(ValidationError):
                    self.profile.full_clean()

    def test_defaults(self):
        user2 = User.objects.create_user(
            email="test2@nyu.edu", username="test2user", password="testpw0rd"
        )
        before = timezone.now()
        profile = Profile.objects.create(
            user=user2,
            bio="bio 2",
            university="New York Univesity",
            profile_photo="pfp/images.jpg",
        )
        after = timezone.now()
        self.assertTrue(profile.visibility)
        self.assertGreaterEqual(profile.created_at, before)
        self.assertLessEqual(profile.created_at, after)
        self.assertEqual(profile.eating_habit, "no_preference")
        self.assertEqual(profile.smoking_preference, "non_smoker")
        self.assertEqual(profile.sharing_preference, "no_preference")
        self.assertEqual(profile.drinking_preference, "no_preference")

    def test_delete_cascade(self):
        self.assertTrue(Profile.objects.filter(user=self.user).exists())
        self.user.delete()
        self.assertFalse(Profile.objects.filter(user_id=self.user.id).exists())

    def test_profile_str(self):
        self.assertEqual(str(self.profile), "testuser's Profile")
        self.assertEqual(
            self.profile.get_preference_display_with_icon("eating"), "🤷 No Preference"
        )
        self.assertEqual(
            self.profile.get_preference_display_with_icon("smoking"), "🚭 Non-Smoker"
        )
        self.assertEqual(
            self.profile.get_preference_display_with_icon("sharing"), "🤷 No Preference"
        )
        self.assertEqual(
            self.profile.get_preference_display_with_icon("drinking"),
            "🤷 No Preference",
        )


class ProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.create_profile_url = reverse("create_profile")
        self.edit_profile_url = reverse("edit_profile")
        self.view_profile_url = reverse("view_profile")
        self.admin_dashboard_url = reverse("admin_dashboard")
        self.pfp_file = create_image()
        self.profile_data = {
            "bio": "my test bio",
            "university": "NYU",
            "profile_photo": self.pfp_file,
            "visibility": True,
            "eating_habit": "no_preference",
            "smoking_preference": "non_smoker",
            "sharing_preference": "no_preference",
            "drinking_preference": "no_preference",
        }
        self.client.login(email="test@nyu.edu", password="testpw0rd")

    def tearDown(self):
        self.user.delete()

    # create_profile test cases
    def test_create_profile_success_view(self):
        self.pfp_file.seek(0)
        response = self.client.post(self.create_profile_url, self.profile_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.view_profile_url)
        self.assertEqual(Profile.objects.filter(user=self.user).count(), 1)
        profile = Profile.objects.get(user=self.user)
        self.assertTrue(profile.visibility)
        self.assertEqual(profile.bio, "my test bio")
        self.assertEqual(profile.university, "NYU")
        self.assertEqual(profile.eating_habit, "no_preference")
        self.assertEqual(profile.smoking_preference, "non_smoker")
        self.assertEqual(profile.sharing_preference, "no_preference")
        self.assertEqual(profile.drinking_preference, "no_preference")

    def test_form_errors(self):
        self.pfp_file.seek(0)
        pfp_file = create_image(image_format="GIF")
        test_cases = [
            {
                "data": {**self.profile_data, "bio": "a" * 5},
                "field": "bio",
                "error_msg": "Bio must be between 10–500 characters.",
            },
            # {
            #    "data": {**self.profile_data, "bio": "a" * 501},
            #    "field": "bio",
            #    "error_msg": "Bio must be between 10–500 characters."
            # },
            {
                "data": {**self.profile_data, "university": "FakeU"},
                "field": "university",
                "error_msg": "Select a valid choice. FakeU is not one of the available choices.",
            },
            {
                "data": {**self.profile_data, "profile_photo": pfp_file},
                "field": "profile_photo",
                "error_msg": "Only JPG, PNG, and WebP formats allowed.",
            },
            {
                "data": {**self.profile_data, "eating_habit": "None"},
                "field": "eating_habit",
                "error_msg": "Select a valid choice. None is not one of the available choices.",
            },
            {
                "data": {**self.profile_data, "smoking_preference": "None"},
                "field": "smoking_preference",
                "error_msg": "Select a valid choice. None is not one of the available choices.",
            },
            {
                "data": {**self.profile_data, "sharing_preference": "None"},
                "field": "sharing_preference",
                "error_msg": "Select a valid choice. None is not one of the available choices.",
            },
            {
                "data": {**self.profile_data, "drinking_preference": "None"},
                "field": "drinking_preference",
                "error_msg": "Select a valid choice. None is not one of the available choices.",
            },
        ]
        for case in test_cases:
            response = self.client.post(self.create_profile_url, case["data"])
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "profiles/profile_form.html")
            form = response.context["form"]
            self.assertFalse(form.is_valid())
            self.assertIn(case["field"], form.errors)
            self.assertIn(case["error_msg"], form.errors[case["field"]])

    def test_not_logged_in(self):
        self.pfp_file.seek(0)
        self.client.logout()
        response = self.client.post(self.create_profile_url, self.profile_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/profiles/create/")
        self.assertFalse(Profile.objects.filter(user=self.user).exists())

    def test_create_duplicate_profile(self):
        self.pfp_file.seek(0)
        self.client.post(self.create_profile_url, self.profile_data)
        response = self.client.post(self.create_profile_url, self.profile_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.view_profile_url)
        self.assertEqual(Profile.objects.filter(user=self.user).count(), 1)
        message = list(get_messages(response.wsgi_request))
        messages = [str(m) for m in message]
        self.assertIn("Profile already exists.", messages)

    # edit_profile test cases
    # note these will be very similar to the above tests
    def test_edit_profile_success(self):
        self.pfp_file.seek(0)
        response = self.client.post(self.create_profile_url, self.profile_data)
        # have to reinstantiate image or else it breaks
        pfp_file = create_image()
        response = self.client.post(
            self.edit_profile_url,
            {**self.profile_data, "bio": "my test bio 2", "profile_photo": pfp_file},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.view_profile_url)
        self.assertEqual(Profile.objects.filter(user=self.user).count(), 1)
        profile = Profile.objects.get(user=self.user)
        self.assertTrue(profile.visibility)
        self.assertEqual(profile.bio, "my test bio 2")
        self.assertEqual(profile.university, "NYU")
        self.assertEqual(profile.eating_habit, "no_preference")
        self.assertEqual(profile.smoking_preference, "non_smoker")
        self.assertEqual(profile.sharing_preference, "no_preference")
        self.assertEqual(profile.drinking_preference, "no_preference")

    def test_edit_form_errors(self):
        self.pfp_file.seek(0)
        self.client.post(self.create_profile_url, self.profile_data)
        pfp_file = create_image()
        pfp_file2 = create_image(image_format="GIF")
        test_cases = [
            {
                "data": {
                    **self.profile_data,
                    "bio": "a" * 5,
                    "profile_photo": pfp_file,
                },
                "field": "bio",
                "error_msg": "Bio must be between 10–500 characters.",
            },
            {
                "data": {
                    **self.profile_data,
                    "university": "FakeU",
                    "profile_photo": pfp_file,
                },
                "field": "university",
                "error_msg": "Select a valid choice. FakeU is not one of the available choices.",
            },
            {
                "data": {**self.profile_data, "profile_photo": pfp_file2},
                "field": "profile_photo",
                "error_msg": "Only JPG, PNG, and WebP formats allowed.",
            },
            {
                "data": {
                    **self.profile_data,
                    "eating_habit": "None",
                    "profile_photo": pfp_file,
                },
                "field": "eating_habit",
                "error_msg": "Select a valid choice. None is not one of the available choices.",
            },
            {
                "data": {
                    **self.profile_data,
                    "smoking_preference": "None",
                    "profile_photo": pfp_file,
                },
                "field": "smoking_preference",
                "error_msg": "Select a valid choice. None is not one of the available choices.",
            },
            {
                "data": {
                    **self.profile_data,
                    "sharing_preference": "None",
                    "profile_photo": pfp_file,
                },
                "field": "sharing_preference",
                "error_msg": "Select a valid choice. None is not one of the available choices.",
            },
            {
                "data": {
                    **self.profile_data,
                    "drinking_preference": "None",
                    "profile_photo": pfp_file,
                },
                "field": "drinking_preference",
                "error_msg": "Select a valid choice. None is not one of the available choices.",
            },
        ]
        for case in test_cases:
            response = self.client.post(self.edit_profile_url, case["data"])
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "profiles/edit_profile.html")
            form = response.context["form"]
            self.assertFalse(form.is_valid())
            self.assertIn(case["field"], form.errors)
            self.assertIn(case["error_msg"], form.errors[case["field"]])

    def test_edit_not_logged_in(self):
        self.client.post(self.create_profile_url, self.profile_data)
        self.client.logout()
        response = self.client.post(
            self.edit_profile_url, {**self.profile_data, "bio": "my test bio 2"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/profiles/edit/")
        profile = Profile.objects.filter(user=self.user)[0]
        bio = profile.bio
        self.assertNotEqual(bio, "my test bio 2")

    # view_profile test cases
    def test_view_profile_success(self):
        self.client.post(self.create_profile_url, self.profile_data)
        response = self.client.get(self.view_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profiles/view_profile.html")

    def test_view_profile_fail(self):
        response = self.client.get(self.view_profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.create_profile_url)

    def test_view_not_logged_in(self):
        self.client.logout()
        response = self.client.post(self.view_profile_url, self.profile_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/profiles/view/")
        self.assertFalse(Profile.objects.filter(user=self.user).exists())

    # admin_dashboard test cases
    def test_admin_dashboard(self):
        User.objects.create_superuser(
            email="staff@nyu.edu", username="staffuser", password="staffpw0rd"
        )
        self.client.logout()
        self.client.login(email="staff@nyu.edu", password="staffpw0rd")
        response = self.client.get(self.admin_dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profiles/admin_dashboard.html")

    def test_admin_regular_user(self):
        response = self.client.get(self.admin_dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/admin/login/?next=/profiles/admin-dashboard/")

    def test_admin_logged_out(self):
        self.client.logout()
        response = self.client.get(self.admin_dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/admin/login/?next=/profiles/admin-dashboard/")
