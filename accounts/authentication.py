from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils.translation import gettext_lazy 

from accounts.models import User
from core.utils.jwt import decode_jwt_token

# Given a JWT, find or create a User. 
# this is a reusable func.
def authenticate_cognito_user(token):
    payload = decode_jwt_token(token)
    print("payload: ", payload)

    sub = payload.get("sub")
    email = payload.get("email")
    first_name = payload.get("given_name", "")
    last_name = payload.get("family_name", "")

    user, created = User.objects.get_or_create(
        cognito_sub=sub,
        defaults={
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        }
    )
    return user

# this class is required by Django REST Framework (DRF)
class CognitoJWTAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith(self.keyword):
            return None  # Let DRF try other authenticators if present

        token = auth_header[len(self.keyword):].strip()

        try:
            # use the token to get the user
            user = authenticate_cognito_user(token)
        except Exception as error:
            raise AuthenticationFailed(gettext_lazy("Invalid or expired token")) from error

        # DRF expects (user, auth) tuple
        return (user, None)  