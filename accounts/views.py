from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import base64

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from accounts.authentication import CognitoJWTAuthentication

from rest_framework.decorators import api_view
from rest_framework.response import Response
from accounts.authentication import authenticate_cognito_user

@api_view(['GET'])
def protected_view(request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = authenticate_cognito_user(token)
    return Response({"message": f"Hello, {user.first_name}!"})

@api_view(['GET'])
@authentication_classes([CognitoJWTAuthentication])
@permission_classes([IsAuthenticated])
def user_profile_view(request):
    user = request.user
    return Response({
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "created_at": user.created_at,
    })

def login_page_view(request):
    """
    GET /auth/login/
    Simple HTML page that redirects to Cognito and extracts tokens
    """
    return render(request, 'templates.login.html')

def cognito_callback_view(request):
    """
    Handles callback from Cognito after authentication.
    For implicit flow: displays tokens (from URL fragment via JS)
    For code flow: exchanges code for tokens
    """
    code = request.GET.get('code')
    
    if code:
        # Authorization Code flow - exchange code for tokens
        return JsonResponse({
            'message': 'Authorization code received',
            'code': code,
            'next_step': 'Exchange this code for tokens using /auth/exchange/'
        })
    
    # Implicit flow - tokens are in URL fragment, handled by JavaScript
    return render(request, 'templates.callback.html')


@csrf_exempt
@api_view(['POST'])
def token_exchange_view(request):
    """
    POST /auth/exchange/
    Exchanges authorization code for tokens
    Body: {"code": "authorization_code"}
    """
    code = request.data.get('code')
    
    if not code:
        return Response({'error': 'Code is required'}, status=400)
    
    # Prepare token endpoint request
    token_url = f"https://{settings.COGNITO_USER_POOL_ID.split('_')[1].lower()}.auth.{settings.COGNITO_REGION}.amazoncognito.com/oauth2/token"
    
    # Encode client credentials
    credentials = f"{settings.COGNITO_BACKEND_CLIENT_ID}:{settings.COGNITO_BACKEND_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {encoded_credentials}'
    }
    
    data = {
        'grant_type': 'authorization_code',
        'client_id': settings.COGNITO_BACKEND_CLIENT_ID,
        'code': code,
        'redirect_uri': 'http://localhost:8000/auth/callback/'
    }
    
    try:
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()
        tokens = response.json()
        
        return Response({
            'id_token': tokens.get('id_token'),
            'access_token': tokens.get('access_token'),
            'refresh_token': tokens.get('refresh_token'),
            'expires_in': tokens.get('expires_in'),
        })
    except requests.exceptions.RequestException as e:
        return Response({
            'error': 'Failed to exchange code for tokens',
            'details': str(e)
        }, status=400)
