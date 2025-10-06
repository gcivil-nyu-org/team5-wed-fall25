from django.shortcuts import render

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
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

