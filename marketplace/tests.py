from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages
from io import BytesIO
from PIL import Image
from decimal import Decimal
from marketplace.models import Item, ItemImage
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


class ItemModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.item = Item.objects.create(
            user=self.user,
            title="Test Item",
            description="This is a test item description with at least 20 characters",
            condition="good",
            price=Decimal("50.00"),
            address="Bobst Library",
        )

    def test_create_item_success(self):
        """Test creating an item with valid data"""
        item = self.item
        self.assertIsNotNone(item)
        self.assertEqual(item.user, self.user)
        self.assertEqual(item.title, "Test Item")
        self.assertEqual(
            item.description,
            "This is a test item description with at least 20 characters",
        )
        self.assertEqual(item.condition, "good")
        self.assertEqual(item.price, Decimal("50.00"))
        self.assertEqual(item.address, "Bobst Library")
        self.assertEqual(Item.objects.filter(user=self.user).count(), 1)

    def test_item_defaults(self):
        """Test default values for item fields"""
        user2 = User.objects.create_user(
            email="test2@nyu.edu", username="test2user", password="testpw0rd"
        )
        before = timezone.now()
        item = Item.objects.create(
            user=user2,
            title="Another Item",
            description="This is another test item description",
            condition="new",
            price=Decimal("100.00"),
            address="Silver Center",
        )
        after = timezone.now()

        self.assertFalse(item.is_edited)
        self.assertFalse(item.is_sold)
        self.assertTrue(item.is_active)
        self.assertGreaterEqual(item.created_at, before)
        self.assertLessEqual(item.created_at, after)

    def test_item_condition_choices(self):
        """Test valid condition choices"""
        valid_conditions = ["new", "like_new", "good", "fair", "poor"]
        for condition in valid_conditions:
            item = Item.objects.create(
                user=self.user,
                title=f"Item {condition}",
                description="Test description with sufficient length",
                condition=condition,
                price=Decimal("25.00"),
                address="Test Location",
            )
            self.assertEqual(item.condition, condition)

    def test_item_str(self):
        """Test Item string representation"""
        self.assertEqual(str(self.item), "Test Item - testuser")

    def test_item_ordering(self):
        """Test items are ordered by created_at descending"""
        item2 = Item.objects.create(
            user=self.user,
            title="Newer Item",
            description="This is a newer test item description",
            condition="new",
            price=Decimal("75.00"),
            address="Kimmel Center",
        )
        items = list(Item.objects.all())
        self.assertEqual(items[0], item2)
        self.assertEqual(items[1], self.item)

    def test_delete_cascade_user(self):
        """Test item deletion when user is deleted"""
        self.assertTrue(Item.objects.filter(user=self.user).exists())
        self.user.delete()
        self.assertFalse(Item.objects.filter(user_id=self.user.id).exists())

    def test_item_update_timestamp(self):
        """Test updated_at timestamp changes on save"""
        original_updated = self.item.updated_at
        self.item.price = Decimal("60.00")
        self.item.save()
        self.item.refresh_from_db()
        self.assertGreater(self.item.updated_at, original_updated)

    def test_latitude_longitude_defaults(self):
        """Test latitude and longitude default to None"""
        self.assertIsNone(self.item.latitude)
        self.assertIsNone(self.item.longitude)

    def test_latitude_longitude_can_be_set(self):
        """Test latitude and longitude can be set"""
        self.item.latitude = 40.7128
        self.item.longitude = -74.0060
        self.item.save()
        self.item.refresh_from_db()
        self.assertEqual(self.item.latitude, 40.7128)
        self.assertEqual(self.item.longitude, -74.0060)


class ItemImageModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.item = Item.objects.create(
            user=self.user,
            title="Test Item",
            description="This is a test item description with at least 20 characters",
            condition="good",
            price=Decimal("50.00"),
            address="Bobst Library",
        )

    def test_create_item_image(self):
        """Test creating an item image"""
        image = create_image()
        item_image = ItemImage.objects.create(item=self.item, image=image)
        self.assertIsNotNone(item_image)
        self.assertEqual(item_image.item, self.item)
        self.assertEqual(ItemImage.objects.filter(item=self.item).count(), 1)

    def test_item_image_str(self):
        """Test ItemImage string representation"""
        image = create_image()
        item_image = ItemImage.objects.create(item=self.item, image=image)
        self.assertEqual(str(item_image), "Image for Test Item")

    def test_item_image_delete_cascade(self):
        """Test images are deleted when item is deleted"""
        image1 = create_image()
        image2 = create_image()
        ItemImage.objects.create(item=self.item, image=image1)
        ItemImage.objects.create(item=self.item, image=image2)
        self.assertEqual(ItemImage.objects.filter(item=self.item).count(), 2)
        self.item.delete()
        self.assertEqual(ItemImage.objects.filter(item_id=self.item.id).count(), 0)

    def test_item_images_related_name(self):
        """Test accessing images through related_name"""
        image1 = create_image()
        image2 = create_image()
        ItemImage.objects.create(item=self.item, image=image1)
        ItemImage.objects.create(item=self.item, image=image2)
        self.assertEqual(self.item.images.count(), 2)


class ItemFormTests(TestCase):
    def setUp(self):
        self.valid_data = {
            "title": "Valid Item",
            "description": "This is a valid description with more than 20 characters",
            "condition": "good",
            "category": "other",
            "price": "50.00",
            "address": "Bobst Library",
        }

    def test_valid_form(self):
        """Test form with valid data"""
        from marketplace.forms import ItemForm

        form = ItemForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_price_validation_negative(self):
        """Test price validation rejects negative values"""
        from marketplace.forms import ItemForm

        data = {**self.valid_data, "price": "-10.00"}
        form = ItemForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)
        self.assertIn("Price must be a positive value.", form.errors["price"])

    def test_price_validation_zero(self):
        """Test price validation rejects zero"""
        from marketplace.forms import ItemForm

        data = {**self.valid_data, "price": "0.00"}
        form = ItemForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)
        self.assertIn("Price must be a positive value.", form.errors["price"])

    def test_price_validation_too_high(self):
        """Test price validation rejects unrealistic high values"""
        from marketplace.forms import ItemForm

        data = {**self.valid_data, "price": "100001.00"}
        form = ItemForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)
        self.assertIn(
            "Price amount seems unrealistic. Please verify.", form.errors["price"]
        )

    def test_price_validation_valid_edge_cases(self):
        """Test price validation accepts valid edge cases"""
        from marketplace.forms import ItemForm

        test_cases = ["0.50", "100.00", "99999.99", "100000.00"]
        for price in test_cases:
            with self.subTest(price=price):
                data = {**self.valid_data, "price": price}
                form = ItemForm(data=data)
                self.assertTrue(form.is_valid())

    def test_description_validation_too_short(self):
        """Test description validation rejects short descriptions"""
        from marketplace.forms import ItemForm

        data = {**self.valid_data, "description": "Too short"}
        form = ItemForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)
        self.assertIn(
            "Description must be at least 20 characters long.",
            form.errors["description"],
        )

    def test_description_validation_minimum_length(self):
        """Test description validation accepts minimum valid length"""
        from marketplace.forms import ItemForm

        data = {**self.valid_data, "description": "a" * 20}
        form = ItemForm(data=data)
        self.assertTrue(form.is_valid())

    def test_required_fields(self):
        """Test all required fields are validated"""
        from marketplace.forms import ItemForm

        required_fields = [
            "title",
            "description",
            "condition",
            "price",
            "address",
        ]
        for field in required_fields:
            with self.subTest(field=field):
                data = {**self.valid_data}
                del data[field]
                form = ItemForm(data=data)
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)


class CreateItemViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.non_edu_user = User.objects.create_user(
            email="test@gmail.com", username="noneduuser", password="testpw0rd"
        )
        self.create_item_url = reverse("create_item")
        self.valid_data = {
            "title": "Test Item",
            "description": "This is a test item description with at least 20 characters",
            "condition": "good",
            "category": "other",
            "price": "50.00",
            "address": "Bobst Library",
        }

    def test_create_item_success(self):
        """Test creating an item with valid data and images"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        image = create_image()
        data = {**self.valid_data, "images": [image]}
        response = self.client.post(self.create_item_url, data)

        self.assertEqual(Item.objects.filter(user=self.user).count(), 1)
        item = Item.objects.get(user=self.user)
        self.assertEqual(item.title, "Test Item")
        self.assertEqual(item.images.count(), 1)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("view_item", kwargs={"item_id": item.id})
        )

    def test_create_item_multiple_images(self):
        """Test creating an item with multiple images"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        images = [create_image() for _ in range(3)]
        data = {**self.valid_data, "images": images}
        self.client.post(self.create_item_url, data)

        self.assertEqual(Item.objects.filter(user=self.user).count(), 1)
        item = Item.objects.get(user=self.user)
        self.assertEqual(item.images.count(), 3)

    def test_create_item_no_images(self):
        """Test creating an item without images fails"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        response = self.client.post(self.create_item_url, self.valid_data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "marketplace/create_item.html")
        self.assertEqual(Item.objects.filter(user=self.user).count(), 0)

    def test_create_item_too_many_images(self):
        """Test creating an item with more than 10 images fails"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        images = [create_image() for _ in range(11)]
        data = {**self.valid_data, "images": images}
        response = self.client.post(self.create_item_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Item.objects.filter(user=self.user).count(), 0)

    def test_create_item_invalid_image_type(self):
        """Test creating an item with non-image file fails"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        text_file = SimpleUploadedFile(
            "test.txt", b"not an image", content_type="text/plain"
        )
        data = {**self.valid_data, "images": [text_file]}
        response = self.client.post(self.create_item_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Item.objects.filter(user=self.user).count(), 0)

    def test_create_item_image_too_large(self):
        """Test creating an item with oversized image fails"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        large_file = SimpleUploadedFile(
            "large.jpg", b"x" * (6 * 1024 * 1024), content_type="image/jpeg"
        )
        data = {**self.valid_data, "images": [large_file]}
        response = self.client.post(self.create_item_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Item.objects.filter(user=self.user).count(), 0)

    def test_create_item_non_edu_email(self):
        """Test non-.edu email cannot create items"""
        self.client.login(email="test@gmail.com", password="testpw0rd")
        image = create_image()
        data = {**self.valid_data, "images": [image]}
        response = self.client.post(self.create_item_url, data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Item.objects.filter(user=self.non_edu_user).count(), 0)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                "Only verified .edu email addresses can post items" in str(m)
                for m in messages_list
            )
        )

    def test_create_item_not_logged_in(self):
        """Test unauthenticated user is redirected to login"""
        image = create_image()
        data = {**self.valid_data, "images": [image]}
        response = self.client.post(self.create_item_url, data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/marketplace/create/")
        self.assertEqual(Item.objects.count(), 0)

    def test_create_item_get_request(self):
        """Test GET request displays the form"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        response = self.client.get(self.create_item_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "marketplace/create_item.html")
        self.assertIn("form", response.context)

    def test_create_item_form_validation_errors(self):
        """Test form validation errors are displayed"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        image = create_image()
        invalid_data = {**self.valid_data, "price": "-10.00", "images": [image]}
        response = self.client.post(self.create_item_url, invalid_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Item.objects.filter(user=self.user).count(), 0)
        form = response.context["form"]
        self.assertFalse(form.is_valid())


class MyItemsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.user2 = User.objects.create_user(
            email="test2@nyu.edu", username="testuser2", password="testpw0rd"
        )
        self.my_items_url = reverse("my_items")

    def test_my_items_view_success(self):
        """Test viewing user's items"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        item1 = Item.objects.create(
            user=self.user,
            title="Item 1",
            description="Description for item 1 with sufficient length",
            condition="good",
            price=Decimal("25.00"),
            address="Location 1",
        )
        item2 = Item.objects.create(
            user=self.user,
            title="Item 2",
            description="Description for item 2 with sufficient length",
            condition="new",
            price=Decimal("50.00"),
            address="Location 2",
        )

        response = self.client.get(self.my_items_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "marketplace/my_items.html")
        self.assertIn("items", response.context)
        items = list(response.context["items"])
        self.assertEqual(len(items), 2)
        self.assertIn(item1, items)
        self.assertIn(item2, items)

    def test_my_items_ordering(self):
        """Test items are ordered by creation date descending"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        item1 = Item.objects.create(
            user=self.user,
            title="Old Item",
            description="Description for old item with sufficient length",
            condition="good",
            price=Decimal("25.00"),
            address="Location 1",
        )
        item2 = Item.objects.create(
            user=self.user,
            title="New Item",
            description="Description for new item with sufficient length",
            condition="new",
            price=Decimal("50.00"),
            address="Location 2",
        )

        response = self.client.get(self.my_items_url)
        items = list(response.context["items"])
        self.assertEqual(items[0], item2)
        self.assertEqual(items[1], item1)

    def test_my_items_excludes_other_users(self):
        """Test only current user's items are displayed"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        my_item = Item.objects.create(
            user=self.user,
            title="My Item",
            description="Description for my item with sufficient length",
            condition="good",
            price=Decimal("25.00"),
            address="My Location",
        )
        other_item = Item.objects.create(
            user=self.user2,
            title="Other Item",
            description="Description for other item with sufficient length",
            condition="good",
            price=Decimal("25.00"),
            address="Other Location",
        )

        response = self.client.get(self.my_items_url)
        items = list(response.context["items"])
        self.assertIn(my_item, items)
        self.assertNotIn(other_item, items)

    def test_my_items_empty(self):
        """Test viewing with no items"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        response = self.client.get(self.my_items_url)

        self.assertEqual(response.status_code, 200)
        items = list(response.context["items"])
        self.assertEqual(len(items), 0)

    def test_my_items_not_logged_in(self):
        """Test unauthenticated user is redirected"""
        response = self.client.get(self.my_items_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/marketplace/my-items/")


class ViewItemViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.user2 = User.objects.create_user(
            email="test2@nyu.edu", username="testuser2", password="testpw0rd"
        )
        self.item = Item.objects.create(
            user=self.user,
            title="Test Item",
            description="Test description with sufficient length",
            condition="good",
            price=Decimal("50.00"),
            address="Test Location",
        )

    def test_view_item_success(self):
        """Test viewing own item"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        url = reverse("view_item", kwargs={"item_id": self.item.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "marketplace/view_item.html")
        self.assertEqual(response.context["item"], self.item)

    def test_view_item_not_owner(self):
        """Test user can view other user's item but cannot edit/delete"""
        self.client.login(email="test2@nyu.edu", password="testpw0rd")
        url = reverse("view_item", kwargs={"item_id": self.item.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["is_owner"])

    def test_view_item_not_found(self):
        """Test viewing non-existent item returns 404"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        url = reverse("view_item", kwargs={"item_id": 99999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_view_item_not_logged_in(self):
        """Test unauthenticated user is redirected"""
        url = reverse("view_item", kwargs={"item_id": self.item.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)


class EditItemViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.user2 = User.objects.create_user(
            email="test2@nyu.edu", username="testuser2", password="testpw0rd"
        )
        self.item = Item.objects.create(
            user=self.user,
            title="Original Title",
            description="Original description with sufficient length",
            condition="good",
            price=Decimal("50.00"),
            address="Original Location",
        )
        image = create_image()
        self.item_image = ItemImage.objects.create(item=self.item, image=image)

    def test_edit_item_get(self):
        """Test GET request displays edit form"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        url = reverse("edit_item", kwargs={"item_id": self.item.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "marketplace/edit_item.html")
        self.assertIn("form", response.context)
        self.assertIn("item", response.context)

    def test_edit_item_success(self):
        """Test editing item with valid data"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        url = reverse("edit_item", kwargs={"item_id": self.item.id})
        data = {
            "title": "Updated Title",
            "description": "Updated description with sufficient length for validation",
            "condition": "like_new",
            "category": "other",
            "price": "75.00",
            "address": "Updated Location",
        }
        response = self.client.post(url, data)

        self.item.refresh_from_db()
        self.assertEqual(self.item.title, "Updated Title")
        self.assertEqual(self.item.price, Decimal("75.00"))
        self.assertTrue(self.item.is_edited)
        self.assertEqual(response.status_code, 302)

    def test_edit_item_add_images(self):
        """Test adding new images to item"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        url = reverse("edit_item", kwargs={"item_id": self.item.id})
        new_images = [create_image() for _ in range(2)]
        data = {
            "title": self.item.title,
            "description": self.item.description,
            "condition": self.item.condition,
            "category": "other",
            "price": str(self.item.price),
            "address": self.item.address,
            "images": new_images,
        }
        self.client.post(url, data)

        self.item.refresh_from_db()
        self.assertEqual(self.item.images.count(), 3)

    def test_edit_item_remove_image_but_keep_one(self):
        """Test removing images while keeping at least one"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        image2 = create_image()
        ItemImage.objects.create(item=self.item, image=image2)

        url = reverse("edit_item", kwargs={"item_id": self.item.id})
        data = {
            "title": self.item.title,
            "description": self.item.description,
            "condition": self.item.condition,
            "category": "other",
            "price": str(self.item.price),
            "address": self.item.address,
            "removed_images": str(self.item_image.id),
        }
        self.client.post(url, data)

        self.item.refresh_from_db()
        self.assertEqual(self.item.images.count(), 1)
        self.assertFalse(ItemImage.objects.filter(id=self.item_image.id).exists())

    def test_edit_item_cannot_remove_all_images(self):
        """Test cannot remove all images without adding new ones"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        url = reverse("edit_item", kwargs={"item_id": self.item.id})
        data = {
            "title": self.item.title,
            "description": self.item.description,
            "condition": self.item.condition,
            "category": "other",
            "price": str(self.item.price),
            "address": self.item.address,
            "removed_images": str(self.item_image.id),
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.images.count(), 1)

    def test_edit_item_remove_and_add_images(self):
        """Test removing old images and adding new ones"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        url = reverse("edit_item", kwargs={"item_id": self.item.id})
        new_image = create_image()
        data = {
            "title": self.item.title,
            "description": self.item.description,
            "condition": self.item.condition,
            "category": "other",
            "price": str(self.item.price),
            "address": self.item.address,
            "removed_images": str(self.item_image.id),
            "images": [new_image],
        }
        self.client.post(url, data)

        self.item.refresh_from_db()
        self.assertEqual(self.item.images.count(), 1)
        self.assertFalse(ItemImage.objects.filter(id=self.item_image.id).exists())

    def test_edit_item_not_owner(self):
        """Test user cannot edit other user's item"""
        self.client.login(email="test2@nyu.edu", password="testpw0rd")
        url = reverse("edit_item", kwargs={"item_id": self.item.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_edit_item_not_logged_in(self):
        """Test unauthenticated user is redirected"""
        url = reverse("edit_item", kwargs={"item_id": self.item.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)


class DeleteItemViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.user2 = User.objects.create_user(
            email="test2@nyu.edu", username="testuser2", password="testpw0rd"
        )
        self.item = Item.objects.create(
            user=self.user,
            title="Test Item",
            description="Test description with sufficient length",
            condition="good",
            price=Decimal("50.00"),
            address="Test Location",
        )

    def test_delete_item_get_confirmation(self):
        """Test GET request shows confirmation page"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        url = reverse("delete_item", kwargs={"item_id": self.item.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "marketplace/delete_item.html")
        self.assertEqual(response.context["item"], self.item)

    def test_delete_item_post_success(self):
        """Test POST request deletes item"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        url = reverse("delete_item", kwargs={"item_id": self.item.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("my_items"))
        self.assertFalse(Item.objects.filter(id=self.item.id).exists())

    def test_delete_item_confirmation_message(self):
        """Test deletion shows success message"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        url = reverse("delete_item", kwargs={"item_id": self.item.id})
        response = self.client.post(url)

        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("deleted successfully" in str(m) for m in messages_list))

    def test_delete_item_not_owner(self):
        """Test user cannot delete other user's item"""
        self.client.login(email="test2@nyu.edu", password="testpw0rd")
        url = reverse("delete_item", kwargs={"item_id": self.item.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Item.objects.filter(id=self.item.id).exists())

    def test_delete_item_not_logged_in(self):
        """Test unauthenticated user is redirected"""
        url = reverse("delete_item", kwargs={"item_id": self.item.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Item.objects.filter(id=self.item.id).exists())

    def test_delete_item_with_images(self):
        """Test deleting item also deletes associated images"""
        image = create_image()
        ItemImage.objects.create(item=self.item, image=image)

        self.client.login(email="test@nyu.edu", password="testpw0rd")
        url = reverse("delete_item", kwargs={"item_id": self.item.id})
        self.client.post(url)

        self.assertFalse(Item.objects.filter(id=self.item.id).exists())
        self.assertEqual(ItemImage.objects.filter(item_id=self.item.id).count(), 0)


class MarkAsSoldViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.user2 = User.objects.create_user(
            email="test2@nyu.edu", username="testuser2", password="testpw0rd"
        )
        self.item = Item.objects.create(
            user=self.user,
            title="Test Item",
            description="Test description with sufficient length",
            condition="good",
            price=Decimal("50.00"),
            address="Test Location",
        )

    def test_mark_as_sold_success(self):
        """Test marking item as sold"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        url = reverse("mark_as_sold", kwargs={"item_id": self.item.id})
        response = self.client.post(url)

        self.item.refresh_from_db()
        self.assertTrue(self.item.is_sold)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("my_items"))

    def test_mark_as_sold_message(self):
        """Test marking as sold shows success message"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        url = reverse("mark_as_sold", kwargs={"item_id": self.item.id})
        response = self.client.post(url)

        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("marked as sold" in str(m) for m in messages_list))

    def test_mark_as_sold_not_owner(self):
        """Test user cannot mark other user's item as sold"""
        self.client.login(email="test2@nyu.edu", password="testpw0rd")
        url = reverse("mark_as_sold", kwargs={"item_id": self.item.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)
        self.item.refresh_from_db()
        self.assertFalse(self.item.is_sold)

    def test_mark_as_sold_not_logged_in(self):
        """Test unauthenticated user is redirected"""
        url = reverse("mark_as_sold", kwargs={"item_id": self.item.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.item.refresh_from_db()
        self.assertFalse(self.item.is_sold)

    def test_mark_as_sold_get_request(self):
        """Test GET request redirects to view_item"""
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        url = reverse("mark_as_sold", kwargs={"item_id": self.item.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("view_item", kwargs={"item_id": self.item.id})
        )
        self.item.refresh_from_db()
        self.assertFalse(self.item.is_sold)


class HelperFunctionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )

    def test_parse_removed_image_ids_valid(self):
        """Test parsing valid comma-separated IDs"""
        from marketplace.views import parse_removed_image_ids

        result = parse_removed_image_ids("1,2,3")
        self.assertEqual(result, [1, 2, 3])

    def test_parse_removed_image_ids_with_spaces(self):
        """Test parsing IDs with spaces"""
        from marketplace.views import parse_removed_image_ids

        result = parse_removed_image_ids("1, 2, 3")
        self.assertEqual(result, [1, 2, 3])

    def test_parse_removed_image_ids_empty(self):
        """Test parsing empty string"""
        from marketplace.views import parse_removed_image_ids

        result = parse_removed_image_ids("")
        self.assertEqual(result, [])

    def test_parse_removed_image_ids_none(self):
        """Test parsing None"""
        from marketplace.views import parse_removed_image_ids

        result = parse_removed_image_ids(None)
        self.assertEqual(result, [])

    def test_validate_uploaded_files_valid(self):
        """Test validating valid image files"""
        from marketplace.views import validate_uploaded_files
        from marketplace.forms import ItemForm

        valid_data = {
            "title": "Valid Item",
            "description": "This is a valid description with more than 20 characters",
            "condition": "good",
            "price": "50.00",
            "address": "Bobst Library",
        }
        form = ItemForm(data=valid_data)
        files = [create_image() for _ in range(3)]
        result = validate_uploaded_files(files, form)
        self.assertFalse(result)

    def test_validate_uploaded_files_too_many(self):
        """Test validating more than 10 files"""
        from marketplace.views import validate_uploaded_files
        from marketplace.forms import ItemForm

        valid_data = {
            "title": "Valid Item",
            "description": "This is a valid description with more than 20 characters",
            "condition": "good",
            "price": "50.00",
            "address": "Bobst Library",
        }
        form = ItemForm(data=valid_data)
        files = [create_image() for _ in range(11)]
        result = validate_uploaded_files(files, form)
        self.assertTrue(result)

    def test_validate_uploaded_files_invalid_type(self):
        """Test validating non-image file"""
        from marketplace.views import validate_uploaded_files
        from marketplace.forms import ItemForm

        valid_data = {
            "title": "Valid Item",
            "description": "This is a valid description with more than 20 characters",
            "condition": "good",
            "price": "50.00",
            "address": "Bobst Library",
        }
        form = ItemForm(data=valid_data)
        text_file = SimpleUploadedFile(
            "test.txt", b"not an image", content_type="text/plain"
        )
        result = validate_uploaded_files([text_file], form)
        self.assertTrue(result)

    def test_validate_uploaded_files_too_large(self):
        """Test validating oversized file"""
        from marketplace.views import validate_uploaded_files
        from marketplace.forms import ItemForm

        valid_data = {
            "title": "Valid Item",
            "description": "This is a valid description with more than 20 characters",
            "condition": "good",
            "price": "50.00",
            "address": "Bobst Library",
        }
        form = ItemForm(data=valid_data)
        large_file = SimpleUploadedFile(
            "large.jpg", b"x" * (6 * 1024 * 1024), content_type="image/jpeg"
        )
        result = validate_uploaded_files([large_file], form)
        self.assertTrue(result)


class MarketplaceHomeViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_marketplace_home_redirect(self):
        """Test marketplace home redirects to my_items"""
        User.objects.create_user(
            email="test@nyu.edu", username="testuser", password="testpw0rd"
        )
        self.client.login(email="test@nyu.edu", password="testpw0rd")
        url = reverse("marketplace_home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("my_items"))


class BrowseMarketplaceViewTests(TestCase):
    """Test the browse marketplace view with search and filtering"""

    def setUp(self):
        self.client = Client()
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

        from profiles.models import Profile

        Profile.objects.create(user=self.user1, university="nyu")
        Profile.objects.create(user=self.user2, university="nyu")

        # Create multiple items with different attributes
        self.item1 = Item.objects.create(
            user=self.user1,
            title="Cheap Desk Lamp",
            description="Great condition desk lamp",
            category="furniture",
            condition="good",
            price=25.00,
            address="Manhattan",
            is_active=True,
            is_sold=False,
        )

        self.item2 = Item.objects.create(
            user=self.user2,
            title="MacBook Pro Laptop",
            description="2020 MacBook Pro in excellent condition",
            category="electronics",
            condition="like_new",
            price=1200.00,
            address="Brooklyn",
            is_active=True,
            is_sold=False,
        )

        self.item3 = Item.objects.create(
            user=self.user1,
            title="Calculus Textbook",
            description="Used textbook for Calc 1",
            category="books",
            condition="good",
            price=50.00,
            address="Queens",
            is_active=True,
            is_sold=False,
        )

        # Sold item (should not appear in results)
        self.sold_item = Item.objects.create(
            user=self.user1,
            title="Sold Item",
            description="Already sold",
            category="furniture",
            condition="good",
            price=100.00,
            address="Manhattan",
            is_active=True,
            is_sold=True,
        )

        # Inactive item (should not appear in results)
        self.inactive_item = Item.objects.create(
            user=self.user1,
            title="Inactive Item",
            description="Not active",
            category="furniture",
            condition="good",
            price=100.00,
            address="Manhattan",
            is_active=False,
            is_sold=False,
        )

    def test_browse_marketplace_requires_login(self):
        """Test that browse marketplace requires authentication"""
        response = self.client.get(reverse("browse_marketplace"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_browse_shows_all_active_unsold(self):
        """Test that all active unsold items are displayed"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")
        response = self.client.get(reverse("browse_marketplace"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("items", response.context)
        items = response.context["items"]
        self.assertEqual(items.count(), 3)
        self.assertIn(self.item1, items)
        self.assertIn(self.item2, items)
        self.assertIn(self.item3, items)
        self.assertNotIn(self.sold_item, items)
        self.assertNotIn(self.inactive_item, items)

    def test_keyword_search(self):
        """Test keyword search in title and description"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        # Search for "laptop"
        response = self.client.get(reverse("browse_marketplace"), {"keyword": "laptop"})
        items = response.context["items"]
        self.assertEqual(items.count(), 1)
        self.assertIn(self.item2, items)

        # Search for "textbook"
        response = self.client.get(
            reverse("browse_marketplace"), {"keyword": "textbook"}
        )
        items = response.context["items"]
        self.assertEqual(items.count(), 1)
        self.assertIn(self.item3, items)

    def test_category_filter(self):
        """Test filtering by category"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        response = self.client.get(
            reverse("browse_marketplace"), {"category": "electronics"}
        )
        items = response.context["items"]
        self.assertEqual(items.count(), 1)
        self.assertIn(self.item2, items)

    def test_price_min_filter(self):
        """Test filtering by minimum price"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        response = self.client.get(reverse("browse_marketplace"), {"price_min": "50"})
        items = response.context["items"]
        self.assertEqual(items.count(), 2)
        self.assertIn(self.item2, items)
        self.assertIn(self.item3, items)
        self.assertNotIn(self.item1, items)

    def test_price_max_filter(self):
        """Test filtering by maximum price"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        response = self.client.get(reverse("browse_marketplace"), {"price_max": "100"})
        items = response.context["items"]
        self.assertEqual(items.count(), 2)
        self.assertIn(self.item1, items)
        self.assertIn(self.item3, items)
        self.assertNotIn(self.item2, items)

    def test_price_range_filter(self):
        """Test filtering by price range (min and max)"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        response = self.client.get(
            reverse("browse_marketplace"),
            {"price_min": "30", "price_max": "100"},
        )
        items = response.context["items"]
        self.assertEqual(items.count(), 1)
        self.assertIn(self.item3, items)

    def test_combined_filters(self):
        """Test multiple filters applied together"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        response = self.client.get(
            reverse("browse_marketplace"),
            {
                "keyword": "desk",
                "category": "furniture",
                "price_min": "10",
                "price_max": "50",
            },
        )
        items = response.context["items"]
        self.assertEqual(items.count(), 1)
        self.assertIn(self.item1, items)

    def test_invalid_price_values(self):
        """Test that invalid price values show warning"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        # Invalid price_min
        response = self.client.get(
            reverse("browse_marketplace"), {"price_min": "invalid"}
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Invalid minimum price" in str(m) for m in messages_list))

        # Invalid price_max
        response = self.client.get(
            reverse("browse_marketplace"), {"price_max": "not_a_number"}
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Invalid maximum price" in str(m) for m in messages_list))

    def test_filter_persistence(self):
        """Test that filter values persist in context"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        response = self.client.get(
            reverse("browse_marketplace"),
            {
                "keyword": "test",
                "category": "electronics",
                "price_min": "50",
                "price_max": "500",
            },
        )

        self.assertEqual(response.context["keyword"], "test")
        self.assertEqual(response.context["category"], "electronics")
        self.assertEqual(response.context["price_min"], "50")
        self.assertEqual(response.context["price_max"], "500")
        self.assertTrue(response.context["has_filters"])

    def test_no_filters_applied(self):
        """Test has_filters is False when no filters applied"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        response = self.client.get(reverse("browse_marketplace"))
        self.assertFalse(response.context["has_filters"])

    def test_categories_in_context(self):
        """Test that category choices are available in context"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        response = self.client.get(reverse("browse_marketplace"))
        self.assertIn("categories", response.context)
        self.assertIsNotNone(response.context["categories"])

    def test_keyword_case_insensitive(self):
        """Test that keyword search is case-insensitive"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        # Search for "LAPTOP" in uppercase
        response = self.client.get(reverse("browse_marketplace"), {"keyword": "LAPTOP"})
        items = response.context["items"]
        self.assertEqual(items.count(), 1)
        self.assertIn(self.item2, items)

    def test_empty_keyword_shows_all(self):
        """Test that empty keyword shows all items"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        response = self.client.get(reverse("browse_marketplace"), {"keyword": ""})
        items = response.context["items"]
        self.assertEqual(items.count(), 3)

    def test_no_results_found(self):
        """Test behavior when no items match filters"""
        self.client.login(username="user1@nyu.edu", password="TestPassword123!")

        response = self.client.get(
            reverse("browse_marketplace"),
            {"keyword": "nonexistent item that does not exist"},
        )
        items = response.context["items"]
        self.assertEqual(items.count(), 0)
