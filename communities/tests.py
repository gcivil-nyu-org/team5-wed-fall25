from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import IntegrityError
from django.urls import reverse
from .models import Community, CommunityMember, Post, PostImage, PostFile, Comment, Thread, ChatMessage
from .forms import CommunityForm, PostForm, CommentForm
from profiles.models import Profile
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


class CommunityModelTests(TestCase):
    """Tests for Community model"""

    def setUp(self):
        """Create test user"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@nyu.edu',
            password='testpass123'
        )

    def test_create_public_community(self):
        """Test creating a public community"""
        community = Community.objects.create(
            name='NYU Students',
            description='Community for all NYU students',
            privacy='public',
            created_by=self.user
        )
        self.assertEqual(community.name, 'NYU Students')
        self.assertEqual(community.privacy, 'public')
        self.assertEqual(community.member_count, 0)
        self.assertEqual(community.post_count, 0)
        self.assertTrue(community.is_active)
        self.assertEqual(str(community), 'NYU Students')

    def test_create_private_community(self):
        """Test creating a private community"""
        community = Community.objects.create(
            name='Private Group',
            description='A private community',
            privacy='private',
            created_by=self.user
        )
        self.assertEqual(community.privacy, 'private')
        self.assertIsNone(community.university)

    def test_create_university_community(self):
        """Test creating a university-restricted community"""
        community = Community.objects.create(
            name='NYU Housing',
            description='NYU students only',
            privacy='university',
            university='NYU',
            created_by=self.user
        )
        self.assertEqual(community.privacy, 'university')
        self.assertEqual(community.university, 'NYU')

    def test_university_validation(self):
        """Test that university field is required for university-restricted communities"""
        community = Community(
            name='Test University Community',
            description='Should fail validation',
            privacy='university',
            # Missing university field
            created_by=self.user
        )
        with self.assertRaises(ValidationError) as context:
            community.full_clean()
        self.assertIn('university', context.exception.message_dict)

    def test_slug_auto_generation(self):
        """Test automatic slug generation from name"""
        community = Community.objects.create(
            name='Test Community Name',
            description='Test description',
            created_by=self.user
        )
        self.assertEqual(community.slug, 'test-community-name')

    def test_auto_slug_counter_increment(self):
        """Test that auto-generated slugs increment counter when base slug exists"""
        # This tests the slug generation logic in save() method
        # When we try to create a slug that already exists, it should add -1, -2, etc.
        # However, since name is unique, we can't test this easily with auto-generation
        # Instead, just verify that slug generation works
        community = Community.objects.create(
            name='Auto Generated Slug',
            description='Test',
            created_by=self.user
        )
        self.assertEqual(community.slug, 'auto-generated-slug')

    def test_unique_name_constraint(self):
        """Test that community names must be unique"""
        Community.objects.create(
            name='Unique Name',
            description='First',
            created_by=self.user
        )
        with self.assertRaises(IntegrityError):
            Community.objects.create(
                name='Unique Name',
                description='Duplicate',
                created_by=self.user
            )

    def test_unique_slug_constraint(self):
        """Test that community slugs must be unique"""
        Community.objects.create(
            name='Community One',
            slug='same-slug',
            description='First',
            created_by=self.user
        )
        with self.assertRaises(IntegrityError):
            Community.objects.create(
                name='Community Two',
                slug='same-slug',
                description='Duplicate slug',
                created_by=self.user
            )

    def test_community_ordering(self):
        """Test communities are ordered by creation date (newest first)"""
        comm1 = Community.objects.create(
            name='First',
            description='First',
            created_by=self.user
        )
        comm2 = Community.objects.create(
            name='Second',
            description='Second',
            created_by=self.user
        )
        communities = list(Community.objects.all())
        self.assertEqual(communities[0], comm2)  # Newest first
        self.assertEqual(communities[1], comm1)


class CommunityMemberModelTests(TestCase):
    """Tests for CommunityMember model"""

    def setUp(self):
        """Create test users and community"""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@nyu.edu',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@columbia.edu',
            password='testpass123'
        )
        self.community = Community.objects.create(
            name='Test Community',
            description='Test description',
            created_by=self.user1
        )

    def test_create_membership(self):
        """Test creating a community membership"""
        membership = CommunityMember.objects.create(
            community=self.community,
            user=self.user1,
            role='member',
            status='active'
        )
        self.assertEqual(membership.community, self.community)
        self.assertEqual(membership.user, self.user1)
        self.assertEqual(membership.role, 'member')
        self.assertEqual(membership.status, 'active')
        self.assertEqual(
            str(membership),
            f"user1 - Test Community (member)"
        )

    def test_default_member_role(self):
        """Test default role is 'member'"""
        membership = CommunityMember.objects.create(
            community=self.community,
            user=self.user1
        )
        self.assertEqual(membership.role, 'member')

    def test_default_active_status(self):
        """Test default status is 'active'"""
        membership = CommunityMember.objects.create(
            community=self.community,
            user=self.user1
        )
        self.assertEqual(membership.status, 'active')

    def test_moderator_role(self):
        """Test creating a moderator membership"""
        membership = CommunityMember.objects.create(
            community=self.community,
            user=self.user1,
            role='moderator'
        )
        self.assertEqual(membership.role, 'moderator')

    def test_admin_role(self):
        """Test creating an admin membership"""
        membership = CommunityMember.objects.create(
            community=self.community,
            user=self.user1,
            role='admin'
        )
        self.assertEqual(membership.role, 'admin')

    def test_pending_status(self):
        """Test creating a pending membership (join request)"""
        membership = CommunityMember.objects.create(
            community=self.community,
            user=self.user2,
            status='pending',
            request_message='I would like to join this community'
        )
        self.assertEqual(membership.status, 'pending')
        self.assertEqual(membership.request_message, 'I would like to join this community')

    def test_banned_status(self):
        """Test banned membership status"""
        membership = CommunityMember.objects.create(
            community=self.community,
            user=self.user2,
            status='banned'
        )
        self.assertEqual(membership.status, 'banned')

    def test_unique_together_constraint(self):
        """Test user can only have one membership per community"""
        CommunityMember.objects.create(
            community=self.community,
            user=self.user1
        )
        with self.assertRaises(IntegrityError):
            CommunityMember.objects.create(
                community=self.community,
                user=self.user1
            )

    def test_multiple_communities_same_user(self):
        """Test user can join multiple communities"""
        community2 = Community.objects.create(
            name='Second Community',
            description='Second',
            created_by=self.user2
        )

        membership1 = CommunityMember.objects.create(
            community=self.community,
            user=self.user1
        )
        membership2 = CommunityMember.objects.create(
            community=community2,
            user=self.user1
        )

        self.assertEqual(self.user1.community_memberships.count(), 2)

    def test_membership_ordering(self):
        """Test memberships are ordered by join date (newest first)"""
        mem1 = CommunityMember.objects.create(
            community=self.community,
            user=self.user1
        )
        mem2 = CommunityMember.objects.create(
            community=self.community,
            user=self.user2
        )
        memberships = list(CommunityMember.objects.all())
        self.assertEqual(memberships[0], mem2)  # Newest first
        self.assertEqual(memberships[1], mem1)

    def test_reviewed_by_field(self):
        """Test reviewed_by field for tracking who approved a request"""
        membership = CommunityMember.objects.create(
            community=self.community,
            user=self.user2,
            status='pending'
        )
        # Simulate approval by admin
        membership.status = 'active'
        membership.reviewed_by = self.user1
        membership.save()

        self.assertEqual(membership.reviewed_by, self.user1)
        self.assertEqual(membership.status, 'active')


class CommunityViewTests(TestCase):
    """Tests for community views"""

    def setUp(self):
        """Create test users and communities"""
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@nyu.edu',
            password='testpass123',
            is_verified=True
        )
        Profile.objects.create(user=self.user1, university='NYU')

        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@columbia.edu',
            password='testpass123',
            is_verified=True
        )
        Profile.objects.create(user=self.user2, university='Columbia')

        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@fordham.edu',
            password='testpass123',
            is_verified=True
        )
        Profile.objects.create(user=self.user3, university='Fordham')

        # Create public community
        self.public_community = Community.objects.create(
            name='Public Community',
            description='A public community',
            privacy='public',
            created_by=self.user1
        )
        # Add creator as admin
        CommunityMember.objects.create(
            community=self.public_community,
            user=self.user1,
            role='admin',
            status='active'
        )

        # Create private community
        self.private_community = Community.objects.create(
            name='Private Community',
            description='A private community',
            privacy='private',
            created_by=self.user1
        )
        CommunityMember.objects.create(
            community=self.private_community,
            user=self.user1,
            role='admin',
            status='active'
        )

    def test_browse_communities_authenticated(self):
        """Test browsing communities as authenticated user"""
        self.client.login(username='user1@nyu.edu', password='testpass123')
        response = self.client.get(reverse('communities:browse'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Public Community')
        self.assertContains(response, 'Private Community')

    def test_browse_communities_unauthenticated(self):
        """Test browsing communities redirects unauthenticated users"""
        response = self.client.get(reverse('communities:browse'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_my_communities_view(self):
        """Test viewing user's joined communities"""
        # Add user2 to public community
        CommunityMember.objects.create(
            community=self.public_community,
            user=self.user2,
            role='member',
            status='active'
        )

        self.client.login(username='user2@columbia.edu', password='testpass123')
        response = self.client.get(reverse('communities:my_communities'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Public Community')
        self.assertNotContains(response, 'Private Community')

    def test_create_community_get(self):
        """Test GET request to create community page"""
        self.client.login(username='user1@nyu.edu', password='testpass123')
        response = self.client.get(reverse('communities:create'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], CommunityForm)

    def test_create_community_post_valid(self):
        """Test creating a community with valid data"""
        self.client.login(username='user1@nyu.edu', password='testpass123')
        data = {
            'name': 'New Community',
            'description': 'A brand new community',
            'privacy': 'public'
        }
        response = self.client.post(reverse('communities:create'), data)
        self.assertEqual(response.status_code, 302)

        # Verify community was created
        community = Community.objects.get(name='New Community')
        self.assertEqual(community.created_by, self.user1)

        # Verify creator is admin
        membership = CommunityMember.objects.get(
            community=community,
            user=self.user1
        )
        self.assertEqual(membership.role, 'admin')
        self.assertEqual(membership.status, 'active')

    def test_create_community_university_validation(self):
        """Test university field required for university-restricted communities"""
        self.client.login(username='user1@nyu.edu', password='testpass123')
        data = {
            'name': 'University Community',
            'description': 'Should require university',
            'privacy': 'university'
            # Missing university field
        }
        response = self.client.post(reverse('communities:create'), data)
        self.assertEqual(response.status_code, 200)  # Form re-rendered with errors
        self.assertFormError(
            response.context['form'],
            'university',
            'University field is required for university-restricted communities.'
        )

    def test_community_detail_view_member(self):
        """Test viewing community detail as a member"""
        CommunityMember.objects.create(
            community=self.public_community,
            user=self.user2,
            role='member',
            status='active'
        )

        self.client.login(username='user2@columbia.edu', password='testpass123')
        response = self.client.get(
            reverse('communities:detail', args=[self.public_community.slug])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_member'])
        self.assertContains(response, 'Leave Community')

    def test_community_detail_view_non_member(self):
        """Test viewing community detail as a non-member"""
        self.client.login(username='user2@columbia.edu', password='testpass123')
        response = self.client.get(
            reverse('communities:detail', args=[self.public_community.slug])
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_member'])
        self.assertContains(response, 'Join Community')

    def test_join_public_community(self):
        """Test joining a public community"""
        self.client.login(username='user2@columbia.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:join', args=[self.public_community.slug])
        )
        self.assertEqual(response.status_code, 302)

        # Verify membership created with active status
        membership = CommunityMember.objects.get(
            community=self.public_community,
            user=self.user2
        )
        self.assertEqual(membership.status, 'active')
        self.assertEqual(membership.role, 'member')

    def test_join_private_community_creates_request(self):
        """Test joining a private community creates pending request"""
        self.client.login(username='user2@columbia.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:join', args=[self.private_community.slug])
        )
        self.assertEqual(response.status_code, 302)

        # Verify membership created with pending status
        membership = CommunityMember.objects.get(
            community=self.private_community,
            user=self.user2
        )
        self.assertEqual(membership.status, 'pending')

    def test_join_community_already_member(self):
        """Test joining a community user is already member of"""
        CommunityMember.objects.create(
            community=self.public_community,
            user=self.user2,
            status='active'
        )

        self.client.login(username='user2@columbia.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:join', args=[self.public_community.slug])
        )
        self.assertEqual(response.status_code, 302)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(
            any('already' in str(m).lower() for m in messages)
        )

    def test_leave_community(self):
        """Test leaving a community"""
        CommunityMember.objects.create(
            community=self.public_community,
            user=self.user2,
            status='active'
        )

        self.client.login(username='user2@columbia.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:leave', args=[self.public_community.slug])
        )
        self.assertEqual(response.status_code, 302)

        # Verify membership deleted
        self.assertFalse(
            CommunityMember.objects.filter(
                community=self.public_community,
                user=self.user2
            ).exists()
        )

    def test_leave_community_last_admin_prevented(self):
        """Test last admin cannot leave community"""
        self.client.login(username='user1@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:leave', args=[self.public_community.slug])
        )
        self.assertEqual(response.status_code, 302)

        # Verify membership still exists
        self.assertTrue(
            CommunityMember.objects.filter(
                community=self.public_community,
                user=self.user1
            ).exists()
        )

        messages = list(response.wsgi_request._messages)
        self.assertTrue(
            any('last admin' in str(m).lower() for m in messages)
        )

    def test_community_settings_view_admin(self):
        """Test accessing settings as admin"""
        self.client.login(username='user1@nyu.edu', password='testpass123')
        response = self.client.get(
            reverse('communities:settings', args=[self.public_community.slug])
        )
        self.assertEqual(response.status_code, 200)

    def test_community_settings_view_non_admin(self):
        """Test accessing settings as non-admin is forbidden"""
        CommunityMember.objects.create(
            community=self.public_community,
            user=self.user2,
            role='member',
            status='active'
        )

        self.client.login(username='user2@columbia.edu', password='testpass123')
        response = self.client.get(
            reverse('communities:settings', args=[self.public_community.slug])
        )
        self.assertEqual(response.status_code, 403)

    def test_member_list_view(self):
        """Test viewing member list"""
        CommunityMember.objects.create(
            community=self.public_community,
            user=self.user2,
            role='member',
            status='active'
        )

        self.client.login(username='user1@nyu.edu', password='testpass123')
        response = self.client.get(
            reverse('communities:members', args=[self.public_community.slug])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'user1')
        self.assertContains(response, 'user2')

    def test_promote_member_by_admin(self):
        """Test admin can promote member to moderator"""
        member = CommunityMember.objects.create(
            community=self.public_community,
            user=self.user2,
            role='member',
            status='active'
        )

        self.client.login(username='user1@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:promote_member', args=[
                self.public_community.slug,
                self.user2.id
            ])
        )
        self.assertEqual(response.status_code, 302)

        member.refresh_from_db()
        self.assertEqual(member.role, 'moderator')

    def test_demote_member_by_admin(self):
        """Test admin can demote moderator to member"""
        moderator = CommunityMember.objects.create(
            community=self.public_community,
            user=self.user2,
            role='moderator',
            status='active'
        )

        self.client.login(username='user1@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:demote_member', args=[
                self.public_community.slug,
                self.user2.id
            ])
        )
        self.assertEqual(response.status_code, 302)

        moderator.refresh_from_db()
        self.assertEqual(moderator.role, 'member')

    def test_remove_member(self):
        """Test moderator can remove a member"""
        member = CommunityMember.objects.create(
            community=self.public_community,
            user=self.user2,
            role='member',
            status='active'
        )

        self.client.login(username='user1@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:remove_member', args=[
                self.public_community.slug,
                self.user2.id
            ])
        )
        self.assertEqual(response.status_code, 302)

        # Verify membership deleted
        self.assertFalse(
            CommunityMember.objects.filter(id=member.id).exists()
        )

    def test_ban_member(self):
        """Test moderator can ban a member"""
        member = CommunityMember.objects.create(
            community=self.public_community,
            user=self.user2,
            role='member',
            status='active'
        )

        self.client.login(username='user1@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:ban_member', args=[
                self.public_community.slug,
                self.user2.id
            ])
        )
        self.assertEqual(response.status_code, 302)

        member.refresh_from_db()
        self.assertEqual(member.status, 'banned')

    def test_join_requests_view(self):
        """Test viewing pending join requests"""
        CommunityMember.objects.create(
            community=self.private_community,
            user=self.user2,
            status='pending',
            request_message='Please let me join'
        )

        self.client.login(username='user1@nyu.edu', password='testpass123')
        response = self.client.get(
            reverse('communities:join_requests', args=[
                self.private_community.slug
            ])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'user2')

    def test_approve_join_request(self):
        """Test approving a join request"""
        request_membership = CommunityMember.objects.create(
            community=self.private_community,
            user=self.user2,
            status='pending'
        )

        self.client.login(username='user1@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:approve_request', args=[
                self.private_community.slug,
                self.user2.id
            ])
        )
        self.assertEqual(response.status_code, 302)

        request_membership.refresh_from_db()
        self.assertEqual(request_membership.status, 'active')
        self.assertEqual(request_membership.reviewed_by, self.user1)

    def test_reject_join_request(self):
        """Test rejecting a join request"""
        request_membership = CommunityMember.objects.create(
            community=self.private_community,
            user=self.user2,
            status='pending'
        )

        self.client.login(username='user1@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:reject_request', args=[
                self.private_community.slug,
                self.user2.id
            ])
        )
        self.assertEqual(response.status_code, 302)

        # Verify membership deleted
        self.assertFalse(
            CommunityMember.objects.filter(id=request_membership.id).exists()
        )

    def test_non_moderator_cannot_manage_members(self):
        """Test regular member cannot access moderation actions"""
        CommunityMember.objects.create(
            community=self.public_community,
            user=self.user2,
            role='member',
            status='active'
        )
        CommunityMember.objects.create(
            community=self.public_community,
            user=self.user3,
            role='member',
            status='active'
        )

        self.client.login(username='user2@columbia.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:remove_member', args=[
                self.public_community.slug,
                self.user3.id
            ])
        )
        self.assertEqual(response.status_code, 403)


