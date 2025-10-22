from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.db.utils import IntegrityError
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image
from .models import Profile, Favorite, ConnectionRequest
from accounts.models import User
import json


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
            "pet_preference": "no_preference",
            "cleanliness_preference": "no_preference",
            "budget_min": 0,
            "budget_max": 5000,
            "location": "",
            "move_in_date": "",
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
        self.pfp_file.seek(0)
        self.client.post(self.create_profile_url, self.profile_data)
        self.client.logout()
        pfp_file = create_image()
        response = self.client.post(
            self.edit_profile_url,
            {**self.profile_data, "bio": "my test bio 2", "profile_photo": pfp_file},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/profiles/edit/")
        profile = Profile.objects.filter(user=self.user)[0]
        bio = profile.bio
        self.assertNotEqual(bio, "my test bio 2")

    # view_profile test cases
    def test_view_profile_success(self):
        self.pfp_file.seek(0)
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


class FavoriteModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            email="user1@nyu.edu", username="user1", password="testpw0rd"
        )
        self.user2 = User.objects.create_user(
            email="user2@nyu.edu", username="user2", password="testpw0rd"
        )
        self.profile1 = Profile.objects.create(
            user=self.user1,
            bio="test bio 1",
            university="NYU",
            profile_photo="pfp/test1.jpg",
        )
        self.profile2 = Profile.objects.create(
            user=self.user2,
            bio="test bio 2",
            university="Columbia",
            profile_photo="pfp/test2.jpg",
        )

    def test_create_favorite_success(self):
        favorite = Favorite.objects.create(
            user=self.user1, favorite_profile=self.profile2
        )
        self.assertIsNotNone(favorite)
        self.assertEqual(favorite.user, self.user1)
        self.assertEqual(favorite.favorite_profile, self.profile2)
        self.assertEqual(Favorite.objects.filter(user=self.user1).count(), 1)

    def test_favorite_unique_constraint(self):
        Favorite.objects.create(user=self.user1, favorite_profile=self.profile2)
        with self.assertRaises(IntegrityError):
            Favorite.objects.create(user=self.user1, favorite_profile=self.profile2)

    def test_favorite_str(self):
        favorite = Favorite.objects.create(
            user=self.user1, favorite_profile=self.profile2
        )
        self.assertEqual(str(favorite), "user1 favorited user2")

    def test_favorite_delete_cascade_user(self):
        Favorite.objects.create(user=self.user1, favorite_profile=self.profile2)
        self.assertTrue(Favorite.objects.filter(user=self.user1).exists())
        self.user1.delete()
        self.assertFalse(Favorite.objects.filter(user_id=self.user1.id).exists())

    def test_favorite_delete_cascade_profile(self):
        Favorite.objects.create(user=self.user1, favorite_profile=self.profile2)
        self.assertTrue(
            Favorite.objects.filter(favorite_profile=self.profile2).exists()
        )
        self.profile2.delete()
        self.assertFalse(
            Favorite.objects.filter(favorite_profile_id=self.profile2.id).exists()
        )


class ConnectionRequestModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            email="user1@nyu.edu", username="user1", password="testpw0rd"
        )
        self.user2 = User.objects.create_user(
            email="user2@nyu.edu", username="user2", password="testpw0rd"
        )

    def test_create_connection_request_success(self):
        request = ConnectionRequest.objects.create(
            from_user=self.user1, to_user=self.user2, message="Hello!"
        )
        self.assertIsNotNone(request)
        self.assertEqual(request.from_user, self.user1)
        self.assertEqual(request.to_user, self.user2)
        self.assertEqual(request.message, "Hello!")
        self.assertEqual(request.status, "pending")

    def test_connection_request_unique_constraint(self):
        ConnectionRequest.objects.create(from_user=self.user1, to_user=self.user2)
        with self.assertRaises(IntegrityError):
            ConnectionRequest.objects.create(from_user=self.user1, to_user=self.user2)

    def test_connection_request_str(self):
        request = ConnectionRequest.objects.create(
            from_user=self.user1, to_user=self.user2
        )
        self.assertEqual(str(request), "user1 → user2 (pending)")

    def test_connection_request_status_choices(self):
        request = ConnectionRequest.objects.create(
            from_user=self.user1, to_user=self.user2
        )
        request.status = "accepted"
        request.save()
        self.assertEqual(request.status, "accepted")
        request.status = "rejected"
        request.save()
        self.assertEqual(request.status, "rejected")

    def test_connection_request_delete_cascade(self):
        ConnectionRequest.objects.create(from_user=self.user1, to_user=self.user2)
        self.assertTrue(ConnectionRequest.objects.filter(from_user=self.user1).exists())
        self.user1.delete()
        self.assertFalse(
            ConnectionRequest.objects.filter(from_user_id=self.user1.id).exists()
        )


class RoommateSearchViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.user2 = User.objects.create_user(
            email="test2@nyu.edu", username="testuser2", password="testpw0rd"
        )
        self.user3 = User.objects.create_user(
            email="test3@nyu.edu", username="testuser3", password="testpw0rd"
        )

        self.profile1 = Profile.objects.create(
            user=self.user,
            bio="test bio 1",
            university="NYU",
            profile_photo="pfp/test1.jpg",
            smoking_preference="non_smoker",
            pet_preference="cats",
            cleanliness_preference="very_clean",
            budget_min=1000,
            budget_max=2000,
            location="Manhattan",
        )
        self.profile2 = Profile.objects.create(
            user=self.user2,
            bio="test bio 2",
            university="Columbia",
            profile_photo="pfp/test2.jpg",
            smoking_preference="smoker",
            pet_preference="dogs",
            cleanliness_preference="moderate",
            budget_min=1500,
            budget_max=2500,
            location="Brooklyn",
        )
        self.profile3 = Profile.objects.create(
            user=self.user3,
            bio="test bio 3",
            university="NYU",
            profile_photo="pfp/test3.jpg",
            smoking_preference="non_smoker",
            pet_preference="no_pets",
            cleanliness_preference="clean",
            budget_min=800,
            budget_max=1500,
            location="Queens",
            visibility=False,  # Hidden profile
        )

        self.roommate_search_url = reverse("roommate_search")
        self.client.login(email="test@nyu.edu", password="testpw0rd")

    def test_roommate_search_view_success(self):
        response = self.client.get(self.roommate_search_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profiles/roommate_search.html")

    def test_roommate_search_excludes_own_profile(self):
        response = self.client.get(self.roommate_search_url)
        profiles = response.context["profiles"]
        self.assertNotIn(self.profile1, profiles)

    def test_roommate_search_excludes_hidden_profiles(self):
        response = self.client.get(self.roommate_search_url)
        profiles = response.context["profiles"]
        self.assertNotIn(self.profile3, profiles)

    def test_roommate_search_filter_smoking(self):
        response = self.client.get(
            self.roommate_search_url, {"smoking_preference": ["non_smoker"]}
        )
        profiles = list(response.context["profiles"])
        self.assertNotIn(self.profile2, profiles)

    def test_roommate_search_filter_pets(self):
        response = self.client.get(
            self.roommate_search_url, {"pet_preference": ["dogs"]}
        )
        profiles = list(response.context["profiles"])
        self.assertIn(self.profile2, profiles)

    def test_roommate_search_filter_cleanliness(self):
        response = self.client.get(
            self.roommate_search_url, {"cleanliness_preference": ["very_clean"]}
        )
        profiles = list(response.context["profiles"])
        self.assertEqual(len(profiles), 0)  # profile1 is excluded (own profile)

    def test_roommate_search_filter_budget_min(self):
        response = self.client.get(self.roommate_search_url, {"budget_min": 2000})
        profiles = list(response.context["profiles"])
        self.assertIn(self.profile2, profiles)

    def test_roommate_search_filter_budget_max(self):
        response = self.client.get(self.roommate_search_url, {"budget_max": 1200})
        profiles = list(response.context["profiles"])
        # Only profiles with budget_min <= 1200 should be included
        self.assertEqual(len(profiles), 0)

    def test_roommate_search_filter_location(self):
        response = self.client.get(self.roommate_search_url, {"location": "Brooklyn"})
        profiles = list(response.context["profiles"])
        self.assertIn(self.profile2, profiles)

    def test_roommate_search_filter_university(self):
        response = self.client.get(
            self.roommate_search_url, {"university": ["Columbia"]}
        )
        profiles = list(response.context["profiles"])
        self.assertIn(self.profile2, profiles)

    def test_roommate_search_not_logged_in(self):
        self.client.logout()
        response = self.client.get(self.roommate_search_url)
        self.assertEqual(response.status_code, 302)


class RoommateDetailViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.user2 = User.objects.create_user(
            email="test2@nyu.edu", username="testuser2", password="testpw0rd"
        )

        self.profile1 = Profile.objects.create(
            user=self.user,
            bio="test bio 1",
            university="NYU",
            profile_photo="pfp/test1.jpg",
        )
        self.profile2 = Profile.objects.create(
            user=self.user2,
            bio="test bio 2",
            university="Columbia",
            profile_photo="pfp/test2.jpg",
        )

        self.client.login(email="test@nyu.edu", password="testpw0rd")

    def test_roommate_detail_view_success(self):
        url = reverse("roommate_detail", kwargs={"user_id": self.user2.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profiles/roommate_detail.html")
        self.assertEqual(response.context["profile"], self.profile2)

    def test_roommate_detail_cannot_view_own_profile(self):
        url = reverse("roommate_detail", kwargs={"user_id": self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("roommate_search"))

    def test_roommate_detail_not_found(self):
        url = reverse("roommate_detail", kwargs={"user_id": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class ToggleFavoriteViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.user2 = User.objects.create_user(
            email="test2@nyu.edu", username="testuser2", password="testpw0rd"
        )

        self.profile1 = Profile.objects.create(
            user=self.user,
            bio="test bio 1",
            university="NYU",
            profile_photo="pfp/test1.jpg",
        )
        self.profile2 = Profile.objects.create(
            user=self.user2,
            bio="test bio 2",
            university="Columbia",
            profile_photo="pfp/test2.jpg",
        )

        self.client.login(email="test@nyu.edu", password="testpw0rd")

    def test_toggle_favorite_add(self):
        url = reverse("toggle_favorite", kwargs={"user_id": self.user2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["favorited"])
        self.assertTrue(
            Favorite.objects.filter(
                user=self.user, favorite_profile=self.profile2
            ).exists()
        )

    def test_toggle_favorite_remove(self):
        Favorite.objects.create(user=self.user, favorite_profile=self.profile2)
        url = reverse("toggle_favorite", kwargs={"user_id": self.user2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data["favorited"])
        self.assertFalse(
            Favorite.objects.filter(
                user=self.user, favorite_profile=self.profile2
            ).exists()
        )

    def test_toggle_favorite_own_profile(self):
        url = reverse("toggle_favorite", kwargs={"user_id": self.user.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_toggle_favorite_not_logged_in(self):
        self.client.logout()
        url = reverse("toggle_favorite", kwargs={"user_id": self.user2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)


class ConnectionRequestViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.user2 = User.objects.create_user(
            email="test2@nyu.edu", username="testuser2", password="testpw0rd"
        )

        self.profile1 = Profile.objects.create(
            user=self.user,
            bio="test bio 1",
            university="NYU",
            profile_photo="pfp/test1.jpg",
        )
        self.profile2 = Profile.objects.create(
            user=self.user2,
            bio="test bio 2",
            university="Columbia",
            profile_photo="pfp/test2.jpg",
        )

        self.client.login(email="test@nyu.edu", password="testpw0rd")

    def test_send_connection_request_success(self):
        url = reverse("send_connection_request", kwargs={"user_id": self.user2.id})
        response = self.client.post(url, {"message": "Let's be roommates!"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ConnectionRequest.objects.filter(
                from_user=self.user, to_user=self.user2
            ).exists()
        )

    def test_send_connection_request_to_self(self):
        url = reverse("send_connection_request", kwargs={"user_id": self.user.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            ConnectionRequest.objects.filter(
                from_user=self.user, to_user=self.user
            ).exists()
        )

    def test_send_duplicate_connection_request(self):
        ConnectionRequest.objects.create(from_user=self.user, to_user=self.user2)
        url = reverse("send_connection_request", kwargs={"user_id": self.user2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            ConnectionRequest.objects.filter(
                from_user=self.user, to_user=self.user2
            ).count(),
            1,
        )

    def test_respond_to_request_accept(self):
        request = ConnectionRequest.objects.create(
            from_user=self.user2, to_user=self.user
        )
        url = reverse("respond_to_request", kwargs={"request_id": request.id})
        response = self.client.post(url, {"action": "accept"})
        self.assertEqual(response.status_code, 302)
        request.refresh_from_db()
        self.assertEqual(request.status, "accepted")

    def test_respond_to_request_reject(self):
        request = ConnectionRequest.objects.create(
            from_user=self.user2, to_user=self.user
        )
        url = reverse("respond_to_request", kwargs={"request_id": request.id})
        response = self.client.post(url, {"action": "reject"})
        self.assertEqual(response.status_code, 302)
        request.refresh_from_db()
        self.assertEqual(request.status, "rejected")

    def test_connection_requests_view(self):
        ConnectionRequest.objects.create(from_user=self.user2, to_user=self.user)
        url = reverse("connection_requests")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profiles/connection_requests.html")

    def test_my_favorites_view(self):
        Favorite.objects.create(user=self.user, favorite_profile=self.profile2)
        url = reverse("my_favorites")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profiles/my_favorites.html")
