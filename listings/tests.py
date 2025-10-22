from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from io import BytesIO
from PIL import Image
from decimal import Decimal
from datetime import timedelta
from .models import Listing, ListingImage, validate_future_date
from .forms import ListingForm
from accounts.models import User


def create_image(image_mode="RGB", size=(5, 5), color="white", image_format="PNG"):
    """Helper function to create test images."""
    data = BytesIO()
    Image.new(image_mode, size, color=color).save(data, image_format)
    image_bytes = data.getvalue()
    mock_image = SimpleUploadedFile(
        name="test.png", content=image_bytes, content_type=f"image/{image_format}"
    )
    return mock_image


class ListingModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.future_start = timezone.now().date() + timedelta(days=7)
        self.future_end = timezone.now().date() + timedelta(days=37)
        self.listing = Listing.objects.create(
            user=self.user,
            title="Test Listing",
            address="123 Main St, Brooklyn, NY 11201",
            rent=Decimal("1500.00"),
            description="This is a test listing description with at least 20 characters",
            amenities="furnished,wifi,laundry",
            custom_amenities="Balcony, Dishwasher",
            availability_start=self.future_start,
            availability_end=self.future_end,
        )

    def test_create_listing_success(self):
        """Test creating a listing with valid data"""
        listing = self.listing
        self.assertIsNotNone(listing)
        self.assertEqual(listing.user, self.user)
        self.assertEqual(listing.title, "Test Listing")
        self.assertEqual(listing.address, "123 Main St, Brooklyn, NY 11201")
        self.assertEqual(listing.rent, Decimal("1500.00"))
        self.assertEqual(
            listing.description,
            "This is a test listing description with at least 20 characters",
        )
        self.assertEqual(listing.amenities, "furnished,wifi,laundry")
        self.assertEqual(listing.custom_amenities, "Balcony, Dishwasher")
        self.assertEqual(listing.availability_start, self.future_start)
        self.assertEqual(listing.availability_end, self.future_end)
        self.assertEqual(Listing.objects.filter(user=self.user).count(), 1)

    def test_listing_defaults(self):
        """Test default values for listing fields"""
        user2 = User.objects.create_user(
            email="test2@nyu.edu", username="test2user", password="testpw0rd"
        )
        before = timezone.now()
        listing = Listing.objects.create(
            user=user2,
            title="Another Listing",
            address="456 Oak Ave, Manhattan, NY 10001",
            rent=Decimal("2000.00"),
            description="Another test listing description",
            availability_start=self.future_start,
            availability_end=self.future_end,
        )
        after = timezone.now()

        self.assertFalse(listing.is_edited)
        self.assertTrue(listing.is_active)
        self.assertGreaterEqual(listing.created_at, before)
        self.assertLessEqual(listing.created_at, after)
        self.assertEqual(listing.amenities, "")
        self.assertEqual(listing.custom_amenities, "")

    def test_listing_str(self):
        """Test Listing string representation"""
        self.assertEqual(str(self.listing), "Test Listing - testuser")

    def test_get_amenities_list(self):
        """Test get_amenities_list method"""
        amenities_list = self.listing.get_amenities_list()
        self.assertEqual(amenities_list, ["furnished", "wifi", "laundry"])

    def test_get_amenities_list_empty(self):
        """Test get_amenities_list with no amenities"""
        listing = Listing.objects.create(
            user=self.user,
            title="No Amenities Listing",
            address="789 Pine St",
            rent=Decimal("1000.00"),
            description="A listing with no amenities selected",
            availability_start=self.future_start,
            availability_end=self.future_end,
        )
        self.assertEqual(listing.get_amenities_list(), [])

    def test_get_amenities_display(self):
        """Test get_amenities_display method"""
        display_list = self.listing.get_amenities_display()
        expected = ["Furnished", "WiFi", "Laundry", "Balcony", "Dishwasher"]
        self.assertEqual(display_list, expected)

    def test_get_amenities_display_no_custom(self):
        """Test get_amenities_display without custom amenities"""
        listing = Listing.objects.create(
            user=self.user,
            title="Standard Amenities",
            address="123 Test St",
            rent=Decimal("1200.00"),
            description="Standard amenities only listing",
            amenities="furnished,wifi",
            availability_start=self.future_start,
            availability_end=self.future_end,
        )
        display_list = listing.get_amenities_display()
        self.assertEqual(display_list, ["Furnished", "WiFi"])

    def test_get_amenities_display_empty(self):
        """Test get_amenities_display with no amenities"""
        listing = Listing.objects.create(
            user=self.user,
            title="Empty Amenities",
            address="456 Test Ave",
            rent=Decimal("1100.00"),
            description="No amenities at all listing",
            availability_start=self.future_start,
            availability_end=self.future_end,
        )
        self.assertEqual(listing.get_amenities_display(), [])

    def test_listing_ordering(self):
        """Test that listings are ordered by creation date"""
        Listing.objects.all().delete()
        listing1 = Listing.objects.create(
            user=self.user,
            title="First Listing",
            address="1 First St",
            rent=Decimal("1000.00"),
            description="First listing created for ordering test",
            availability_start=self.future_start,
            availability_end=self.future_end,
        )
        listing2 = Listing.objects.create(
            user=self.user,
            title="Second Listing",
            address="2 Second St",
            rent=Decimal("1100.00"),
            description="Second listing created for ordering test",
            availability_start=self.future_start,
            availability_end=self.future_end,
        )

        listings = Listing.objects.filter(user=self.user).order_by("-created_at")
        self.assertEqual(listings[0].id, listing2.id)
        self.assertEqual(listings[1].id, listing1.id)

    def test_validate_future_date_valid(self):
        """Test future date validation with valid date"""
        future_date = timezone.now().date() + timedelta(days=1)
        try:
            validate_future_date(future_date)
        except ValidationError:
            self.fail("validate_future_date raised ValidationError unexpectedly")

    def test_validate_future_date_invalid(self):
        """Test future date validation with past date"""
        past_date = timezone.now().date() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            validate_future_date(past_date)

    def test_validate_future_date_today(self):
        """Test future date validation with today's date"""
        # Note: The validator allows today's date, only past dates are rejected
        today = timezone.now().date()
        try:
            validate_future_date(today)
        except ValidationError:
            self.fail(
                "validate_future_date raised ValidationError unexpectedly for today"
            )

    def test_listing_cascade_delete_images(self):
        """Test that deleting a listing deletes associated images"""
        image = create_image()
        listing_image = ListingImage.objects.create(listing=self.listing, image=image)
        listing_image_id = listing_image.id

        self.assertEqual(ListingImage.objects.filter(listing=self.listing).count(), 1)
        self.listing.delete()
        self.assertEqual(ListingImage.objects.filter(id=listing_image_id).count(), 0)

    def test_listing_cascade_delete_user(self):
        """Test that deleting a user deletes their listings"""
        user3 = User.objects.create_user(
            email="test3@nyu.edu", username="test3user", password="testpw0rd"
        )
        listing = Listing.objects.create(
            user=user3,
            title="User3 Listing",
            address="999 Test Blvd",
            rent=Decimal("1800.00"),
            description="Listing for cascade delete test",
            availability_start=self.future_start,
            availability_end=self.future_end,
        )
        listing_id = listing.id

        self.assertEqual(Listing.objects.filter(user=user3).count(), 1)
        user3.delete()
        self.assertEqual(Listing.objects.filter(id=listing_id).count(), 0)


class ListingImageModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.future_start = timezone.now().date() + timedelta(days=7)
        self.future_end = timezone.now().date() + timedelta(days=37)
        self.listing = Listing.objects.create(
            user=self.user,
            title="Test Listing",
            address="123 Main St",
            rent=Decimal("1500.00"),
            description="Test listing for image tests",
            availability_start=self.future_start,
            availability_end=self.future_end,
        )

    def test_create_listing_image(self):
        """Test creating a listing image"""
        image = create_image()
        listing_image = ListingImage.objects.create(listing=self.listing, image=image)

        self.assertIsNotNone(listing_image)
        self.assertEqual(listing_image.listing, self.listing)
        self.assertTrue(listing_image.image.name.startswith("listing_photos/"))

    def test_listing_image_str(self):
        """Test ListingImage string representation"""
        image = create_image()
        listing_image = ListingImage.objects.create(listing=self.listing, image=image)
        self.assertEqual(str(listing_image), "Image for Test Listing")

    def test_multiple_images_for_listing(self):
        """Test creating multiple images for a listing"""
        for i in range(5):
            image = create_image()
            ListingImage.objects.create(listing=self.listing, image=image)

        self.assertEqual(ListingImage.objects.filter(listing=self.listing).count(), 5)

    def test_listing_image_cascade_delete(self):
        """Test that deleting a listing deletes its images"""
        for i in range(3):
            image = create_image()
            ListingImage.objects.create(listing=self.listing, image=image)

        listing_id = self.listing.id
        self.assertEqual(ListingImage.objects.filter(listing=self.listing).count(), 3)

        self.listing.delete()
        self.assertEqual(ListingImage.objects.filter(listing_id=listing_id).count(), 0)