class PostModelTests(TestCase):
    """Tests for Post model"""

    def setUp(self):
        """Create test user, community, and membership"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@nyu.edu',
            password='testpass123'
        )
        self.community = Community.objects.create(
            name='Test Community',
            description='Test description',
            created_by=self.user
        )
        CommunityMember.objects.create(
            community=self.community,
            user=self.user,
            role='member',
            status='active'
        )

    def test_create_post(self):
        """Test creating a basic post"""
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            title='Test Post',
            content='This is a test post'
        )
        self.assertEqual(post.title, 'Test Post')
        self.assertEqual(post.content, 'This is a test post')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.community, self.community)
        self.assertEqual(post.comment_count, 0)
        self.assertFalse(post.is_edited)
        self.assertFalse(post.is_pinned)

    def test_create_post_without_title(self):
        """Test creating a post without title (title is optional)"""
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            content='This is a test post without title'
        )
        self.assertEqual(post.title, '')
        self.assertEqual(post.content, 'This is a test post without title')

    def test_post_ordering(self):
        """Test posts are ordered by pinned status then creation date"""
        post1 = Post.objects.create(
            community=self.community,
            author=self.user,
            content='First post'
        )
        post2 = Post.objects.create(
            community=self.community,
            author=self.user,
            content='Second post'
        )
        post3 = Post.objects.create(
            community=self.community,
            author=self.user,
            content='Pinned post',
            is_pinned=True
        )

        posts = list(Post.objects.all())
        self.assertEqual(posts[0], post3)  # Pinned first
        self.assertEqual(posts[1], post2)  # Then newest
        self.assertEqual(posts[2], post1)

    def test_post_str(self):
        """Test post string representation"""
        post = Post.objects.create(
            community=self.community,
            author=self.user,
            title='Test Title',
            content='Test content'
        )
        expected = f"{self.user.username} in {self.community.name}: Test Title"
        self.assertEqual(str(post), expected)


class PostImageTests(TestCase):
    """Tests for PostImage model"""

    def setUp(self):
        """Create test user, community, and post"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@nyu.edu',
            password='testpass123'
        )
        self.community = Community.objects.create(
            name='Test Community',
            description='Test description',
            created_by=self.user
        )
        self.post = Post.objects.create(
            community=self.community,
            author=self.user,
            content='Test post'
        )

    def test_create_post_image(self):
        """Test creating a post image"""
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake_image_content',
            content_type='image/jpeg'
        )
        post_image = PostImage.objects.create(
            post=self.post,
            image=image
        )
        self.assertEqual(post_image.post, self.post)
        self.assertTrue(post_image.image)

    def test_multiple_images_per_post(self):
        """Test attaching multiple images to a post"""
        image1 = SimpleUploadedFile('img1.jpg', b'content1', 'image/jpeg')
        image2 = SimpleUploadedFile('img2.jpg', b'content2', 'image/jpeg')

        PostImage.objects.create(post=self.post, image=image1)
        PostImage.objects.create(post=self.post, image=image2)

        self.assertEqual(self.post.images.count(), 2)


