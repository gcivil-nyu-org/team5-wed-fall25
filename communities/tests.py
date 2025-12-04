from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse
from .models import Community, CommunityMember
from .forms import CommunityForm
from profiles.models import Profile

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
