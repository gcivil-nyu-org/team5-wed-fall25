"""
Views for communities app - Phase 1: Core Infrastructure
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST

from .models import Community, CommunityMember
from .forms import CommunityForm, JoinRequestForm
from .permissions import (
    check_membership, is_admin, is_moderator_or_admin,
    can_moderate, require_membership, require_moderator, require_admin
)
from .utils import validate_university_access


@login_required
def browse_communities(request):
    """Browse all public and university communities."""
    communities = Community.objects.filter(
        is_active=True
    ).annotate(
        member_count_actual=Count('memberships', filter=Q(memberships__status='active'))
    ).order_by('-created_at')

    # Get user's memberships for display
    user_memberships = set()
    if request.user.is_authenticated:
        user_memberships = set(
            CommunityMember.objects.filter(
                user=request.user,
                status='active'
            ).values_list('community_id', flat=True)
        )

    context = {
        'communities': communities,
        'user_memberships': user_memberships,
    }
    return render(request, 'communities/browse.html', context)


@login_required
def my_communities(request):
    """Show user's joined communities."""
    memberships = CommunityMember.objects.filter(
        user=request.user,
        status='active'
    ).select_related('community').order_by('-joined_at')

    context = {
        'memberships': memberships,
    }
    return render(request, 'communities/my_communities.html', context)


@login_required
def create_community(request):
    """Create a new community."""
    if request.method == 'POST':
        form = CommunityForm(request.POST, request.FILES)
        if form.is_valid():
            community = form.save(commit=False)
            community.created_by = request.user
            community.save()

            # Auto-add creator as admin
            CommunityMember.objects.create(
                community=community,
                user=request.user,
                role='admin',
                status='active'
            )

            # Update member count
            community.member_count = 1
            community.save()

            messages.success(request, f'Community "{community.name}" created successfully!')
            return redirect('communities:detail', slug=community.slug)
    else:
        form = CommunityForm()

    context = {'form': form}
    return render(request, 'communities/create.html', context)


def community_detail(request, slug):
    """Community home page."""
    community = get_object_or_404(Community, slug=slug, is_active=True)

    # Check if user is a member
    is_member = False
    membership = None
    if request.user.is_authenticated:
        try:
            membership = CommunityMember.objects.get(
                community=community,
                user=request.user
            )
            is_member = membership.status == 'active'
        except CommunityMember.DoesNotExist:
            pass

    # For private communities, only members can see details
    if community.privacy == 'private' and not is_member and not request.user.is_staff:
        messages.warning(request, 'This is a private community. Request to join to see details.')
        return redirect('communities:browse')

    # Get member count
    active_members = CommunityMember.objects.filter(
        community=community,
        status='active'
    ).select_related('user').order_by('-joined_at')[:10]  # Show first 10

    context = {
        'community': community,
        'is_member': is_member,
        'membership': membership,
        'active_members': active_members,
        'can_manage': membership and membership.role in ['admin', 'moderator'] if membership else False,
        'is_admin': membership and membership.role == 'admin' if membership else False,
    }
    return render(request, 'communities/detail.html', context)


@login_required
@require_admin
def community_settings(request, slug):
    """Edit community settings (admin only)."""
    community = get_object_or_404(Community, slug=slug, is_active=True)

    if request.method == 'POST':
        form = CommunityForm(request.POST, request.FILES, instance=community)
        if form.is_valid():
            form.save()
            messages.success(request, 'Community settings updated successfully!')
            return redirect('communities:detail', slug=community.slug)
    else:
        form = CommunityForm(instance=community)

    context = {
        'form': form,
        'community': community,
    }
    return render(request, 'communities/settings.html', context)


