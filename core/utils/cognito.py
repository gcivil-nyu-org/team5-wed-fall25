"""
Utility functions for AWS Cognito integration
"""
from django.conf import settings


def get_cognito_domain():
    """
    Generate the correct Cognito domain URL from settings.
    
    Format: https://{region}{subdomain}.auth.{region}.amazoncognito.com
    Example: https://us-east-1a2xtskfof.auth.us-east-1.amazoncognito.com
    
    From user pool ID like "us-east-1_A2XTSkfoF":
    - Extract region: "us-east-1"
    - Extract subdomain: "A2XTSkfoF"
    - Convert subdomain to lowercase: "a2xtskfof"
    - Combine: "us-east-1a2xtskfof"
    """
    pool_id = settings.COGNITO_USER_POOL_ID
    region = settings.COGNITO_REGION
    
    # Split the pool ID to get the subdomain (part after '_')
    # Example: "us-east-1_A2XTSkfoF" -> ["us-east-1", "A2XTSkfoF"]
    if '_' in pool_id:
        subdomain = pool_id.split('_')[1].lower()
    else:
        # Fallback if format is different
        subdomain = pool_id.lower()
    
    # Build the complete domain
    cognito_domain = f"https://{region}{subdomain}.auth.{region}.amazoncognito.com"
    
    return cognito_domain


def get_cognito_token_url():
    """
    Get the Cognito OAuth2 token endpoint URL.
    Used for exchanging authorization codes for tokens.
    """
    domain = get_cognito_domain()
    return f"{domain}/oauth2/token"


def get_cognito_login_url(response_type='code', redirect_uri=None, scopes=None):
    """
    Generate a complete Cognito login URL.
    
    Args:
        response_type: 'code' or 'token' (default: 'code')
        redirect_uri: Where to redirect after login (default: http://localhost:8000/auth/callback/)
        scopes: List of scopes (default: ['email', 'openid', 'phone'])
    
    Returns:
        Complete Cognito login URL
    """
    if redirect_uri is None:
        redirect_uri = 'http://localhost:8000/auth/callback/'
    
    if scopes is None:
        scopes = ['email', 'openid', 'phone']
    
    scope_string = '+'.join(scopes)
    domain = get_cognito_domain()
    client_id = settings.COGNITO_FRONTEND_CLIENT_ID
    
    return (
        f"{domain}/login?"
        f"client_id={client_id}&"
        f"response_type={response_type}&"
        f"scope={scope_string}&"
        f"redirect_uri={redirect_uri}"
    )


def get_cognito_logout_url(redirect_uri=None):
    """
    Generate Cognito logout URL.
    
    Args:
        redirect_uri: Where to redirect after logout (default: http://localhost:8000/)
    
    Returns:
        Complete Cognito logout URL
    """
    if redirect_uri is None:
        redirect_uri = 'http://localhost:8000/'
    
    domain = get_cognito_domain()
    client_id = settings.COGNITO_FRONTEND_CLIENT_ID
    
    return f"{domain}/logout?client_id={client_id}&logout_uri={redirect_uri}"