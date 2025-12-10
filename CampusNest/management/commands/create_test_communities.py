from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from communities.models import Community, CommunityMember, Event, EventRSVP, Post
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
import random

User = get_user_model()


def generate_placeholder_image(color=(73, 109, 137)):
    """Generate a simple placeholder image with custom color"""
    img = Image.new("RGB", (800, 400), color=color)
    img_io = BytesIO()
    img.save(img_io, "JPEG")
    img_io.seek(0)
    return ContentFile(img_io.read(), name="placeholder.jpg")


# Community Data
COMMUNITIES_DATA = [
    {
        "name": "NYC Tech & Startups",
        "description": "A community for students interested in technology, entrepreneurship, and startups. Connect with fellow tech enthusiasts, share project ideas, attend hackathons, and network with industry professionals. Whether you're a CS major or just tech-curious, everyone is welcome!",
        "privacy": "public",
        "university": None,
        "color": (66, 135, 245),  # Blue
    },
    {
        "name": "NYU Study Groups",
        "description": "Exclusive community for NYU students to organize study sessions, share notes, and collaborate on coursework. Find study partners for your classes, join group sessions for midterms and finals, and support each other academically.",
        "privacy": "university",
        "university": "NYU",
        "color": (87, 24, 130),  # NYU Purple
    },
    {
        "name": "Film & Photography Club",
        "description": "Private community for aspiring filmmakers and photographers. Share your work, get constructive feedback, learn new techniques, and collaborate on creative projects. Members must apply to join and demonstrate genuine interest in visual arts.",
        "privacy": "private",
        "university": None,
        "color": (245, 124, 0),  # Orange
    },
]

# Event Data Templates
EVENTS_DATA = {
    "NYC Tech & Startups": [
        {
            "title": "Startup Pitch Night",
            "description": "Present your startup ideas and get feedback from fellow students and mentors! Whether you have a fully developed concept or just a rough idea, this is a supportive environment to practice your pitch. Pizza and refreshments will be provided.",
            "location": "NYU Tandon MakerSpace, 370 Jay St, Brooklyn",
            "location_details": "Room 311, 3rd Floor. Enter through main entrance and take elevator to 3rd floor.",
            "days_offset": 7,
            "duration_hours": 3,
        },
        {
            "title": "React & Next.js Workshop",
            "description": "Hands-on workshop covering modern React development with Next.js. We'll build a full-stack application from scratch, covering server components, API routes, and deployment. Bring your laptop! Prerequisites: Basic JavaScript knowledge.",
            "location": "Columbia Engineering Library, 500 W 120th St",
            "location_details": "Computer Lab B, Lower Level. Sign in at front desk.",
            "days_offset": 14,
            "duration_hours": 4,
        },
        {
            "title": "Tech Career Fair Prep",
            "description": "Get ready for upcoming career fairs! We'll review resume tips, practice elevator pitches, and do mock technical interviews. Industry professionals will provide feedback and share insider tips for landing internships at top tech companies.",
            "location": "Pace University, 1 Pace Plaza, Manhattan",
            "location_details": "Schimmel Center, Meeting Room 2A",
            "days_offset": 21,
            "duration_hours": 2,
        },
    ],
    "NYU Study Groups": [
        {
            "title": "Calculus II Study Session",
            "description": "Final exam prep for Calculus II! We'll work through practice problems, review key concepts (integration techniques, series, sequences), and help each other with challenging topics. Bring your textbook and previous exams.",
            "location": "Bobst Library, 70 Washington Square South",
            "location_details": "Study Room 505, 5th Floor (reserved under 'Study Group')",
            "days_offset": 5,
            "duration_hours": 3,
        },
        {
            "title": "Data Structures Midterm Prep",
            "description": "Collaborative study session for Data Structures midterm. We'll review linked lists, trees, graphs, sorting algorithms, and time complexity analysis. Great opportunity to clarify concepts and work through practice problems together.",
            "location": "Warren Weaver Hall, 251 Mercer St",
            "location_details": "Room 109, Ground Floor Computer Lab",
            "days_offset": 10,
            "duration_hours": 4,
        },
        {
            "title": "Organic Chemistry Review",
            "description": "Weekly organic chemistry review session led by students who've aced the course. We'll cover reaction mechanisms, stereochemistry, and synthesis problems. All students taking Orgo are welcome, regardless of which professor you have.",
            "location": "Silver Center, 100 Washington Square East",
            "location_details": "Room 207, Chemistry Wing",
            "days_offset": 3,
            "duration_hours": 2,
        },
    ],
    "Film & Photography Club": [
        {
            "title": "Portrait Photography Workshop",
            "description": "Learn professional portrait photography techniques! We'll cover lighting setups, composition, working with models, and post-processing in Lightroom. Bring your camera (DSLR or mirrorless preferred). Models will be provided for practice shots.",
            "location": "Brooklyn Studios, 45 Main St, DUMBO",
            "location_details": "Studio 3B, 3rd Floor. Building has elevator access.",
            "days_offset": 12,
            "duration_hours": 5,
        },
        {
            "title": "Short Film Screening & Critique",
            "description": "Monthly screening of member-submitted short films (5-15 minutes). After each screening, we'll have constructive group discussions about cinematography, storytelling, editing, and sound design. Submit your films by the deadline!",
            "location": "Kimmel Center, 60 Washington Square South",
            "location_details": "Eisner & Lubin Auditorium, 2nd Floor",
            "days_offset": 18,
            "duration_hours": 3,
        },
        {
            "title": "Night Photography Walk",
            "description": "Explore NYC's nightlife through your lens! We'll walk through Times Square, Brooklyn Bridge, and Lower Manhattan capturing long exposures, light trails, and urban landscapes. Perfect for learning low-light photography techniques.",
            "location": "Meet at Washington Square Park Arch",
            "location_details": "We'll meet at the arch and walk to various locations. Bring a tripod if you have one!",
            "days_offset": 25,
            "duration_hours": 4,
        },
    ],
}