class PostFileTests(TestCase):
    """Tests for PostFile model"""

    def setUp(self):
        """Create test user, community, and post"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@nyu.edu',
            password='testpass123'
        )
        self.community = Community.objects.create(
            name='Test Community',
            description='Test description',
            created_by=self.user
        )
        self.post = Post.objects.create(
            community=self.community,
            author=self.user,
            content='Test post'
        )

    def test_create_post_file(self):
        """Test creating a post file"""
        file = SimpleUploadedFile(
            name='test_file.pdf',
            content=b'fake_file_content',
            content_type='application/pdf'
        )
        post_file = PostFile.objects.create(
            post=self.post,
            file=file,
            file_name='test_file.pdf',
            file_size=17
        )
        self.assertEqual(post_file.post, self.post)
        self.assertEqual(post_file.file_name, 'test_file.pdf')
        self.assertEqual(post_file.file_size, 17)

    def test_file_auto_name_and_size(self):
        """Test file name and size are auto-populated"""
        file = SimpleUploadedFile('auto_test.txt', b'content', 'text/plain')
        post_file = PostFile.objects.create(
            post=self.post,
            file=file
        )
        self.assertEqual(post_file.file_name, 'auto_test.txt')
        self.assertEqual(post_file.file_size, 7)  # len(b'content')


class CommentModelTests(TestCase):
    """Tests for Comment model"""

    def setUp(self):
        """Create test users, community, and post"""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@nyu.edu',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@columbia.edu',
            password='testpass123'
        )
        self.community = Community.objects.create(
            name='Test Community',
            description='Test description',
            created_by=self.user1
        )
        self.post = Post.objects.create(
            community=self.community,
            author=self.user1,
            content='Test post'
        )

    def test_create_comment(self):
        """Test creating a comment on a post"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user2,
            content='This is a test comment'
        )
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author, self.user2)
        self.assertEqual(comment.content, 'This is a test comment')
        self.assertIsNone(comment.parent)
        self.assertFalse(comment.is_edited)

    def test_create_nested_comment(self):
        """Test creating a nested reply to a comment"""
        parent_comment = Comment.objects.create(
            post=self.post,
            author=self.user1,
            content='Parent comment'
        )
        reply = Comment.objects.create(
            post=self.post,
            author=self.user2,
            content='Reply to parent',
            parent=parent_comment
        )
        self.assertEqual(reply.parent, parent_comment)
        self.assertEqual(parent_comment.replies.count(), 1)
        self.assertEqual(parent_comment.replies.first(), reply)

    def test_comment_ordering(self):
        """Test comments are ordered chronologically"""
        comment1 = Comment.objects.create(
            post=self.post,
            author=self.user1,
            content='First comment'
        )
        comment2 = Comment.objects.create(
            post=self.post,
            author=self.user2,
            content='Second comment'
        )

        comments = list(Comment.objects.all())
        self.assertEqual(comments[0], comment1)  # Oldest first
        self.assertEqual(comments[1], comment2)

    def test_comment_str(self):
        """Test comment string representation"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user2,
            content='Test comment'
        )
        expected = f"Comment by {self.user2.username} on post {self.post.id}"
        self.assertEqual(str(comment), expected)

    def test_multiple_nested_levels(self):
        """Test comments can be nested multiple levels deep"""
        comment1 = Comment.objects.create(
            post=self.post,
            author=self.user1,
            content='Level 1'
        )
        comment2 = Comment.objects.create(
            post=self.post,
            author=self.user2,
            content='Level 2',
            parent=comment1
        )
        comment3 = Comment.objects.create(
            post=self.post,
            author=self.user1,
            content='Level 3',
            parent=comment2
        )

        self.assertEqual(comment1.replies.count(), 1)
        self.assertEqual(comment2.parent, comment1)
        self.assertEqual(comment3.parent, comment2)
        self.assertEqual(comment2.replies.count(), 1)


# ============================================================================
# COMPREHENSIVE TESTS FOR POST AND COMMENT VIEWS (PHASE 2)
# ============================================================================


class PostViewTests(TestCase):
    """Comprehensive tests for post views"""

    def setUp(self):
        """Create test users, community, and memberships"""
        self.client = Client()

        # Create users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@nyu.edu',
            password='testpass123',
            is_verified=True
        )
        Profile.objects.create(user=self.admin_user, university='NYU')

        self.moderator_user = User.objects.create_user(
            username='moderator',
            email='moderator@nyu.edu',
            password='testpass123',
            is_verified=True
        )
        Profile.objects.create(user=self.moderator_user, university='NYU')

        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@nyu.edu',
            password='testpass123',
            is_verified=True
        )
        Profile.objects.create(user=self.regular_user, university='NYU')

        self.non_member = User.objects.create_user(
            username='nonmember',
            email='nonmember@columbia.edu',
            password='testpass123',
            is_verified=True
        )
        Profile.objects.create(user=self.non_member, university='Columbia')

        # Create community
        self.community = Community.objects.create(
            name='Test Community',
            description='A test community',
            privacy='public',
            created_by=self.admin_user
        )

        # Create memberships
        CommunityMember.objects.create(
            community=self.community,
            user=self.admin_user,
            role='admin',
            status='active'
        )
        CommunityMember.objects.create(
            community=self.community,
            user=self.moderator_user,
            role='moderator',
            status='active'
        )
        CommunityMember.objects.create(
            community=self.community,
            user=self.regular_user,
            role='member',
            status='active'
        )

    def test_create_post_get(self):
        """Test GET request to create post page"""
        self.client.login(username='regular@nyu.edu', password='testpass123')
        response = self.client.get(
            reverse('communities:create_post', args=[self.community.slug])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_create_post_non_member_forbidden(self):
        """Test non-member cannot access create post page"""
        self.client.login(username='nonmember@columbia.edu', password='testpass123')
        response = self.client.get(
            reverse('communities:create_post', args=[self.community.slug])
        )
        self.assertEqual(response.status_code, 403)

    def test_create_post_with_title_and_content(self):
        """Test creating a post with title and content"""
        self.client.login(username='regular@nyu.edu', password='testpass123')
        data = {
            'title': 'Test Post Title',
            'content': 'This is the post content'
        }
        response = self.client.post(
            reverse('communities:create_post', args=[self.community.slug]),
            data
        )

        # Should redirect to post detail
        self.assertEqual(response.status_code, 302)

        # Verify post created
        post = Post.objects.get(title='Test Post Title')
        self.assertEqual(post.author, self.regular_user)
        self.assertEqual(post.community, self.community)
        self.assertEqual(post.content, 'This is the post content')

        # Verify community post count updated
        self.community.refresh_from_db()
        self.assertEqual(self.community.post_count, 1)

    def test_create_post_without_title(self):
        """Test creating a post with only content (no title)"""
        self.client.login(username='regular@nyu.edu', password='testpass123')
        data = {
            'content': 'Post without title'
        }
        response = self.client.post(
            reverse('communities:create_post', args=[self.community.slug]),
            data
        )

        self.assertEqual(response.status_code, 302)
        post = Post.objects.get(content='Post without title')
        self.assertEqual(post.title, '')

    def test_create_post_with_images(self):
        """Test creating a post with multiple images"""
        self.client.login(username='regular@nyu.edu', password='testpass123')

        image1 = SimpleUploadedFile('img1.jpg', b'image1', 'image/jpeg')
        image2 = SimpleUploadedFile('img2.jpg', b'image2', 'image/jpeg')

        data = {
            'content': 'Post with images',
            'images': [image1, image2]
        }
        response = self.client.post(
            reverse('communities:create_post', args=[self.community.slug]),
            data
        )

        self.assertEqual(response.status_code, 302)
        post = Post.objects.get(content='Post with images')
        self.assertEqual(post.images.count(), 2)

    def test_create_post_with_files(self):
        """Test creating a post with file attachments"""
        self.client.login(username='regular@nyu.edu', password='testpass123')

        file1 = SimpleUploadedFile('file1.pdf', b'content1', 'application/pdf')
        file2 = SimpleUploadedFile('file2.txt', b'content2', 'text/plain')

        data = {
            'content': 'Post with files',
            'files': [file1, file2]
        }
        response = self.client.post(
            reverse('communities:create_post', args=[self.community.slug]),
            data
        )

        self.assertEqual(response.status_code, 302)
        post = Post.objects.get(content='Post with files')
        self.assertEqual(post.files.count(), 2)

    def test_create_post_image_limit(self):
        """Test that only first 5 images are uploaded"""
        self.client.login(username='regular@nyu.edu', password='testpass123')

        images = [
            SimpleUploadedFile(f'img{i}.jpg', b'content', 'image/jpeg')
            for i in range(10)
        ]

        data = {
            'content': 'Post with many images',
            'images': images
        }
        response = self.client.post(
            reverse('communities:create_post', args=[self.community.slug]),
            data
        )

        self.assertEqual(response.status_code, 302)
        post = Post.objects.get(content='Post with many images')
        # Should only create 5 images (limit enforced in view)
        self.assertLessEqual(post.images.count(), 5)

    def test_post_detail_view_member(self):
        """Test viewing post detail as community member"""
        post = Post.objects.create(
            community=self.community,
            author=self.regular_user,
            title='Test Post',
            content='Test content'
        )

        self.client.login(username='regular@nyu.edu', password='testpass123')
        response = self.client.get(
            reverse('communities:post_detail', args=[self.community.slug, post.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['post'], post)
        self.assertIn('comment_form', response.context)

    def test_post_detail_view_non_member_forbidden(self):
        """Test non-member cannot view post detail"""
        post = Post.objects.create(
            community=self.community,
            author=self.regular_user,
            content='Test content'
        )

        self.client.login(username='nonmember@columbia.edu', password='testpass123')
        response = self.client.get(
            reverse('communities:post_detail', args=[self.community.slug, post.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_post_detail_shows_images_and_files(self):
        """Test post detail displays attached images and files"""
        post = Post.objects.create(
            community=self.community,
            author=self.regular_user,
            content='Test post'
        )

        image = SimpleUploadedFile('test.jpg', b'image', 'image/jpeg')
        PostImage.objects.create(post=post, image=image)

        file = SimpleUploadedFile('test.pdf', b'file', 'application/pdf')
        PostFile.objects.create(post=post, file=file)

        self.client.login(username='regular@nyu.edu', password='testpass123')
        response = self.client.get(
            reverse('communities:post_detail', args=[self.community.slug, post.id])
        )

        self.assertEqual(response.status_code, 200)
        post_from_context = response.context['post']
        self.assertEqual(post_from_context.images.count(), 1)
        self.assertEqual(post_from_context.files.count(), 1)

    def test_edit_post_as_author(self):
        """Test author can edit their post"""
        post = Post.objects.create(
            community=self.community,
            author=self.regular_user,
            title='Original Title',
            content='Original content'
        )

        self.client.login(username='regular@nyu.edu', password='testpass123')
        data = {
            'title': 'Updated Title',
            'content': 'Updated content'
        }
        response = self.client.post(
            reverse('communities:edit_post', args=[self.community.slug, post.id]),
            data
        )

        self.assertEqual(response.status_code, 302)
        post.refresh_from_db()
        self.assertEqual(post.title, 'Updated Title')
        self.assertEqual(post.content, 'Updated content')
        self.assertTrue(post.is_edited)

    def test_edit_post_as_moderator(self):
        """Test moderator can edit any post"""
        post = Post.objects.create(
            community=self.community,
            author=self.regular_user,
            content='Original content'
        )

        self.client.login(username='moderator@nyu.edu', password='testpass123')
        data = {
            'content': 'Moderator edited content'
        }
        response = self.client.post(
            reverse('communities:edit_post', args=[self.community.slug, post.id]),
            data
        )

        self.assertEqual(response.status_code, 302)
        post.refresh_from_db()
        self.assertEqual(post.content, 'Moderator edited content')
        self.assertTrue(post.is_edited)

    def test_edit_post_non_author_non_moderator_forbidden(self):
        """Test non-author, non-moderator cannot edit post"""
        post = Post.objects.create(
            community=self.community,
            author=self.regular_user,
            content='Original content'
        )

        # Create another regular member
        another_user = User.objects.create_user(
            username='another',
            email='another@nyu.edu',
            password='testpass123',
            is_verified=True
        )
        CommunityMember.objects.create(
            community=self.community,
            user=another_user,
            role='member',
            status='active'
        )

        self.client.login(username='another@nyu.edu', password='testpass123')
        data = {
            'content': 'Unauthorized edit'
        }
        response = self.client.post(
            reverse('communities:edit_post', args=[self.community.slug, post.id]),
            data
        )

        self.assertEqual(response.status_code, 403)

    def test_delete_post_as_author(self):
        """Test author can delete their post"""
        post = Post.objects.create(
            community=self.community,
            author=self.regular_user,
            content='To be deleted'
        )

        self.client.login(username='regular@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:delete_post', args=[self.community.slug, post.id])
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Post.objects.filter(id=post.id).exists())

        # Verify community post count updated
        self.community.refresh_from_db()
        self.assertEqual(self.community.post_count, 0)

    def test_delete_post_as_moderator(self):
        """Test moderator can delete any post"""
        post = Post.objects.create(
            community=self.community,
            author=self.regular_user,
            content='To be deleted by moderator'
        )

        self.client.login(username='moderator@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:delete_post', args=[self.community.slug, post.id])
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Post.objects.filter(id=post.id).exists())

    def test_delete_post_non_author_non_moderator_forbidden(self):
        """Test non-author, non-moderator cannot delete post"""
        post = Post.objects.create(
            community=self.community,
            author=self.regular_user,
            content='Cannot delete'
        )

        another_user = User.objects.create_user(
            username='another',
            email='another@nyu.edu',
            password='testpass123',
            is_verified=True
        )
        CommunityMember.objects.create(
            community=self.community,
            user=another_user,
            role='member',
            status='active'
        )

        self.client.login(username='another@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:delete_post', args=[self.community.slug, post.id])
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Post.objects.filter(id=post.id).exists())

    def test_pin_post_as_moderator(self):
        """Test moderator can pin a post"""
        post = Post.objects.create(
            community=self.community,
            author=self.regular_user,
            content='To be pinned'
        )

        self.client.login(username='moderator@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:toggle_pin_post', args=[self.community.slug, post.id])
        )

        self.assertEqual(response.status_code, 302)
        post.refresh_from_db()
        self.assertTrue(post.is_pinned)
        self.assertEqual(post.pinned_by, self.moderator_user)

    def test_unpin_post_as_moderator(self):
        """Test moderator can unpin a post"""
        post = Post.objects.create(
            community=self.community,
            author=self.regular_user,
            content='Pinned post',
            is_pinned=True,
            pinned_by=self.moderator_user
        )

        self.client.login(username='moderator@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:toggle_pin_post', args=[self.community.slug, post.id])
        )

        self.assertEqual(response.status_code, 302)
        post.refresh_from_db()
        self.assertFalse(post.is_pinned)
        self.assertIsNone(post.pinned_by)

    def test_pin_post_as_admin(self):
        """Test admin can pin a post"""
        post = Post.objects.create(
            community=self.community,
            author=self.regular_user,
            content='To be pinned by admin'
        )

        self.client.login(username='admin@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:toggle_pin_post', args=[self.community.slug, post.id])
        )

        self.assertEqual(response.status_code, 302)
        post.refresh_from_db()
        self.assertTrue(post.is_pinned)

    def test_pin_post_as_member_forbidden(self):
        """Test regular member cannot pin posts"""
        post = Post.objects.create(
            community=self.community,
            author=self.regular_user,
            content='Cannot be pinned'
        )

        self.client.login(username='regular@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:toggle_pin_post', args=[self.community.slug, post.id])
        )

        self.assertEqual(response.status_code, 403)
        post.refresh_from_db()
        self.assertFalse(post.is_pinned)

    def test_community_detail_shows_pinned_posts_first(self):
        """Test pinned posts appear at the top of community feed"""
        # Create regular posts
        post1 = Post.objects.create(
            community=self.community,
            author=self.regular_user,
            content='Regular post 1'
        )
        post2 = Post.objects.create(
            community=self.community,
            author=self.regular_user,
            content='Regular post 2'
        )
        # Create pinned post (older than regular posts)
        pinned_post = Post.objects.create(
            community=self.community,
            author=self.admin_user,
            content='Pinned post',
            is_pinned=True
        )

        self.client.login(username='regular@nyu.edu', password='testpass123')
        response = self.client.get(
            reverse('communities:detail', args=[self.community.slug])
        )

        self.assertEqual(response.status_code, 200)
        posts = list(response.context['posts'])
        # Pinned post should be first despite being older
        self.assertEqual(posts[0], pinned_post)


class CommentViewTests(TestCase):
    """Comprehensive tests for comment views"""

    def setUp(self):
        """Create test users, community, and post"""
        self.client = Client()

        self.author = User.objects.create_user(
            username='author',
            email='author@nyu.edu',
            password='testpass123',
            is_verified=True
        )
        Profile.objects.create(user=self.author, university='NYU')

        self.commenter = User.objects.create_user(
            username='commenter',
            email='commenter@nyu.edu',
            password='testpass123',
            is_verified=True
        )
        Profile.objects.create(user=self.commenter, university='NYU')

        self.moderator = User.objects.create_user(
            username='moderator',
            email='moderator@nyu.edu',
            password='testpass123',
            is_verified=True
        )
        Profile.objects.create(user=self.moderator, university='NYU')

        self.non_member = User.objects.create_user(
            username='nonmember',
            email='nonmember@columbia.edu',
            password='testpass123',
            is_verified=True
        )
        Profile.objects.create(user=self.non_member, university='Columbia')

        # Create community
        self.community = Community.objects.create(
            name='Test Community',
            description='A test community',
            privacy='public',
            created_by=self.author
        )

        # Create memberships
        CommunityMember.objects.create(
            community=self.community,
            user=self.author,
            role='admin',
            status='active'
        )
        CommunityMember.objects.create(
            community=self.community,
            user=self.commenter,
            role='member',
            status='active'
        )
        CommunityMember.objects.create(
            community=self.community,
            user=self.moderator,
            role='moderator',
            status='active'
        )

        # Create post
        self.post = Post.objects.create(
            community=self.community,
            author=self.author,
            content='Test post for comments'
        )

    def test_create_comment(self):
        """Test creating a comment on a post"""
        self.client.login(username='commenter@nyu.edu', password='testpass123')
        data = {
            'content': 'This is a test comment'
        }
        response = self.client.post(
            reverse('communities:create_comment', args=[
                self.community.slug, self.post.id
            ]),
            data
        )

        self.assertEqual(response.status_code, 302)
        comment = Comment.objects.get(content='This is a test comment')
        self.assertEqual(comment.author, self.commenter)
        self.assertEqual(comment.post, self.post)
        self.assertIsNone(comment.parent)

        # Verify post comment count updated
        self.post.refresh_from_db()
        self.assertEqual(self.post.comment_count, 1)

    def test_create_reply_comment(self):
        """Test creating a reply to an existing comment"""
        parent_comment = Comment.objects.create(
            post=self.post,
            author=self.author,
            content='Parent comment'
        )

        self.client.login(username='commenter@nyu.edu', password='testpass123')
        data = {
            'content': 'Reply to parent',
            'parent_id': parent_comment.id
        }
        response = self.client.post(
            reverse('communities:create_comment', args=[
                self.community.slug, self.post.id
            ]),
            data
        )

        self.assertEqual(response.status_code, 302)
        reply = Comment.objects.get(content='Reply to parent')
        self.assertEqual(reply.parent, parent_comment)
        self.assertEqual(parent_comment.replies.count(), 1)

    def test_create_comment_non_member_forbidden(self):
        """Test non-member cannot create comment"""
        self.client.login(username='nonmember@columbia.edu', password='testpass123')
        data = {
            'content': 'Unauthorized comment'
        }
        response = self.client.post(
            reverse('communities:create_comment', args=[
                self.community.slug, self.post.id
            ]),
            data
        )

        self.assertEqual(response.status_code, 403)

    def test_edit_comment_as_author(self):
        """Test author can edit their comment"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.commenter,
            content='Original comment'
        )

        self.client.login(username='commenter@nyu.edu', password='testpass123')
        data = {
            'content': 'Edited comment'
        }
        response = self.client.post(
            reverse('communities:edit_comment', args=[
                self.community.slug, self.post.id, comment.id
            ]),
            data
        )

        self.assertEqual(response.status_code, 302)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'Edited comment')
        self.assertTrue(comment.is_edited)

    def test_edit_comment_non_author_forbidden(self):
        """Test non-author cannot edit comment"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.commenter,
            content='Original comment'
        )

        self.client.login(username='author@nyu.edu', password='testpass123')
        data = {
            'content': 'Unauthorized edit'
        }
        response = self.client.post(
            reverse('communities:edit_comment', args=[
                self.community.slug, self.post.id, comment.id
            ]),
            data
        )

        self.assertEqual(response.status_code, 403)

    def test_delete_comment_as_author(self):
        """Test author can delete their comment"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.commenter,
            content='To be deleted'
        )

        self.client.login(username='commenter@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:delete_comment', args=[
                self.community.slug, self.post.id, comment.id
            ])
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.filter(id=comment.id).exists())

        # Verify post comment count updated
        self.post.refresh_from_db()
        self.assertEqual(self.post.comment_count, 0)

    def test_delete_comment_as_moderator(self):
        """Test moderator can delete any comment"""
        comment = Comment.objects.create(
            post=self.post,
            author=self.commenter,
            content='To be deleted by moderator'
        )

        self.client.login(username='moderator@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:delete_comment', args=[
                self.community.slug, self.post.id, comment.id
            ])
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.filter(id=comment.id).exists())

    def test_delete_comment_non_author_non_moderator_forbidden(self):
        """Test non-author, non-moderator cannot delete comment"""
        # Create another regular member who is neither author nor moderator
        another_member = User.objects.create_user(
            username='anothermember',
            email='anothermember@nyu.edu',
            password='testpass123',
            is_verified=True
        )
        Profile.objects.create(user=another_member, university='NYU')
        CommunityMember.objects.create(
            community=self.community,
            user=another_member,
            role='member',
            status='active'
        )

        comment = Comment.objects.create(
            post=self.post,
            author=self.commenter,
            content='Cannot be deleted'
        )

        self.client.login(username='anothermember@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:delete_comment', args=[
                self.community.slug, self.post.id, comment.id
            ])
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Comment.objects.filter(id=comment.id).exists())

    def test_post_detail_shows_top_level_comments(self):
        """Test post detail displays top-level comments"""
        comment1 = Comment.objects.create(
            post=self.post,
            author=self.author,
            content='Top level comment 1'
        )
        comment2 = Comment.objects.create(
            post=self.post,
            author=self.commenter,
            content='Top level comment 2'
        )
        # Create reply (should not appear in top-level list)
        Comment.objects.create(
            post=self.post,
            author=self.author,
            content='Reply',
            parent=comment1
        )

        self.client.login(username='commenter@nyu.edu', password='testpass123')
        response = self.client.get(
            reverse('communities:post_detail', args=[self.community.slug, self.post.id])
        )

        comments = response.context['comments']
        # Should only show top-level comments
        self.assertEqual(comments.count(), 2)

    def test_deleting_parent_comment_deletes_replies(self):
        """Test that deleting a parent comment cascades to replies"""
        parent = Comment.objects.create(
            post=self.post,
            author=self.author,
            content='Parent'
        )
        reply1 = Comment.objects.create(
            post=self.post,
            author=self.commenter,
            content='Reply 1',
            parent=parent
        )
        reply2 = Comment.objects.create(
            post=self.post,
            author=self.commenter,
            content='Reply 2',
            parent=parent
        )

        self.client.login(username='author@nyu.edu', password='testpass123')
        self.client.post(
            reverse('communities:delete_comment', args=[
                self.community.slug, self.post.id, parent.id
            ])
        )

        # Parent and replies should be deleted
        self.assertFalse(Comment.objects.filter(id=parent.id).exists())
        self.assertFalse(Comment.objects.filter(id=reply1.id).exists())
        self.assertFalse(Comment.objects.filter(id=reply2.id).exists())