@login_required
@require_POST
def join_community(request, slug):
    """Join a community or request to join."""
    community = get_object_or_404(Community, slug=slug, is_active=True)

    # Check if already a member
    existing_membership = CommunityMember.objects.filter(
        community=community,
        user=request.user
    ).first()

    if existing_membership:
        if existing_membership.status == 'active':
            messages.info(request, 'You are already a member of this community.')
        elif existing_membership.status == 'pending':
            messages.info(request, 'Your join request is pending approval.')
        elif existing_membership.status == 'banned':
            messages.error(request, 'You have been banned from this community.')
        return redirect('communities:detail', slug=slug)

    # Check university access for university-restricted communities
    if community.privacy == 'university':
        if not validate_university_access(request.user, community):
            messages.error(
                request,
                f'This community is restricted to {community.university} students only.'
            )
            return redirect('communities:detail', slug=slug)

    # Handle different privacy levels
    if community.privacy == 'public' or community.privacy == 'university':
        # Instant join
        CommunityMember.objects.create(
            community=community,
            user=request.user,
            role='member',
            status='active'
        )
        # Update member count
        community.member_count = CommunityMember.objects.filter(
            community=community,
            status='active'
        ).count()
        community.save()
        messages.success(request, f'You joined {community.name}!')
    else:
        # Private community - create join request
        CommunityMember.objects.create(
            community=community,
            user=request.user,
            role='member',
            status='pending'
        )
        messages.success(request, 'Join request sent! Waiting for approval.')

    return redirect('communities:detail', slug=slug)


@login_required
@require_POST
def leave_community(request, slug):
    """Leave a community."""
    community = get_object_or_404(Community, slug=slug, is_active=True)

    try:
        membership = CommunityMember.objects.get(
            community=community,
            user=request.user,
            status='active'
        )

        # Prevent last admin from leaving
        if membership.role == 'admin':
            admin_count = CommunityMember.objects.filter(
                community=community,
                role='admin',
                status='active'
            ).count()
            if admin_count <= 1:
                messages.error(request, 'You are the last admin. Promote another member to admin before leaving.')
                return redirect('communities:detail', slug=slug)

        membership.delete()

        # Update member count
        community.member_count = CommunityMember.objects.filter(
            community=community,
            status='active'
        ).count()
        community.save()

        messages.success(request, f'You left {community.name}.')
        return redirect('communities:browse')

    except CommunityMember.DoesNotExist:
        messages.error(request, 'You are not a member of this community.')
        return redirect('communities:detail', slug=slug)


@login_required
@require_membership
def member_list(request, slug):
    """View all community members."""
    community = get_object_or_404(Community, slug=slug, is_active=True)

    members = CommunityMember.objects.filter(
        community=community,
        status='active'
    ).select_related('user', 'user__profile').order_by('-role', '-joined_at')

    # Check if user can manage members
    user_membership = CommunityMember.objects.get(
        community=community,
        user=request.user,
        status='active'
    )

    context = {
        'community': community,
        'members': members,
        'can_manage': user_membership.role in ['admin', 'moderator'],
        'is_admin': user_membership.role == 'admin',
    }
    return render(request, 'communities/members.html', context)


@login_required
@require_POST
def promote_member(request, slug, user_id):
    """Promote member to moderator (admin only)."""
    community = get_object_or_404(Community, slug=slug, is_active=True)

    # Check if requester is admin
    if not is_admin(request.user, community):
        raise PermissionDenied("Only admins can promote members")

    # Get target membership
    target_membership = get_object_or_404(
        CommunityMember,
        community=community,
        user_id=user_id,
        status='active'
    )

    if target_membership.role == 'member':
        target_membership.role = 'moderator'
        target_membership.save()
        messages.success(request, f'{target_membership.user.username} promoted to moderator.')
    else:
        messages.info(request, f'{target_membership.user.username} is already a moderator or admin.')

    return redirect('communities:members', slug=slug)


@login_required
@require_POST
def demote_member(request, slug, user_id):
    """Demote moderator to member (admin only)."""
    community = get_object_or_404(Community, slug=slug, is_active=True)

    # Check if requester is admin
    if not is_admin(request.user, community):
        raise PermissionDenied("Only admins can demote members")

    # Get target membership
    target_membership = get_object_or_404(
        CommunityMember,
        community=community,
        user_id=user_id,
        status='active'
    )

    if target_membership.role == 'moderator':
        target_membership.role = 'member'
        target_membership.save()
        messages.success(request, f'{target_membership.user.username} demoted to member.')
    else:
        messages.info(request, 'User is not a moderator.')

    return redirect('communities:members', slug=slug)