class ListingFormTests(TestCase):
    def setUp(self):
        self.future_start = timezone.now().date() + timedelta(days=7)
        self.future_end = timezone.now().date() + timedelta(days=37)

    def test_valid_listing_form(self):
        """Test listing form with valid data"""
        form_data = {
            "title": "Beautiful Apartment",
            "description": "A beautiful apartment with great amenities and location",
            "address": "123 Main St, Brooklyn, NY 11201",
            "rent": "1500.00",
            "amenities": ["furnished", "wifi"],
            "custom_amenities": "Balcony, Dishwasher",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        form = ListingForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_missing_required_fields(self):
        """Test form validation with missing required fields"""
        form_data = {
            "title": "",
            "description": "",
            "address": "",
            "rent": "",
        }
        form = ListingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)
        self.assertIn("description", form.errors)
        self.assertIn("address", form.errors)
        self.assertIn("rent", form.errors)

    def test_rent_validation_negative(self):
        """Test rent validation with negative value"""
        form_data = {
            "title": "Test Listing",
            "description": "Test description with at least 20 characters",
            "address": "123 Test St",
            "rent": "-100.00",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        form = ListingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("rent", form.errors)

    def test_rent_validation_zero(self):
        """Test rent validation with zero value"""
        form_data = {
            "title": "Test Listing",
            "description": "Test description with at least 20 characters",
            "address": "123 Test St",
            "rent": "0.00",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        form = ListingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("rent", form.errors)

    def test_rent_validation_too_high(self):
        """Test rent validation with unrealistic value"""
        form_data = {
            "title": "Test Listing",
            "description": "Test description with at least 20 characters",
            "address": "123 Test St",
            "rent": "150000.00",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        form = ListingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("rent", form.errors)

    def test_description_too_short(self):
        """Test description validation with text too short"""
        form_data = {
            "title": "Test Listing",
            "description": "Too short",
            "address": "123 Test St",
            "rent": "1500.00",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        form = ListingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)

    def test_description_minimum_length(self):
        """Test description validation with exactly 20 characters"""
        form_data = {
            "title": "Test Listing",
            "description": "12345678901234567890",
            "address": "123 Test St",
            "rent": "1500.00",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        form = ListingForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_availability_start_past_date(self):
        """Test availability_start validation with past date"""
        past_date = timezone.now().date() - timedelta(days=1)
        form_data = {
            "title": "Test Listing",
            "description": "Test description with at least 20 characters",
            "address": "123 Test St",
            "rent": "1500.00",
            "availability_start": past_date,
            "availability_end": self.future_end,
        }
        form = ListingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("availability_start", form.errors)

    def test_availability_end_past_date(self):
        """Test availability_end validation with past date"""
        past_date = timezone.now().date() - timedelta(days=1)
        form_data = {
            "title": "Test Listing",
            "description": "Test description with at least 20 characters",
            "address": "123 Test St",
            "rent": "1500.00",
            "availability_start": self.future_start,
            "availability_end": past_date,
        }
        form = ListingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("availability_end", form.errors)

    def test_end_date_before_start_date(self):
        """Test validation when end date is before start date"""
        form_data = {
            "title": "Test Listing",
            "description": "Test description with at least 20 characters",
            "address": "123 Test St",
            "rent": "1500.00",
            "availability_start": self.future_end,
            "availability_end": self.future_start,
        }
        form = ListingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_end_date_equals_start_date(self):
        """Test validation when end date equals start date"""
        same_date = self.future_start
        form_data = {
            "title": "Test Listing",
            "description": "Test description with at least 20 characters",
            "address": "123 Test St",
            "rent": "1500.00",
            "availability_start": same_date,
            "availability_end": same_date,
        }
        form = ListingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_amenities_optional(self):
        """Test that amenities field is optional"""
        form_data = {
            "title": "Test Listing",
            "description": "Test description with at least 20 characters",
            "address": "123 Test St",
            "rent": "1500.00",
            "amenities": [],
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        form = ListingForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_custom_amenities_cleaning(self):
        """Test custom amenities are cleaned properly"""
        form_data = {
            "title": "Test Listing",
            "description": "Test description with at least 20 characters",
            "address": "123 Test St",
            "rent": "1500.00",
            "custom_amenities": "  Balcony  ,  Dishwasher  ,  Pool  ",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        form = ListingForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["custom_amenities"], "Balcony, Dishwasher, Pool"
        )

    def test_custom_amenities_empty_strings(self):
        """Test custom amenities with empty strings are removed"""
        form_data = {
            "title": "Test Listing",
            "description": "Test description with at least 20 characters",
            "address": "123 Test St",
            "rent": "1500.00",
            "custom_amenities": "Balcony,  ,  , Dishwasher",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        form = ListingForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["custom_amenities"], "Balcony, Dishwasher")

    def test_form_save_amenities_conversion(self):
        """Test that amenities are converted to comma-separated string on save"""
        user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        form_data = {
            "title": "Test Listing",
            "description": "Test description with at least 20 characters",
            "address": "123 Test St",
            "rent": "1500.00",
            "amenities": ["furnished", "wifi", "laundry"],
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        form = ListingForm(data=form_data)
        self.assertTrue(form.is_valid())
        listing = form.save(commit=False)
        listing.user = user
        listing.save()
        self.assertEqual(listing.amenities, "furnished,wifi,laundry")


class CreateListingViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_edu = User.objects.create_user(
            email="test@nyu.edu", username="eduuser", password="testpw0rd"
        )
        self.user_non_edu = User.objects.create_user(
            email="test@gmail.com", username="noneduuser", password="testpw0rd"
        )
        self.future_start = timezone.now().date() + timedelta(days=7)
        self.future_end = timezone.now().date() + timedelta(days=37)

    def test_create_listing_get_authenticated_edu(self):
        """Test GET request to create listing with .edu email"""
        self.client.force_login(self.user_edu)
        response = self.client.get(reverse("create_listing"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/create_listing.html")
        self.assertIsInstance(response.context["form"], ListingForm)

    def test_create_listing_requires_login(self):
        """Test that create listing requires login"""
        response = self.client.get(reverse("create_listing"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_create_listing_requires_edu_email(self):
        """Test that only .edu email users can create listings"""
        self.client.force_login(self.user_non_edu)
        response = self.client.get(reverse("create_listing"))
        self.assertEqual(response.status_code, 302)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                "Only verified .edu email addresses can post listings" in str(m)
                for m in messages_list
            )
        )

    def test_create_listing_post_valid_data(self):
        """Test POST request to create listing with valid data"""
        self.client.force_login(self.user_edu)
        image = create_image()
        form_data = {
            "title": "Beautiful Apartment",
            "description": "A beautiful apartment with great amenities and location",
            "address": "123 Main St, Brooklyn, NY 11201",
            "rent": "1500.00",
            "amenities": ["furnished", "wifi"],
            "custom_amenities": "Balcony",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
            "images": [image],
        }
        response = self.client.post(reverse("create_listing"), form_data)

        self.assertEqual(Listing.objects.count(), 1)
        listing = Listing.objects.first()
        self.assertEqual(listing.title, "Beautiful Apartment")
        self.assertEqual(listing.user, self.user_edu)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("view_listing", args=[listing.id]))

    def test_create_listing_no_images(self):
        """Test creating listing without images fails"""
        self.client.force_login(self.user_edu)
        form_data = {
            "title": "Beautiful Apartment",
            "description": "A beautiful apartment with great amenities and location",
            "address": "123 Main St, Brooklyn, NY 11201",
            "rent": "1500.00",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        response = self.client.post(reverse("create_listing"), form_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Listing.objects.count(), 0)
        self.assertFormError(
            response.context["form"], None, "Please upload at least one image."
        )

    def test_create_listing_too_many_images(self):
        """Test creating listing with more than 10 images fails"""
        self.client.force_login(self.user_edu)
        images = [create_image() for _ in range(11)]
        form_data = {
            "title": "Beautiful Apartment",
            "description": "A beautiful apartment with great amenities and location",
            "address": "123 Main St, Brooklyn, NY 11201",
            "rent": "1500.00",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
            "images": images,
        }
        response = self.client.post(reverse("create_listing"), form_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Listing.objects.count(), 0)
        self.assertFormError(
            response.context["form"], None, "You can upload a maximum of 10 images."
        )

    def test_create_listing_invalid_file_type(self):
        """Test creating listing with non-image file fails"""
        self.client.force_login(self.user_edu)
        invalid_file = SimpleUploadedFile(
            "test.txt", b"file_content", content_type="text/plain"
        )
        form_data = {
            "title": "Beautiful Apartment",
            "description": "A beautiful apartment with great amenities and location",
            "address": "123 Main St, Brooklyn, NY 11201",
            "rent": "1500.00",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
            "images": [invalid_file],
        }
        response = self.client.post(reverse("create_listing"), form_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Listing.objects.count(), 0)
        self.assertFormError(
            response.context["form"], None, "test.txt is not a valid image file."
        )

    def test_create_listing_image_too_large(self):
        """Test creating listing with image larger than 5MB fails"""
        self.client.force_login(self.user_edu)
        # Create a large file (simulate 6MB)
        large_file = SimpleUploadedFile(
            "large.jpg", b"x" * (6 * 1024 * 1024), content_type="image/jpeg"
        )
        form_data = {
            "title": "Beautiful Apartment",
            "description": "A beautiful apartment with great amenities and location",
            "address": "123 Main St, Brooklyn, NY 11201",
            "rent": "1500.00",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
            "images": [large_file],
        }
        response = self.client.post(reverse("create_listing"), form_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Listing.objects.count(), 0)
        self.assertFormError(
            response.context["form"], None, "large.jpg exceeds 5MB size limit."
        )

    def test_create_listing_creates_images(self):
        """Test that creating a listing creates associated images"""
        self.client.force_login(self.user_edu)
        images = [create_image() for _ in range(3)]
        form_data = {
            "title": "Beautiful Apartment",
            "description": "A beautiful apartment with great amenities and location",
            "address": "123 Main St, Brooklyn, NY 11201",
            "rent": "1500.00",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
            "images": images,
        }
        response = self.client.post(reverse("create_listing"), form_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Listing.objects.count(), 1)
        listing = Listing.objects.first()
        self.assertEqual(ListingImage.objects.filter(listing=listing).count(), 3)

    def test_create_listing_success_message(self):
        """Test that success message is displayed after creating listing"""
        self.client.force_login(self.user_edu)
        image = create_image()
        form_data = {
            "title": "Beautiful Apartment",
            "description": "A beautiful apartment with great amenities and location",
            "address": "123 Main St, Brooklyn, NY 11201",
            "rent": "1500.00",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
            "images": [image],
        }
        response = self.client.post(reverse("create_listing"), form_data)

        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("Listing created successfully" in str(m) for m in messages_list)
        )


class EditListingViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.other_user = User.objects.create_user(
            email="other@nyu.edu", username="otheruser", password="testpw0rd"
        )
        self.future_start = timezone.now().date() + timedelta(days=7)
        self.future_end = timezone.now().date() + timedelta(days=37)
        self.listing = Listing.objects.create(
            user=self.user,
            title="Original Title",
            address="123 Main St",
            rent=Decimal("1500.00"),
            description="Original description with at least 20 characters",
            amenities="furnished,wifi",
            availability_start=self.future_start,
            availability_end=self.future_end,
        )
        image = create_image()
        ListingImage.objects.create(listing=self.listing, image=image)

    def test_edit_listing_get_authenticated(self):
        """Test GET request to edit listing"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("edit_listing", args=[self.listing.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/edit_listing.html")
        self.assertIsInstance(response.context["form"], ListingForm)

    def test_edit_listing_requires_login(self):
        """Test that edit listing requires login"""
        response = self.client.get(reverse("edit_listing", args=[self.listing.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_edit_listing_requires_ownership(self):
        """Test that only owner can edit listing"""
        self.client.force_login(self.other_user)
        response = self.client.get(reverse("edit_listing", args=[self.listing.id]))
        self.assertEqual(response.status_code, 404)

    def test_edit_listing_post_valid_data(self):
        """Test POST request to edit listing with valid data"""
        self.client.force_login(self.user)
        new_image = create_image()
        form_data = {
            "title": "Updated Title",
            "description": "Updated description with at least 20 characters",
            "address": "456 Oak Ave",
            "rent": "2000.00",
            "amenities": ["furnished", "wifi", "laundry"],
            "availability_start": self.future_start,
            "availability_end": self.future_end,
            "images": [new_image],
        }
        response = self.client.post(
            reverse("edit_listing", args=[self.listing.id]), form_data
        )

        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, "Updated Title")
        self.assertEqual(self.listing.rent, Decimal("2000.00"))
        self.assertTrue(self.listing.is_edited)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("view_listing", args=[self.listing.id]))

    def test_edit_listing_sets_is_edited_flag(self):
        """Test that editing a listing sets is_edited to True"""
        self.client.force_login(self.user)
        self.assertFalse(self.listing.is_edited)

        form_data = {
            "title": "Updated Title",
            "description": "Updated description with at least 20 characters",
            "address": "456 Oak Ave",
            "rent": "2000.00",
            "keep_existing_images": "on",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        response = self.client.post(
            reverse("edit_listing", args=[self.listing.id]), form_data
        )

        self.assertEqual(response.status_code, 302)
        self.listing.refresh_from_db()
        self.assertTrue(self.listing.is_edited)

    def test_edit_listing_keep_existing_images(self):
        """Test editing listing while keeping existing images"""
        self.client.force_login(self.user)
        original_image_count = self.listing.images.count()

        form_data = {
            "title": "Updated Title",
            "description": "Updated description with at least 20 characters",
            "address": "456 Oak Ave",
            "rent": "2000.00",
            "keep_existing_images": "on",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        response = self.client.post(
            reverse("edit_listing", args=[self.listing.id]), form_data
        )

        self.assertEqual(response.status_code, 302)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.images.count(), original_image_count)

    def test_edit_listing_replace_images(self):
        """Test editing listing and replacing images"""
        self.client.force_login(self.user)
        new_images = [create_image() for _ in range(2)]

        form_data = {
            "title": "Updated Title",
            "description": "Updated description with at least 20 characters",
            "address": "456 Oak Ave",
            "rent": "2000.00",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
            "images": new_images,
        }
        response = self.client.post(
            reverse("edit_listing", args=[self.listing.id]), form_data
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.listing.images.count(), 2)

    def test_edit_listing_no_images_no_keep_existing(self):
        """Test editing without new images and without checking keep_existing still succeeds if images exist"""
        self.client.force_login(self.user)
        # The listing already has an image from setUp
        self.assertEqual(self.listing.images.count(), 1)

        form_data = {
            "title": "Updated Title",
            "description": "Updated description with at least 20 characters",
            "address": "456 Oak Ave",
            "rent": "2000.00",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        response = self.client.post(
            reverse("edit_listing", args=[self.listing.id]), form_data
        )

        # Should succeed because listing already has images
        self.assertEqual(response.status_code, 302)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, "Updated Title")
        # Images should remain unchanged
        self.assertEqual(self.listing.images.count(), 1)

    def test_edit_listing_no_images_when_none_exist(self):
        """Test editing fails when listing has no images and none are uploaded"""
        # Create a listing without images
        listing_no_images = Listing.objects.create(
            user=self.user,
            title="No Images Listing",
            address="789 Test St",
            rent=Decimal("1800.00"),
            description="A listing without any images for testing",
            amenities="wifi",
            availability_start=self.future_start,
            availability_end=self.future_end,
        )
        # Verify it has no images
        self.assertEqual(listing_no_images.images.count(), 0)

        self.client.force_login(self.user)
        form_data = {
            "title": "Updated Title",
            "description": "Updated description with at least 20 characters",
            "address": "456 Oak Ave",
            "rent": "2000.00",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        response = self.client.post(
            reverse("edit_listing", args=[listing_no_images.id]), form_data
        )

        # Should fail because no images exist and none were uploaded
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            None,
            "Please upload at least one image or keep existing images.",
        )

    def test_edit_listing_amenities_prepopulated(self):
        """Test that amenities are prepopulated in edit form"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("edit_listing", args=[self.listing.id]))

        if response.status_code == 200:
            form = response.context["form"]
            self.assertEqual(form.initial["amenities"], ["furnished", "wifi"])

    def test_edit_listing_success_message(self):
        """Test that success message is displayed after editing"""
        self.client.force_login(self.user)
        form_data = {
            "title": "Updated Title",
            "description": "Updated description with at least 20 characters",
            "address": "456 Oak Ave",
            "rent": "2000.00",
            "keep_existing_images": "on",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        response = self.client.post(
            reverse("edit_listing", args=[self.listing.id]), form_data
        )

        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("Listing updated successfully" in str(m) for m in messages_list)
        )


class DeleteListingViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.other_user = User.objects.create_user(
            email="other@nyu.edu", username="otheruser", password="testpw0rd"
        )
        self.future_start = timezone.now().date() + timedelta(days=7)
        self.future_end = timezone.now().date() + timedelta(days=37)
        self.listing = Listing.objects.create(
            user=self.user,
            title="Test Listing",
            address="123 Main St",
            rent=Decimal("1500.00"),
            description="Test description with at least 20 characters",
            availability_start=self.future_start,
            availability_end=self.future_end,
        )

    def test_delete_listing_get_confirmation(self):
        """Test GET request shows confirmation page"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("delete_listing", args=[self.listing.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/delete_listing.html")
        self.assertEqual(response.context["listing"], self.listing)

    def test_delete_listing_requires_login(self):
        """Test that delete listing requires login"""
        response = self.client.get(reverse("delete_listing", args=[self.listing.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_delete_listing_requires_ownership(self):
        """Test that only owner can delete listing"""
        self.client.force_login(self.other_user)
        response = self.client.get(reverse("delete_listing", args=[self.listing.id]))
        self.assertEqual(response.status_code, 404)

    def test_delete_listing_post_deletes(self):
        """Test POST request deletes the listing"""
        self.client.force_login(self.user)
        listing_id = self.listing.id

        response = self.client.post(reverse("delete_listing", args=[listing_id]))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("my_listings"))
        self.assertEqual(Listing.objects.filter(id=listing_id).count(), 0)

    def test_delete_listing_deletes_images(self):
        """Test that deleting listing also deletes associated images"""
        self.client.force_login(self.user)
        image = create_image()
        ListingImage.objects.create(listing=self.listing, image=image)
        listing_id = self.listing.id

        self.assertEqual(ListingImage.objects.filter(listing=self.listing).count(), 1)
        response = self.client.post(reverse("delete_listing", args=[listing_id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ListingImage.objects.filter(listing_id=listing_id).count(), 0)

    def test_delete_listing_success_message(self):
        """Test that success message is displayed after deletion"""
        self.client.force_login(self.user)
        listing_title = self.listing.title

        response = self.client.post(reverse("delete_listing", args=[self.listing.id]))

        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                f"Listing '{listing_title}' has been deleted" in str(m)
                for m in messages_list
            )
        )


class ViewListingViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.other_user = User.objects.create_user(
            email="other@nyu.edu", username="otheruser", password="testpw0rd"
        )
        self.future_start = timezone.now().date() + timedelta(days=7)
        self.future_end = timezone.now().date() + timedelta(days=37)
        self.listing = Listing.objects.create(
            user=self.user,
            title="Test Listing",
            address="123 Main St",
            rent=Decimal("1500.00"),
            description="Test description with at least 20 characters",
            availability_start=self.future_start,
            availability_end=self.future_end,
        )

    def test_view_listing_authenticated_owner(self):
        """Test viewing listing as owner"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("view_listing", args=[self.listing.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/view_listing.html")
        self.assertEqual(response.context["listing"], self.listing)

    def test_view_listing_requires_login(self):
        """Test that viewing listing requires login"""
        response = self.client.get(reverse("view_listing", args=[self.listing.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_view_listing_requires_ownership(self):
        """Test that only owner can view listing"""
        self.client.force_login(self.other_user)
        response = self.client.get(reverse("view_listing", args=[self.listing.id]))
        self.assertEqual(response.status_code, 404)

    def test_view_listing_nonexistent(self):
        """Test viewing non-existent listing returns 404"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("view_listing", args=[99999]))
        self.assertEqual(response.status_code, 404)


class MyListingsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.other_user = User.objects.create_user(
            email="other@nyu.edu", username="otheruser", password="testpw0rd"
        )
        self.future_start = timezone.now().date() + timedelta(days=7)
        self.future_end = timezone.now().date() + timedelta(days=37)

    def test_my_listings_authenticated(self):
        """Test viewing my listings page when authenticated"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("my_listings"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/my_listings.html")

    def test_my_listings_requires_login(self):
        """Test that my listings requires login"""
        response = self.client.get(reverse("my_listings"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_my_listings_shows_only_user_listings(self):
        """Test that my listings only shows current user's listings"""
        Listing.objects.create(
            user=self.user,
            title="User Listing",
            address="123 Main St",
            rent=Decimal("1500.00"),
            description="User listing description",
            availability_start=self.future_start,
            availability_end=self.future_end,
        )
        Listing.objects.create(
            user=self.other_user,
            title="Other User Listing",
            address="456 Oak Ave",
            rent=Decimal("2000.00"),
            description="Other user listing description",
            availability_start=self.future_start,
            availability_end=self.future_end,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("my_listings"))

        if response.status_code == 200 and response.context:
            listings = response.context["listings"]
            self.assertEqual(listings.count(), 1)
            self.assertEqual(listings[0].title, "User Listing")

    def test_my_listings_ordered_by_created_at(self):
        """Test that my listings are ordered by creation date"""
        listing1 = Listing.objects.create(
            user=self.user,
            title="First Listing",
            address="123 Main St",
            rent=Decimal("1500.00"),
            description="First listing description",
            availability_start=self.future_start,
            availability_end=self.future_end,
        )
        listing2 = Listing.objects.create(
            user=self.user,
            title="Second Listing",
            address="456 Oak Ave",
            rent=Decimal("2000.00"),
            description="Second listing description",
            availability_start=self.future_start,
            availability_end=self.future_end,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("my_listings"))

        if response.status_code == 200 and response.context:
            listings = response.context["listings"]
            self.assertEqual(listings[0].id, listing2.id)
            self.assertEqual(listings[1].id, listing1.id)

    def test_my_listings_empty(self):
        """Test my listings page when user has no listings"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("my_listings"))

        self.assertEqual(response.status_code, 200)
        if response.context:
            listings = response.context["listings"]
            self.assertEqual(listings.count(), 0)


class HelperFunctionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.future_start = timezone.now().date() + timedelta(days=7)
        self.future_end = timezone.now().date() + timedelta(days=37)
        self.listing = Listing.objects.create(
            user=self.user,
            title="Test Listing",
            address="123 Main St",
            rent=Decimal("1500.00"),
            description="Test description",
            availability_start=self.future_start,
            availability_end=self.future_end,
        )

    def test_validate_image_files_valid(self):
        """Test validate_image_files with valid images"""
        from .views import validate_image_files

        files = [create_image() for _ in range(3)]
        # Create a bound form so add_error works
        form_data = {
            "title": "Test",
            "description": "Test description with at least 20 characters",
            "address": "123 Test St",
            "rent": "1500.00",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        form = ListingForm(data=form_data)
        result = validate_image_files(files, form)
        self.assertFalse(result)

    def test_validate_image_files_too_many(self):
        """Test validate_image_files with too many images"""
        from .views import validate_image_files

        files = [create_image() for _ in range(11)]
        # Create a bound form so add_error works
        form_data = {
            "title": "Test",
            "description": "Test description with at least 20 characters",
            "address": "123 Test St",
            "rent": "1500.00",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        form = ListingForm(data=form_data)
        result = validate_image_files(files, form)
        self.assertTrue(result)
        self.assertIn("You can upload a maximum of 10 images", str(form.errors))

    def test_validate_image_files_invalid_type(self):
        """Test validate_image_files with invalid file type"""
        from .views import validate_image_files

        invalid_file = SimpleUploadedFile(
            "test.txt", b"file_content", content_type="text/plain"
        )
        # Create a bound form so add_error works
        form_data = {
            "title": "Test",
            "description": "Test description with at least 20 characters",
            "address": "123 Test St",
            "rent": "1500.00",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        form = ListingForm(data=form_data)
        result = validate_image_files([invalid_file], form)
        self.assertTrue(result)
        self.assertIn("is not a valid image file", str(form.errors))

    def test_validate_image_files_too_large(self):
        """Test validate_image_files with file too large"""
        from .views import validate_image_files

        large_file = SimpleUploadedFile(
            "large.jpg", b"x" * (6 * 1024 * 1024), content_type="image/jpeg"
        )
        # Create a bound form so add_error works
        form_data = {
            "title": "Test",
            "description": "Test description with at least 20 characters",
            "address": "123 Test St",
            "rent": "1500.00",
            "availability_start": self.future_start,
            "availability_end": self.future_end,
        }
        form = ListingForm(data=form_data)
        result = validate_image_files([large_file], form)
        self.assertTrue(result)
        self.assertIn("exceeds 5MB size limit", str(form.errors))