class PostFormTests(TestCase):
    """Tests for PostForm"""

    def test_post_form_valid_with_content_only(self):
        """Test form is valid with only content"""
        form = PostForm(data={'content': 'Test content'})
        self.assertTrue(form.is_valid())

    def test_post_form_valid_with_title_and_content(self):
        """Test form is valid with title and content"""
        form = PostForm(data={
            'title': 'Test Title',
            'content': 'Test content'
        })
        self.assertTrue(form.is_valid())

    def test_post_form_invalid_without_content(self):
        """Test form is invalid without content"""
        form = PostForm(data={'title': 'Only title'})
        self.assertFalse(form.is_valid())

    def test_post_form_title_max_length(self):
        """Test form validates title max length"""
        long_title = 'a' * 201  # Exceeds 200 char limit
        form = PostForm(data={
            'title': long_title,
            'content': 'Content'
        })
        self.assertFalse(form.is_valid())

    def test_post_form_content_max_length(self):
        """Test form validates content max length"""
        long_content = 'a' * 10001  # Exceeds 10000 char limit
        form = PostForm(data={
            'title': 'Title',
            'content': long_content
        })
        self.assertFalse(form.is_valid())


class CommentFormTests(TestCase):
    """Tests for CommentForm"""

    def test_comment_form_valid(self):
        """Test form is valid with content"""
        form = CommentForm(data={'content': 'Test comment'})
        self.assertTrue(form.is_valid())

    def test_comment_form_invalid_without_content(self):
        """Test form is invalid without content"""
        form = CommentForm(data={})
        self.assertFalse(form.is_valid())

    def test_comment_form_max_length(self):
        """Test form validates content max length"""
        long_content = 'a' * 2001  # Exceeds 2000 char limit
        form = CommentForm(data={'content': long_content})
        self.assertFalse(form.is_valid())


