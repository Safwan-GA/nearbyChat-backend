from firebase.firebase_admin import db, fcm, firebase_auth
from django.http import JsonResponse

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from firebase_admin import auth


def verify_firebase_token(request):
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return None, JsonResponse({"error": "Missing auth token"}, status=401)

    token = auth_header.split(" ")[1]

    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token, None
    except Exception:
        return None, JsonResponse({"error": "Invalid token"}, status=401)


class FirebaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return None  # DRF will handle unauthenticated users

        token = auth_header.split(" ")[1]

        try:
            decoded_token = auth.verify_id_token(token)
        except Exception:
            raise AuthenticationFailed("Invalid Firebase token")

        return (decoded_token, None)

