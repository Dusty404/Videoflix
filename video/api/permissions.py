from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class HasJWTPermission(BasePermission):
    message = "Ein gültiger Login ist erforderlich."

    def has_permission(self, request, view):
        token = request.COOKIES.get("access_token")

        if not token:
            return False

        authentication = JWTAuthentication()

        try:
            validated_token = authentication.get_validated_token(token)
            authentication.get_user(validated_token)
        except (InvalidToken, AuthenticationFailed):
            return False

        return True