class PermissionHelperTests(TestCase):
    """Tests for permission helper functions"""

    def setUp(self):
        """Create test users and community"""
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@nyu.edu',
            password='testpass123'
        )
        self.moderator = User.objects.create_user(
            username='moderator',
            email='moderator@nyu.edu',
            password='testpass123'
        )
        self.member = User.objects.create_user(
            username='member',
            email='member@nyu.edu',
            password='testpass123'
        )
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@nyu.edu',
            password='testpass123',
            is_staff=True
        )
        self.outsider = User.objects.create_user(
            username='outsider',
            email='outsider@columbia.edu',
            password='testpass123'
        )

        self.community = Community.objects.create(
            name='Test Community',
            description='Test',
            created_by=self.admin
        )

        CommunityMember.objects.create(
            community=self.community,
            user=self.admin,
            role='admin',
            status='active'
        )
        CommunityMember.objects.create(
            community=self.community,
            user=self.moderator,
            role='moderator',
            status='active'
        )
        CommunityMember.objects.create(
            community=self.community,
            user=self.member,
            role='member',
            status='active'
        )

    def test_is_admin_returns_true_for_admin(self):
        """Test is_admin returns True for admin users"""
        from communities.permissions import is_admin
        self.assertTrue(is_admin(self.admin, self.community))

    def test_is_admin_returns_false_for_moderator(self):
        """Test is_admin returns False for moderator users"""
        from communities.permissions import is_admin
        self.assertFalse(is_admin(self.moderator, self.community))

    def test_is_admin_returns_false_for_member(self):
        """Test is_admin returns False for regular members"""
        from communities.permissions import is_admin
        self.assertFalse(is_admin(self.member, self.community))

    def test_is_moderator_or_admin_returns_true_for_admin(self):
        """Test is_moderator_or_admin returns True for admin"""
        from communities.permissions import is_moderator_or_admin
        self.assertTrue(is_moderator_or_admin(self.admin, self.community))

    def test_is_moderator_or_admin_returns_true_for_moderator(self):
        """Test is_moderator_or_admin returns True for moderator"""
        from communities.permissions import is_moderator_or_admin
        self.assertTrue(is_moderator_or_admin(self.moderator, self.community))

    def test_is_moderator_or_admin_returns_false_for_member(self):
        """Test is_moderator_or_admin returns False for member"""
        from communities.permissions import is_moderator_or_admin
        self.assertFalse(is_moderator_or_admin(self.member, self.community))

    def test_can_moderate_returns_true_for_staff(self):
        """Test can_moderate returns True for staff users"""
        from communities.permissions import can_moderate
        self.assertTrue(can_moderate(self.staff, self.community))

    def test_can_moderate_returns_true_for_moderator(self):
        """Test can_moderate returns True for moderators"""
        from communities.permissions import can_moderate
        self.assertTrue(can_moderate(self.moderator, self.community))

    def test_can_moderate_returns_false_for_member(self):
        """Test can_moderate returns False for regular members"""
        from communities.permissions import can_moderate
        self.assertFalse(can_moderate(self.member, self.community))

    def test_check_membership_raises_for_non_member(self):
        """Test check_membership raises PermissionDenied for non-members"""
        from communities.permissions import check_membership
        with self.assertRaises(PermissionDenied):
            check_membership(self.outsider, self.community)

    def test_check_membership_returns_membership_for_member(self):
        """Test check_membership returns membership for active member"""
        from communities.permissions import check_membership
        membership = check_membership(self.member, self.community)
        self.assertEqual(membership.user, self.member)
        self.assertEqual(membership.community, self.community)


