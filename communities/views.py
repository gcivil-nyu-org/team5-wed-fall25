"""
Views for communities app - Phase 1: Core Infrastructure & Phase 2: Posts and Comments
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from .models import Community, CommunityMember, Post, PostImage, PostFile, Comment
from .forms import CommunityForm, JoinRequestForm, PostForm, CommentForm
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

    # Get posts for members (Phase 2)
    posts = None
    if is_member:
        posts = Post.objects.filter(
            community=community
        ).select_related('author', 'author__profile').prefetch_related(
            'images', 'files'
        ).order_by('-is_pinned', '-created_at')[:10]  # Show first 10 posts

    context = {
        'community': community,
        'is_member': is_member,
        'membership': membership,
        'active_members': active_members,
        'posts': posts,
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


# ============================================================================
# PHASE 2: POSTS AND COMMENTS VIEWS
# ============================================================================

@login_required
@require_membership
def create_post(request, slug):
    """Create a new post in a community (members only)."""
    community = get_object_or_404(Community, slug=slug, is_active=True)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.community = community
            post.author = request.user
            post.save()

            # Handle multiple image uploads
            images = request.FILES.getlist('images')
            for image in images[:5]:  # Limit to 5 images
                PostImage.objects.create(post=post, image=image)

            # Handle multiple file uploads
            files = request.FILES.getlist('files')
            for file in files[:5]:  # Limit to 5 files
                PostFile.objects.create(post=post, file=file)

            # Update community post count
            community.post_count = Post.objects.filter(community=community).count()
            community.save()

            messages.success(request, 'Post created successfully!')
            return redirect('communities:post_detail', slug=slug, post_id=post.id)
    else:
        form = PostForm()

    context = {
        'community': community,
        'form': form,
    }
    return render(request, 'communities/create_post.html', context)


@login_required
@require_membership
def post_detail(request, slug, post_id):
    """View a single post with its comments (members only)."""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    post = get_object_or_404(
        Post.objects.select_related('author', 'author__profile')
        .prefetch_related('images', 'files'),
        id=post_id,
        community=community
    )

    # Get top-level comments with their replies
    comments = Comment.objects.filter(
        post=post,
        parent__isnull=True
    ).select_related('author', 'author__profile').prefetch_related('replies__author__profile')

    # Check if current user is the author or moderator
    is_author = request.user == post.author
    can_pin = can_moderate(request.user, community)

    comment_form = CommentForm()

    context = {
        'community': community,
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'is_author': is_author,
        'can_pin': can_pin,
    }
    return render(request, 'communities/post_detail.html', context)


@login_required
def edit_post(request, slug, post_id):
    """Edit a post (author or moderator only)."""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    post = get_object_or_404(Post, id=post_id, community=community)

    # Check permissions: author or moderator
    if request.user != post.author and not can_moderate(request.user, community):
        raise PermissionDenied("Only the author or moderators can edit this post")

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.is_edited = True
            post.save()

            # Handle new image uploads
            images = request.FILES.getlist('images')
            for image in images[:5]:
                PostImage.objects.create(post=post, image=image)

            # Handle new file uploads
            files = request.FILES.getlist('files')
            for file in files[:5]:
                PostFile.objects.create(post=post, file=file)

            messages.success(request, 'Post updated successfully!')
            return redirect('communities:post_detail', slug=slug, post_id=post.id)
    else:
        form = PostForm(instance=post)

    context = {
        'community': community,
        'post': post,
        'form': form,
    }
    return render(request, 'communities/edit_post.html', context)


@login_required
@require_POST
def delete_post(request, slug, post_id):
    """Delete a post (author or moderator only)."""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    post = get_object_or_404(Post, id=post_id, community=community)

    # Check permissions: author or moderator
    if request.user != post.author and not can_moderate(request.user, community):
        raise PermissionDenied("Only the author or moderators can delete this post")

    post.delete()

    # Update community post count
    community.post_count = Post.objects.filter(community=community).count()
    community.save()

    messages.success(request, 'Post deleted successfully!')
    return redirect('communities:detail', slug=slug)


@login_required
@require_POST
def toggle_pin_post(request, slug, post_id):
    """Pin or unpin a post (moderator+ only)."""
    community = get_object_or_404(Community, slug=slug, is_active=True)

    # Check if user can moderate
    if not can_moderate(request.user, community):
        raise PermissionDenied("Only moderators and admins can pin posts")

    post = get_object_or_404(Post, id=post_id, community=community)

    if post.is_pinned:
        post.is_pinned = False
        post.pinned_by = None
        messages.success(request, 'Post unpinned.')
    else:
        post.is_pinned = True
        post.pinned_by = request.user
        messages.success(request, 'Post pinned to top of feed.')

    post.save()
    return redirect('communities:post_detail', slug=slug, post_id=post.id)


@login_required
@require_POST
def create_comment(request, slug, post_id):
    """Create a comment on a post (members only)."""
    community = get_object_or_404(Community, slug=slug, is_active=True)

    # Check membership
    check_membership(request.user, community)

    post = get_object_or_404(Post, id=post_id, community=community)

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user

        # Check if this is a reply to another comment
        parent_id = request.POST.get('parent_id')
        if parent_id:
            parent_comment = get_object_or_404(Comment, id=parent_id, post=post)
            comment.parent = parent_comment

        comment.save()

        # Update post comment count
        post.comment_count = Comment.objects.filter(post=post).count()
        post.save()

        messages.success(request, 'Comment posted!')
    else:
        messages.error(request, 'Error posting comment. Please try again.')

    return redirect('communities:post_detail', slug=slug, post_id=post_id)


@login_required
def edit_comment(request, slug, post_id, comment_id):
    """Edit a comment (author only)."""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    post = get_object_or_404(Post, id=post_id, community=community)
    comment = get_object_or_404(Comment, id=comment_id, post=post)

    # Only author can edit their comment
    if request.user != comment.author:
        raise PermissionDenied("Only the author can edit this comment")

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.is_edited = True
            comment.save()
            messages.success(request, 'Comment updated!')
            return redirect('communities:post_detail', slug=slug, post_id=post_id)
    else:
        form = CommentForm(instance=comment)

    context = {
        'community': community,
        'post': post,
        'comment': comment,
        'form': form,
    }
    return render(request, 'communities/edit_comment.html', context)


@login_required
@require_POST
def delete_comment(request, slug, post_id, comment_id):
    """Delete a comment (author or moderator only)."""
    community = get_object_or_404(Community, slug=slug, is_active=True)
    post = get_object_or_404(Post, id=post_id, community=community)
    comment = get_object_or_404(Comment, id=comment_id, post=post)

    # Check permissions: author or moderator
    if request.user != comment.author and not can_moderate(request.user, community):
        raise PermissionDenied("Only the author or moderators can delete this comment")

    comment.delete()

    # Update post comment count
    post.comment_count = Comment.objects.filter(post=post).count()
    post.save()

    messages.success(request, 'Comment deleted!')
    return redirect('communities:post_detail', slug=slug, post_id=post_id)
