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
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_confirmation_email(user)

        return Response({"message": "Benutzer erstellt"}, status=status.HTTP_201_CREATED)

        

class CookieTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
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
    