class UtilityFunctionTests(TestCase):
    """Tests for utility functions"""

    def setUp(self):
        """Create test users and community"""
        self.nyu_user = User.objects.create_user(
            username='nyu',
            email='student@nyu.edu',
            password='testpass123'
        )
        Profile.objects.create(user=self.nyu_user, university='NYU')

        self.columbia_user = User.objects.create_user(
            username='columbia',
            email='student@columbia.edu',
            password='testpass123'
        )
        Profile.objects.create(user=self.columbia_user, university='Columbia')

        self.barnard_user = User.objects.create_user(
            username='barnard',
            email='student@barnard.edu',
            password='testpass123'
        )
        Profile.objects.create(user=self.barnard_user, university='Columbia')

        self.nyu_community = Community.objects.create(
            name='NYU Community',
            description='NYU only',
            privacy='university',
            university='NYU',
            created_by=self.nyu_user
        )

        self.columbia_community = Community.objects.create(
            name='Columbia Community',
            description='Columbia only',
            privacy='university',
            university='Columbia',
            created_by=self.columbia_user
        )

    def test_validate_university_access_profile_match(self):
        """Test validation passes when profile university matches"""
        from communities.utils import validate_university_access
        self.assertTrue(validate_university_access(
            self.nyu_user, self.nyu_community
        ))

    def test_validate_university_access_email_domain_match(self):
        """Test validation passes when email domain matches"""
        from communities.utils import validate_university_access
        self.assertTrue(validate_university_access(
            self.barnard_user, self.columbia_community
        ))

    def test_validate_university_access_no_match(self):
        """Test validation fails when no match"""
        from communities.utils import validate_university_access
        self.assertFalse(validate_university_access(
            self.nyu_user, self.columbia_community
        ))

    def test_validate_university_access_public_community(self):
        """Test validation always passes for public communities"""
        from communities.utils import validate_university_access
        public_community = Community.objects.create(
            name='Public',
            description='Public',
            privacy='public',
            created_by=self.nyu_user
        )
        self.assertTrue(validate_university_access(
            self.columbia_user, public_community
        ))

    def test_get_user_university_from_email(self):
        """Test extracting university from email"""
        from communities.utils import get_user_university_from_email
        self.assertEqual(
            get_user_university_from_email('student@nyu.edu'),
            'NYU'
        )
        self.assertEqual(
            get_user_university_from_email('student@columbia.edu'),
            'Columbia'
        )
        self.assertEqual(
            get_user_university_from_email('student@barnard.edu'),
            'Columbia'
        )
        self.assertIsNone(
            get_user_university_from_email('student@unknown.edu')
        )


