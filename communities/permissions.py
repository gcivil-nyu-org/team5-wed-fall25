"""
Permission helpers and decorators for communities app.
"""
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from functools import wraps
from .models import Community, CommunityMember


def check_membership(user, community, status='active'):
    """
    Check if user is an active member of the community.

    Args:
        user: User instance
        community: Community instance
        status: Membership status to check (default: 'active')

    Returns:
        CommunityMember instance if found

    Raises:
        PermissionDenied if user is not a member with the specified status
    """
    try:
        return CommunityMember.objects.get(
            user=user,
            community=community,
            status=status
        )
    except CommunityMember.DoesNotExist:
        raise PermissionDenied("You are not a member of this community")


def is_admin(user, community):
    """
    Check if user is an admin of the community.

    Args:
        user: User instance
        community: Community instance

    Returns:
        True if user is admin, False otherwise
    """
    try:
        membership = CommunityMember.objects.get(
            user=user,
            community=community,
            status='active'
        )
        return membership.role == 'admin'
    except CommunityMember.DoesNotExist:
        return False


def is_moderator_or_admin(user, community):
    """
    Check if user is a moderator or admin of the community.

    Args:
        user: User instance
        community: Community instance

    Returns:
        True if user is moderator or admin, False otherwise
    """
    try:
        membership = CommunityMember.objects.get(
            user=user,
            community=community,
            status='active'
        )
        return membership.role in ['moderator', 'admin']
    except CommunityMember.DoesNotExist:
        return False


def can_moderate(user, community):
    """
    Check if user can perform moderation actions.
    Includes staff override (staff users can moderate any community).

    Args:
        user: User instance
        community: Community instance

    Returns:
        True if user can moderate, False otherwise
    """
    return is_moderator_or_admin(user, community) or user.is_staff


# Decorators

def require_membership(view_func):
    """
    Decorator to require active membership in community.
    Assumes slug parameter in URL.

    Usage:
        @login_required
        @require_membership
        def my_view(request, slug):
            ...
    """
    @wraps(view_func)
    def wrapper(request, slug, *args, **kwargs):
        community = get_object_or_404(Community, slug=slug)
        check_membership(request.user, community)
        return view_func(request, slug, *args, **kwargs)
    return wrapper


def require_moderator(view_func):
    """
    Decorator to require moderator or admin role.
    Assumes slug parameter in URL.

    Usage:
        @login_required
        @require_moderator
        def my_view(request, slug):
            ...
    """
    @wraps(view_func)
    def wrapper(request, slug, *args, **kwargs):
        community = get_object_or_404(Community, slug=slug)
        if not can_moderate(request.user, community):
            raise PermissionDenied("You must be a moderator or admin")
        return view_func(request, slug, *args, **kwargs)
    return wrapper


def require_admin(view_func):
    """
    Decorator to require admin role.
    Assumes slug parameter in URL.

    Usage:
        @login_required
        @require_admin
        def my_view(request, slug):
            ...
    """
    @wraps(view_func)
    def wrapper(request, slug, *args, **kwargs):
        community = get_object_or_404(Community, slug=slug)
        if not is_admin(request.user, community):
            raise PermissionDenied("You must be an admin")
        return view_func(request, slug, *args, **kwargs)
    return wrapper