# Posts data
POSTS_DATA = {
    "NYC Tech & Startups": [
        {
            "title": "Looking for co-founder with ML experience",
            "content": "Hey everyone! I'm working on a SaaS platform that uses machine learning to help students optimize their study schedules. I've built the MVP and have some early users, but I need someone with ML/AI experience to take the recommendation engine to the next level. If you're interested in edtech and want to build something meaningful, let's chat!",
        },
        {
            "title": "Free Coursera Plus accounts available!",
            "content": "Just found out that NYU students get free access to Coursera Plus through the library. You can take unlimited courses in data science, web dev, cloud computing, etc. Check out the library website under 'Digital Resources'. Game changer for building skills outside of class!",
        },
    ],
    "NYU Study Groups": [
        {
            "title": "Study group for CSCI-UA 102?",
            "content": "Is anyone else taking Data Structures with Professor Thompson this semester? The last assignment on binary search trees completely destroyed me. Would love to form a regular study group to work through the problem sets together. Let me know if you're interested!",
        },
        {
            "title": "Shared Google Drive for CS course notes",
            "content": "I've created a shared Google Drive folder where we can all upload and share our course notes, study guides, and practice exams (obviously only for studying, respecting academic integrity). If you want access, drop your NYU email below. Let's help each other succeed! 📚",
        },
    ],
    "Film & Photography Club": [
        {
            "title": "Seeking actors for senior thesis film",
            "content": "I'm directing my senior thesis film this spring - a 20-minute psychological thriller about identity and perception. Looking for 3 actors (2 male, 1 female, ages 20-25). Shooting will be over 4 weekends in March. This is an unpaid student project, but you'll get IMDb credit, meals on set, and a copy of the final film for your reel. Serious inquiries only!",
        },
    ],
}


