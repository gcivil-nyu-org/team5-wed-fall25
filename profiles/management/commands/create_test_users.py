from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from profiles.models import Profile
import random

User = get_user_model()

FIRST_NAMES = [
    "Alex",
    "Jordan",
    "Casey",
    "Morgan",
    "Riley",
    "Taylor",
    "Jamie",
    "Avery",
    "Sam",
    "Quinn",
    "Blake",
    "Drew",
    "Reese",
    "Dakota",
    "Skylar",
    "Sage",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
]

UNIVERSITIES = ["NYU", "Columbia", "CUNY", "Pace", "Fordham", "The New School"]

SMOKING_CHOICES = ["non_smoker", "smoker", "occasionally"]
PET_CHOICES = ["no_pets", "cats", "dogs", "other", "no_preference"]
CLEANLINESS_CHOICES = ["very_clean", "clean", "moderate", "relaxed", "no_preference"]


class Command(BaseCommand):
    help = "Create test users with roommate preferences for testing the find roommates feature"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=5,
            help="Number of test users to create (default: 5)",
        )

    def handle(self, *args, **options):
        count = options["count"]
        created_count = 0

        for i in range(count):
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

            # Create/update profile with random preferences
            profile, created = Profile.objects.get_or_create(user=user)
            profile.smoking_preference = random.choice(SMOKING_CHOICES)
            profile.pet_preference = random.choice(PET_CHOICES)
            profile.cleanliness_preference = random.choice(CLEANLINESS_CHOICES)
            profile.budget_min = random.choice([800, 1000, 1200, 1500])
            profile.budget_max = profile.budget_min + random.choice([300, 500, 700])
            profile.location = random.choice(
                ["Manhattan", "Brooklyn", "Queens", "Astoria"]
            )
            profile.university = random.choice(UNIVERSITIES)
            profile.bio = f"Hi! I'm {first_name}, a student looking for a great roommate. Let's connect!"
            profile.save()

            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Created user: {username} ({first_name} {last_name})"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Successfully created {created_count} test users!")
        )
        self.stdout.write(
            self.style.WARNING(
                "\nAll test users have password: testpass123\n"
                "You can login with any username to test the find roommates feature."
            )
        )
