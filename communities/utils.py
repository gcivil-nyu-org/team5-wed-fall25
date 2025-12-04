"""
Utility functions for communities app.
"""

# University email domain mappings
UNIVERSITY_EMAIL_DOMAINS = {
    'NYU': ['nyu.edu'],
    'Columbia': ['columbia.edu', 'barnard.edu'],
    'Fordham': ['fordham.edu'],
    'CUNY': ['cuny.edu', 'hunter.cuny.edu', 'brooklyn.cuny.edu', 'ccny.cuny.edu'],
    'Pace': ['pace.edu'],
    'The New School': ['newschool.edu'],
}


def validate_university_access(user, community):
    """
    Validate if user can access a university-restricted community.

    Checks in priority order:
    1. User's profile.university matches community.university
    2. User's email domain matches allowed domains for community.university

    Args:
        user: User instance
        community: Community instance

    Returns:
        bool: True if user can access, False otherwise
    """
    # Non-university communities are always accessible
    if community.privacy != 'university':
        return True

    # Check profile university first (most reliable)
    if hasattr(user, 'profile') and user.profile.university == community.university:
        return True

    # Check email domain as fallback
    if '@' in user.email:
        user_domain = user.email.split('@')[1]
        allowed_domains = UNIVERSITY_EMAIL_DOMAINS.get(community.university, [])
        return user_domain in allowed_domains

    return False


def get_user_university_from_email(email):
    """
    Extract university from email domain.

    Args:
        email: Email address

    Returns:
        str or None: University name if domain matches, None otherwise
    """
    if '@' not in email:
        return None

    domain = email.split('@')[1]

    for university, domains in UNIVERSITY_EMAIL_DOMAINS.items():
        if domain in domains:
            return university

    return None