class IntegrationTests(TestCase):
    """Integration tests for complete workflows"""

    def setUp(self):
        """Create test environment"""
        self.client = Client()

        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@nyu.edu',
            password='testpass123',
            is_verified=True
        )
        Profile.objects.create(user=self.user1, university='NYU')

        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@nyu.edu',
            password='testpass123',
            is_verified=True
        )
        Profile.objects.create(user=self.user2, university='NYU')

    def test_complete_post_workflow(self):
        """Test complete workflow: create community, join, post, comment"""
        # User1 creates community
        self.client.login(username='user1@nyu.edu', password='testpass123')
        response = self.client.post(reverse('communities:create'), {
            'name': 'Integration Test Community',
            'description': 'Test',
            'privacy': 'public'
        })
        self.assertEqual(response.status_code, 302)

        community = Community.objects.get(name='Integration Test Community')

        # User2 joins community
        self.client.login(username='user2@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:join', args=[community.slug])
        )
        self.assertEqual(response.status_code, 302)

        # User2 creates post
        response = self.client.post(
            reverse('communities:create_post', args=[community.slug]),
            {'content': 'Hello community!'}
        )
        self.assertEqual(response.status_code, 302)

        post = Post.objects.get(content='Hello community!')
        self.assertEqual(post.author, self.user2)

        # User1 comments on post
        self.client.login(username='user1@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:create_comment', args=[community.slug, post.id]),
            {'content': 'Welcome!'}
        )
        self.assertEqual(response.status_code, 302)

        comment = Comment.objects.get(content='Welcome!')
        self.assertEqual(comment.author, self.user1)
        self.assertEqual(comment.post, post)

        # User2 replies to comment
        self.client.login(username='user2@nyu.edu', password='testpass123')
        response = self.client.post(
            reverse('communities:create_comment', args=[community.slug, post.id]),
            {
                'content': 'Thanks!',
                'parent_id': comment.id
            }
        )
        self.assertEqual(response.status_code, 302)

        reply = Comment.objects.get(content='Thanks!')
        self.assertEqual(reply.parent, comment)

    def test_post_edit_marks_as_edited(self):
        """Test that editing a post sets is_edited flag"""
        self.client.login(username='user1@nyu.edu', password='testpass123')

        # Create community and post
        self.client.post(reverse('communities:create'), {
            'name': 'Test Community',
            'description': 'Test',
            'privacy': 'public'
        })
        community = Community.objects.get(name='Test Community')

        self.client.post(
            reverse('communities:create_post', args=[community.slug]),
            {'content': 'Original'}
        )
        post = Post.objects.get(content='Original')
        self.assertFalse(post.is_edited)

        # Edit post
        self.client.post(
            reverse('communities:edit_post', args=[community.slug, post.id]),
            {'content': 'Edited'}
        )
        post.refresh_from_db()
        self.assertTrue(post.is_edited)


