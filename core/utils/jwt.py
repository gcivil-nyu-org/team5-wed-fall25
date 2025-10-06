import json
import jwt
import requests
from jwt.algorithms import RSAAlgorithm
from django.conf import settings
from jwt.exceptions import InvalidTokenError

JWKS_URL = f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"

# Cache JWKS to avoid fetching on every request
_jwks_cache = {}

def get_jwks():
    global _jwks_cache
    if not _jwks_cache:
        print("JWKS_URL: ", JWKS_URL)
        response = requests.get(JWKS_URL)
        response.raise_for_status()
        _jwks_cache = {key["kid"]: key for key in response.json()["keys"]}
    return _jwks_cache

def decode_jwt_token(token: str):
    try:
        # Get unverified header to extract 'kid'
        headers = jwt.get_unverified_header(token)
        kid = headers["kid"]

        # Get public key from JWKS
        jwks = get_jwks()
        if kid not in jwks:
            _jwks_cache.clear()  # force refresh
            jwks = get_jwks()
        key = jwks[kid]

        # Convert JWKS to public key
        public_key = RSAAlgorithm.from_jwk(json.dumps(key))

        # Decode & verify
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
            issuer=f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}",
        )

        return payload

    except InvalidTokenError as error:
        raise ValueError(f"Invalid token: {error}")
    
# audience=settings.COGNITO_FRONTEND_CLIENT_ID,
    