class Command(BaseCommand):
    help = "Create test communities with events and posts for demo purposes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-members",
            action="store_true",
            help="Also create test users and add them as members to communities",
        )

    def get_or_create_admin_user(self):
        """Get or create admin user for communities."""
        admin_user, created = User.objects.get_or_create(
            username="community_admin",
            defaults={
                "email": "admin@nyu.edu",
                "first_name": "Community",
                "last_name": "Admin",
                "is_verified": True,
            },
        )
        if created:
            admin_user.set_password("testpass123")
            admin_user.save()
            self.stdout.write(
                self.style.SUCCESS(f"✓ Created admin user: {admin_user.username}")
            )
        return admin_user

    def create_events_for_community(self, community, admin_user, comm_data):
        """Create events for a specific community."""
        created_events = 0
        events_for_community = EVENTS_DATA.get(comm_data["name"], [])
        for event_data in events_for_community:
            start_datetime = timezone.now() + timedelta(days=event_data["days_offset"])
            # Set start time to 6 PM on that day
            start_datetime = start_datetime.replace(
                hour=18, minute=0, second=0, microsecond=0
            )
            end_datetime = start_datetime + timedelta(
                hours=event_data["duration_hours"]
            )

            event = Event.objects.create(
                community=community,
                organizer=admin_user,
                title=event_data["title"],
                description=event_data["description"],
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                location=event_data["location"],
                location_details=event_data["location_details"],
                is_cancelled=False,
            )

            created_events += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✓ Created event: {event.title} ({start_datetime.strftime('%b %d, %Y at %I:%M %p')})"
                )
            )
        return created_events

    def create_posts_for_community(self, community, admin_user, comm_data):
        """Create posts for a specific community."""
        created_posts = 0
        posts_for_community = POSTS_DATA.get(comm_data["name"], [])
        for post_data in posts_for_community:
            post = Post.objects.create(
                community=community,
                author=admin_user,
                title=post_data.get("title", ""),
                content=post_data["content"],
                is_pinned=False,
            )

            created_posts += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✓ Created post: {post.title or post.content[:50]}..."
                )
            )
        return created_posts

    def add_members_to_communities(self):
        """Add existing users as members to communities."""
        created_members = 0
        created_posts = 0

        self.stdout.write(
            self.style.WARNING("\nAdding existing users as community members...")
        )

        # Get existing users (exclude superusers and the admin user we just created)
        existing_users = list(
            User.objects.filter(is_verified=True, is_superuser=False)
            .exclude(username="community_admin")
            .order_by("?")[:10]  # Get random 10 users
        )

        if not existing_users:
            self.stdout.write(
                self.style.WARNING(
                    "  ⚠ No existing users found. Run 'python manage.py create_test_users' first to create dummy accounts."
                )
            )
            return created_members, created_posts

        self.stdout.write(
            self.style.SUCCESS(f"  ✓ Found {len(existing_users)} existing users")
        )

        # Add users to communities
        for user in existing_users:
            # Add user to random communities (1-3 communities per user)
            communities = list(Community.objects.filter(is_active=True))
            num_communities = min(random.randint(1, 3), len(communities))

            for community in random.sample(communities, k=num_communities):
                # Check if already a member
                if not CommunityMember.objects.filter(
                    community=community, user=user
                ).exists():
                    # Determine status based on privacy
                    status = "pending" if community.privacy == "private" else "active"

                    # Randomly make some users moderators
                    role = "moderator" if random.random() < 0.2 else "member"

                    CommunityMember.objects.create(
                        community=community,
                        user=user,
                        role=role,
                        status=status,
                    )
                    created_members += 1

                    # Add RSVP to 1-2 random events in this community
                    events = list(community.events.filter(is_cancelled=False))
                    if events:
                        num_rsvps = min(random.randint(1, 2), len(events))
                        for event in random.sample(events, k=num_rsvps):
                            EventRSVP.objects.get_or_create(
                                event=event,
                                user=user,
                                defaults={
                                    "status": random.choice(
                                        ["going", "interested", "going", "going"]
                                    )  # 75% going, 25% interested
                                },
                            )
                            # Update event RSVP counts
                            event.update_rsvp_counts()

        # Also add some posts from existing users
        created_posts = self.create_posts_from_users()

        return created_members, created_posts

    def create_posts_from_users(self):
        """Create posts from existing users."""
        created_posts = 0
        self.stdout.write(self.style.WARNING("\nAdding posts from existing users..."))

        # Get active community members
        active_members = CommunityMember.objects.filter(status="active").select_related(
            "user", "community"
        )

        # Create 3-5 additional posts from random users
        num_extra_posts = min(random.randint(3, 5), len(active_members))
        sample_members = random.sample(list(active_members), k=num_extra_posts)

        post_templates = [
            {
                "title": "First time here!",
                "content": "Hey everyone! Just joined this community and excited to connect with like-minded people. Looking forward to attending some events and meeting you all!",
            },
            {
                "title": "",
                "content": "Does anyone have recommendations for good coffee shops near campus where we could meet up for study sessions? Looking for places with good WiFi and not too crowded.",
            },
            {
                "title": "Project collaboration opportunity",
                "content": "I'm working on a cool project and looking for collaborators! If anyone's interested in joining or just wants to learn more, let me know. Always happy to work with motivated people!",
            },
            {
                "title": "Thank you!",
                "content": "Just wanted to say thanks to everyone who came to the last event. Had an amazing time and learned so much. Can't wait for the next one!",
            },
            {
                "title": "",
                "content": "Quick question - is there a Discord or Slack channel for this community? Would be great to have a place for quick discussions and sharing resources.",
            },
        ]

        for member in sample_members:
            post_data = random.choice(post_templates)
            Post.objects.create(
                community=member.community,
                author=member.user,
                title=post_data["title"],
                content=post_data["content"],
                is_pinned=False,
            )
            created_posts += 1

        return created_posts

    def handle(self, *args, **options):
        with_members = options["with_members"]
        created_communities = 0
        created_events = 0
        created_posts = 0
        created_members = 0

        # Get or create a default admin user for communities
        admin_user = self.get_or_create_admin_user()

        # Create communities
        for comm_data in COMMUNITIES_DATA:
            # Check if community already exists
            if Community.objects.filter(name=comm_data["name"]).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"Community '{comm_data['name']}' already exists, skipping..."
                    )
                )
                continue

            # Create community
            community = Community.objects.create(
                name=comm_data["name"],
                description=comm_data["description"],
                privacy=comm_data["privacy"],
                university=comm_data["university"],
                created_by=admin_user,
                is_active=True,
            )

            # Add cover image
            community.cover_image.save(
                "cover.jpg",
                generate_placeholder_image(color=comm_data["color"]),
                save=True,
            )

            # Add creator as admin member
            CommunityMember.objects.create(
                community=community,
                user=admin_user,
                role="admin",
                status="active",
            )

            created_communities += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Created community: {community.name} ({comm_data['privacy']})"
                )
            )

            # Create events and posts for this community
            created_events += self.create_events_for_community(
                community, admin_user, comm_data
            )
            created_posts += self.create_posts_for_community(
                community, admin_user, comm_data
            )

        # Optionally add existing users as members
        if with_members:
            members_added, posts_added = self.add_members_to_communities()
            created_members += members_added
            created_posts += posts_added

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Successfully created:"
                f"\n  • {created_communities} communities"
                f"\n  • {created_events} events"
                f"\n  • {created_posts} posts"
            )
        )

        if with_members:
            self.stdout.write(
                self.style.SUCCESS(f"  • {created_members} community memberships")
            )

        self.stdout.write(
            self.style.WARNING(
                "\n💡 Admin user credentials:"
                "\n   Username: community_admin"
                "\n   Password: testpass123"
                "\n\nYou can now view these communities in your application!"
            )
        )