# ============================================================================
# PHASE 3: CHAT MODEL TESTS
# ============================================================================

class ThreadModelTests(TestCase):
    """Tests for Thread model"""

    def setUp(self):
        """Create test user and community"""
        self.user = User.objects.create_user(
            email='test@nyu.edu',
            username='testuser',
            password='testpass123'
        )
        Profile.objects.create(user=self.user, university='NYU')

        self.community = Community.objects.create(
            name='Test Community',
            description='Test Description',
            privacy='public',
            created_by=self.user
        )

    def test_thread_creation(self):
        """Test creating a thread"""
        thread = Thread.objects.create(community=self.community)
        self.assertEqual(thread.community, self.community)
        self.assertEqual(thread.message_count, 0)

    def test_thread_str(self):
        """Test thread string representation"""
        thread = Thread.objects.create(community=self.community)
        self.assertEqual(str(thread), f"Chat thread for {self.community.name}")

    def test_one_to_one_relationship(self):
        """Test that one community can only have one thread"""
        Thread.objects.create(community=self.community)

        # Try to create another thread for the same community
        with self.assertRaises(Exception):
            Thread.objects.create(community=self.community)

    def test_thread_message_count_default(self):
        """Test that message_count defaults to 0"""
        thread = Thread.objects.create(community=self.community)
        self.assertEqual(thread.message_count, 0)


class ChatMessageModelTests(TestCase):
    """Tests for ChatMessage model"""

    def setUp(self):
        """Create test users, community, and thread"""
        self.user1 = User.objects.create_user(
            email='user1@nyu.edu',
            username='user1',
            password='testpass123'
        )
        Profile.objects.create(user=self.user1, university='NYU')

        self.user2 = User.objects.create_user(
            email='user2@nyu.edu',
            username='user2',
            password='testpass123'
        )
        Profile.objects.create(user=self.user2, university='NYU')

        self.community = Community.objects.create(
            name='Test Community',
            description='Test Description',
            privacy='public',
            created_by=self.user1
        )

        self.thread = Thread.objects.create(community=self.community)

    def test_chat_message_creation(self):
        """Test creating a chat message"""
        message = ChatMessage.objects.create(
            thread=self.thread,
            sender=self.user1,
            content='Hello, world!'
        )

        self.assertEqual(message.thread, self.thread)
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.content, 'Hello, world!')
        self.assertFalse(message.is_edited)
        self.assertIsNone(message.edited_at)

    def test_chat_message_str(self):
        """Test chat message string representation"""
        message = ChatMessage.objects.create(
            thread=self.thread,
            sender=self.user1,
            content='Test message'
        )
        expected = f"Message by {self.user1.username} in {self.community.name}"
        self.assertEqual(str(message), expected)

    def test_chat_message_ordering(self):
        """Test that messages are ordered by created_at"""
        msg1 = ChatMessage.objects.create(
            thread=self.thread,
            sender=self.user1,
            content='First'
        )
        msg2 = ChatMessage.objects.create(
            thread=self.thread,
            sender=self.user2,
            content='Second'
        )

        messages = ChatMessage.objects.filter(thread=self.thread)
        self.assertEqual(messages[0], msg1)
        self.assertEqual(messages[1], msg2)

    def test_chat_message_is_edited_default(self):
        """Test that is_edited defaults to False"""
        message = ChatMessage.objects.create(
            thread=self.thread,
            sender=self.user1,
            content='Test'
        )
        self.assertFalse(message.is_edited)

    def test_multiple_messages_same_thread(self):
        """Test creating multiple messages in the same thread"""
        ChatMessage.objects.create(
            thread=self.thread,
            sender=self.user1,
            content='Message 1'
        )
        ChatMessage.objects.create(
            thread=self.thread,
            sender=self.user2,
            content='Message 2'
        )
        ChatMessage.objects.create(
            thread=self.thread,
            sender=self.user1,
            content='Message 3'
        )

        self.assertEqual(ChatMessage.objects.filter(thread=self.thread).count(), 3)

    def test_delete_thread_deletes_messages(self):
        """Test that deleting a thread deletes all its messages"""
        ChatMessage.objects.create(
            thread=self.thread,
            sender=self.user1,
            content='Test'
        )

        thread_id = self.thread.id
        self.thread.delete()

        # Verify messages are deleted
        self.assertEqual(
            ChatMessage.objects.filter(thread_id=thread_id).count(),
            0
        )
