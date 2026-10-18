from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView)
from .serializers import CustomTokenObtainPairSerializer, RegistrationSerializer, CheckAccountForPasswordResetSerializer, PasswordResetSerializer
from .functions import send_confirmation_email, check_activation_token, send_password_reset_email
from django.utils.http import urlsafe_base64_decode
from django.core import signing
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

User = get_user_model()

class RegisterView(APIView):
    serializer_class = RegistrationSerializer

    def post(self, request, *args, **kwargs):
        """
        Create an inactive account and send its activation email.

        Args:
            request (Request): The incoming HTTP request.
            *args: Additional positional arguments supplied by the framework.
            **kwargs: Additional keyword arguments supplied by the framework.

        Returns:
            Response: HTTP 201 confirming account creation.

        Raises:
            ValidationError: If registration data is invalid.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_confirmation_email(user)

        return Response({"message": "Benutzer erstellt"}, status=status.HTTP_201_CREATED)

        

class CookieTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """
        Authenticate an active user and set secure HTTP-only JWT cookies.

        Args:
            request (Request): The incoming request containing email and password.
            *args: Additional positional arguments supplied by the framework.
            **kwargs: Additional keyword arguments supplied by the framework.

        Returns:
            Response: Login confirmation with token cookies, or HTTP 403 for an inactive account with valid credentials.

        Raises:
            ValidationError: If the supplied credentials fail serializer validation.
            AuthenticationFailed: If authentication is rejected.
        """
        email = request.data.get("email")
        password = request.data.get("password")

        user = None
        if isinstance(email, str) and email.strip():
            user = User.objects.filter(
                email__iexact=email.strip()
            ).first()

        if (user is not None and not user.is_active and isinstance(password, str) and user.check_password(password)):
            return Response({"detail": ("Bitte überprüfe deine Eingaben und versuche es erneut.")}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response = Response({"message": "Login erfolgreich"})

        response.set_cookie(
            key="access_token",
            value=serializer.validated_data["access"],
            httponly=True,
            secure=True,
            samesite="Lax",
        )

        response.set_cookie(
            key="refresh_token",
            value=serializer.validated_data["refresh"],
            httponly=True,
            secure=True,
            samesite="Lax",
        )

        return response


class CookieRefreshTokenView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        """
        Validate the refresh cookie and replace the access-token cookie.

        Args:
            request (Request): The incoming HTTP request.
            *args: Additional positional arguments supplied by the framework.
            **kwargs: Additional keyword arguments supplied by the framework.

        Returns:
            Response: Refresh confirmation, HTTP 400 for a missing cookie, or HTTP 401 when refresh validation fails.
        """
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token is None:
            return Response(
                {"detail": "Refresh token not found!"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except:
            return Response({"detail": "Refresh token invalid!"}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = serializer.validated_data.get("access")

        response = Response({"message": "access Token refreshed"})
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="Lax"
            )

        return response

class LogoutView(APIView):
    http_method_names = ["post"]

    def post(self, request):
        """
        Blacklist the supplied refresh token and remove both JWT cookies.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            Response: HTTP 200 confirming logout. Invalid refresh tokens are ignored.
        """
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass

        response = Response({"detail": "Logout successful."})
        response.delete_cookie("access_token", path="/", samesite="Lax")
        response.delete_cookie("refresh_token", path="/", samesite="Lax")

        return response

class AccountActivationView(APIView):
    http_method_names = ["get"]

    def get(self, request, uidb64, token):
        """
        Verify a signed activation link and activate the matching account.

        Args:
            request (Request): The incoming HTTP request.
            uidb64 (str): URL-safe Base64-encoded user ID.
            token (str): Signed activation token, valid for 24 hours.

        Returns:
            Response: HTTP 200 for an activated or already active account, or HTTP 400 for a handled invalid link.
        """
        try:
            data = check_activation_token(token)
        except signing.SignatureExpired:
            return Response({"message": "This activation link has expired."}, status=status.HTTP_400_BAD_REQUEST)
        except signing.BadSignature:
         return Response({"message": "This activation link is invalid. signatur"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=user_id)
        except (ValueError, TypeError, OverflowError, User.DoesNotExist):
            return Response({"message": "This activation link is invalid. uid"}, status=status.HTTP_400_BAD_REQUEST)
        
        if data != str(user.pk):
            return Response(
            {"message": "This activation link is invalid."},
            status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_active:
            return Response({"message": "Your account is already active"}, status=status.HTTP_200_OK)

        user.is_active = True
        user.save(update_fields=["is_active"])

        return Response({"message": "Account successfully activated."})

class PasswordResetView(APIView):
    http_method_names = ["post"]

    def post(self, request):
        """
        Send a reset email when an account matches the supplied email address.

        Return the same confirmation for existing and unknown addresses.

        Args:
            request (Request): The incoming request containing an email address.

        Returns:
            Response: HTTP 200 with a generic reset-email confirmation.

        Raises:
            ValidationError: If the email field is invalid.
        """
        serializer = CheckAccountForPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.filter(email__iexact=email).first()

        if user is not None:
            send_password_reset_email(user)
        return Response({"detail": "An email has been sent to reset your password."})

class SafeResetPasswordView(APIView):
    http_method_names = ["post"]

    def post(self, request, uidb64, token):
        """
        Validate a reset token and save the newly hashed password.

        Args:
            request (Request): The incoming request containing new_password and confirm_password.
            uidb64 (str): URL-safe Base64-encoded user ID.
            token (str): Password reset token from the email link.

        Returns:
            Response: HTTP 200 after updating the password, or HTTP 400 for a handled invalid or expired link.

        Raises:
            ValidationError: If password fields are invalid or do not match.
        """
        password = request.data.get("new_password")
        confirm_password= request.data.get("confirm_password")

        try:
            user_id = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=user_id)
        except (ValueError, TypeError, OverflowError, User.DoesNotExist):
            return Response({"message": "This activation link is invalid."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response(
            {"message": "Reset-Link is invalid or expired."},
            status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PasswordResetSerializer(data={"password": password, "confirm_password": confirm_password})

        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password"])
            
        return Response({"detail": "Your Password has been successfully reset."})
    