@login_required
@require_POST
def remove_member(request, slug, user_id):
    """Remove member from community (moderator+ can remove)."""
    community = get_object_or_404(Community, slug=slug, is_active=True)

    # Check if requester can moderate
    if not can_moderate(request.user, community):
        raise PermissionDenied("Only moderators and admins can remove members")

    # Get target membership
    target_membership = get_object_or_404(
        CommunityMember,
        community=community,
        user_id=user_id,
        status='active'
    )

    # Can't remove admins
    if target_membership.role == 'admin':
        messages.error(request, 'Cannot remove an admin.')
        return redirect('communities:members', slug=slug)

    # Can't remove self
    if target_membership.user == request.user:
        messages.error(request, 'Use the "Leave Community" option to leave.')
        return redirect('communities:members', slug=slug)

    username = target_membership.user.username
    target_membership.delete()

    # Update member count
    community.member_count = CommunityMember.objects.filter(
        community=community,
        status='active'
    ).count()
    community.save()

    messages.success(request, f'{username} has been removed from the community.')
    return redirect('communities:members', slug=slug)


@login_required
@require_POST
def ban_member(request, slug, user_id):
    """Ban member from community (moderator+)."""
    community = get_object_or_404(Community, slug=slug, is_active=True)

    # Check if requester can moderate
    if not can_moderate(request.user, community):
        raise PermissionDenied("Only moderators and admins can ban members")

    # Get target membership
    target_membership = get_object_or_404(
        CommunityMember,
        community=community,
        user_id=user_id
    )

    # Can't ban admins
    if target_membership.role == 'admin':
        messages.error(request, 'Cannot ban an admin.')
        return redirect('communities:members', slug=slug)

    # Can't ban self
    if target_membership.user == request.user:
        messages.error(request, 'Cannot ban yourself.')
        return redirect('communities:members', slug=slug)

    username = target_membership.user.username
    target_membership.status = 'banned'
    target_membership.save()

    # Update member count if they were active
    community.member_count = CommunityMember.objects.filter(
        community=community,
        status='active'
    ).count()
    community.save()

    messages.success(request, f'{username} has been banned from the community.')
    return redirect('communities:members', slug=slug)


@login_required
@require_moderator
def join_requests(request, slug):
    """View pending join requests (moderator+)."""
    community = get_object_or_404(Community, slug=slug, is_active=True)

    pending_requests = CommunityMember.objects.filter(
        community=community,
        status='pending'
    ).select_related('user', 'user__profile').order_by('-joined_at')

    context = {
        'community': community,
        'pending_requests': pending_requests,
    }
    return render(request, 'communities/join_requests.html', context)


@login_required
@require_POST
def approve_request(request, slug, user_id):
    """Approve join request (moderator+)."""
    community = get_object_or_404(Community, slug=slug, is_active=True)

    # Check if requester can moderate
    if not can_moderate(request.user, community):
        raise PermissionDenied("Only moderators and admins can approve requests")

    # Get join request
    join_request = get_object_or_404(
        CommunityMember,
        user__id=user_id,
        community=community,
        status='pending'
    )

    join_request.status = 'active'
    join_request.reviewed_by = request.user
    join_request.save()

    # Update member count
    community.member_count = CommunityMember.objects.filter(
        community=community,
        status='active'
    ).count()
    community.save()

    messages.success(request, f'Approved {join_request.user.username} to join the community.')
    return redirect('communities:join_requests', slug=slug)


@login_required
@require_POST
def reject_request(request, slug, user_id):
    """Reject join request (moderator+)."""
    community = get_object_or_404(Community, slug=slug, is_active=True)

    # Check if requester can moderate
    if not can_moderate(request.user, community):
        raise PermissionDenied("Only moderators and admins can reject requests")

    # Get join request
    join_request = get_object_or_404(
        CommunityMember,
        user__id=user_id,
        community=community,
        status='pending'
    )

    username = join_request.user.username
    join_request.delete()

    messages.success(request, f'Rejected {username}\'s join request.')
    return redirect('communities:join_requests', slug=slug)
