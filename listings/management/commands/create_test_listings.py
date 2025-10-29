from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from profiles.models import Profile
from listings.models import Listing, ListingImage
from marketplace.models import Item, ItemImage
from marketplace.constants import ITEM_CATEGORY_CHOICES
import random
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile

User = get_user_model()

FIRST_NAMES = [
    "Alex", "Jordan", "Casey", "Morgan", "Riley", "Taylor", "Jamie", "Avery",
    "Sam", "Quinn", "Blake", "Drew", "Reese", "Dakota", "Skylar", "Sage",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
]

UNIVERSITIES = ["NYU", "Columbia", "CUNY", "Pace", "Fordham", "The New School"]

SMOKING_CHOICES = ["non_smoker", "smoker", "occasionally"]
PET_CHOICES = ["no_pets", "cats", "dogs", "other", "no_preference"]
CLEANLINESS_CHOICES = ["very_clean", "clean", "moderate", "relaxed", "no_preference"]

LISTING_TITLES = [
    "Cozy Studio in Manhattan",
    "Spacious 2BR in Brooklyn",
    "Modern Apartment with Gym",
    "Sunny Room Near Campus",
    "Luxury Loft in Astoria",
    "Affordable Room in Queens",
    "Renovated Apartment",
    "Bright Studio with Balcony",
    "Quiet Room in Residential Area",
    "Furnished Apartment Ready Now",
]

NEIGHBORHOODS = [
    "Manhattan", "Brooklyn", "Queens", "Astoria", "Williamsburg", "Park Slope",
    "Upper West Side", "East Village", "Long Island City", "Sunset Park",
]

AMENITIES = [
    "WiFi", "Gym", "Laundry", "Parking", "Doorman", "Rooftop", "Balcony",
    "Kitchen", "Air Conditioning", "Hardwood Floors", "Pet Friendly", "Furnished",
]

MARKETPLACE_ITEMS = [
    "Used Desk", "Bookshelf", "Desk Chair", "Twin Bed Frame", "Mattress",
    "Nightstand", "Dresser", "Lamp", "Rug", "Curtains", "Textbooks",
    "Laptop", "Monitor", "Keyboard", "Mouse", "Headphones", "Speaker",
    "Microwave", "Mini Fridge", "Coffee Maker", "Blender", "Toaster",
    "Bicycle", "Skateboard", "Backpack", "Suitcase", "Shoes", "Jacket",
]

ITEM_CONDITIONS = ["like_new", "good", "fair", "used"]
# Item categories are imported from marketplace.constants.ITEM_CATEGORY_CHOICES
ITEM_CATEGORIES = [choice[0] for choice in ITEM_CATEGORY_CHOICES]  # Extract just the values


def generate_placeholder_image():
    """Generate a simple placeholder image"""
    img = Image.new('RGB', (400, 300), color=(73, 109, 137))
    img_io = BytesIO()
    img.save(img_io, 'JPEG')
    img_io.seek(0)
    return ContentFile(img_io.read(), name='placeholder.jpg')


class Command(BaseCommand):
    help = "Create test users with house listings for testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--users",
            type=int,
            default=3,
            help="Number of test users to create (default: 3)",
        )
        parser.add_argument(
            "--listings",
            type=int,
            default=2,
            help="Number of listings per user (default: 2)",
        )
        parser.add_argument(
            "--items",
            type=int,
            default=2,
            help="Number of marketplace items per user (default: 2)",
        )

    def handle(self, *args, **options):
        user_count = options["users"]
        listings_per_user = options["listings"]
        items_per_user = options["items"]
        created_users = 0
        created_listings = 0
        created_items = 0

        for i in range(user_count):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            username = f"{first_name.lower()}_{last_name.lower()}_{i}"
            email = f"{username}@nyu.edu"

            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(f"User {username} already exists, skipping...")
                continue

            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password="testpass123",
                first_name=first_name,
                last_name=last_name,
                is_verified=True,
            )

            # Create/update profile
            profile, created = Profile.objects.get_or_create(user=user)
            profile.smoking_preference = random.choice(SMOKING_CHOICES)
            profile.pet_preference = random.choice(PET_CHOICES)
            profile.cleanliness_preference = random.choice(CLEANLINESS_CHOICES)
            profile.budget_min = random.choice([800, 1000, 1200, 1500])
            profile.budget_max = profile.budget_min + random.choice([300, 500, 700])
            profile.location = random.choice(NEIGHBORHOODS)
            profile.university = random.choice(UNIVERSITIES)
            profile.bio = f"Hi! I'm {first_name}, a student looking for a great roommate. Let's connect!"
            profile.save()

            created_users += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Created user: {username} ({first_name} {last_name})"
                )
            )

            # Create listings for this user
            for j in range(listings_per_user):
                title = random.choice(LISTING_TITLES)
                rent = random.choice([800, 1000, 1200, 1500, 1800, 2000])
                address = f"{random.randint(100, 9999)} {random.choice(['Main', 'Park', 'Broadway', 'Madison', 'Fifth'])} St, {random.choice(NEIGHBORHOODS)}, NY"
                
                availability_start = timezone.now().date() + timedelta(days=random.randint(1, 30))
                availability_end = availability_start + timedelta(days=random.randint(90, 365))

                listing = Listing.objects.create(
                    user=user,
                    title=f"{title} #{j+1}",
                    description=f"Beautiful {random.choice(['studio', '1-bedroom', '2-bedroom'])} apartment. "
                                f"Amenities: {', '.join(random.sample(AMENITIES, k=random.randint(3, 6)))}. "
                                f"Perfect for students!",
                    address=address,
                    rent=rent,
                    availability_start=availability_start,
                    availability_end=availability_end,
                    is_active=True,
                )

                # Add a placeholder image
                image = ListingImage.objects.create(listing=listing)
                image.image.save('placeholder.jpg', generate_placeholder_image(), save=True)

                created_listings += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Created listing: {listing.title} (${rent}/month)"
                    )
                )

            # Create marketplace items for this user
            for k in range(items_per_user):
                item_name = random.choice(MARKETPLACE_ITEMS)
                price = random.choice([10, 25, 50, 75, 100, 150, 200, 300, 500])
                condition = random.choice(ITEM_CONDITIONS)
                category = random.choice(ITEM_CATEGORIES)  # Uses values from marketplace.constants

                item = Item.objects.create(
                    user=user,
                    title=f"{item_name} #{k+1}",
                    description=f"Great {item_name.lower()} in {condition} condition. "
                               f"Perfect for students! Willing to negotiate on price.",
                    price=price,
                    condition=condition,
                    category=category,
                    pickup_location=f"{random.choice(NEIGHBORHOODS)}, NY",
                    owner_name=f"{user.first_name} {user.last_name}",
                    contact_details=user.email,
                    is_active=True,
                )

                # Add a placeholder image
                image = ItemImage.objects.create(item=item)
                image.image.save('placeholder.jpg', generate_placeholder_image(), save=True)

                created_items += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Created item: {item.title} (${price})"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Successfully created {created_users} test users, {created_listings} listings, and {created_items} marketplace items!"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                f"\nAll test users have password: testpass123\n"
                f"You can login with any username to view listings and profiles."
            )
        )
