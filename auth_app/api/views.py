from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView)
from .serializers import CustomTokenObtainPairSerializer, RegistrationSerializer
from .functions import send_confirmation_email, check_activation_token
from django.utils.http import urlsafe_base64_decode
from django.core import signing

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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(rais_exception=True)
        response = Response({"message": "Login erfolgreich"})
      
        refresh = serializer.validated_data["refresh"]
        access = serializer.validated_data["access"]

        response.set_cookie(
            key="access",
            value=access,
            httponly=True,
            secure=True,
            samesite="Lax"
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            secure=True,
            samesite="Lax"
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
                serializer.is_valid(raise_exeption=True)
            except:
                return Response(
                      {"detail": "Refresh token invalid!"},
                      status=status.HTTP_400_BAD_REQUEST
                )

            access_token = serializer.validated_data.get("access")

            response = Response({"message": "access Token refreshed"})
            response.set_cookie(
                        key="access_token",
                        value=access_token,
                        httponly=True,
                        secure=True,
                        samesite="Lax"
                    )

class AccountActivationView(APIView):
    http_method_names = ["get"]

    def get(self, request, uidb64, token):
        try:
            data = check_activation_token(token)
        except signing.SignatureExpired:
            return Response({"message": "This activation link has expired."}, status=status.HTTP_400_BAD_REQUEST)
        except signing.BadSignature:
         return Response({"message": "This activation link is invalid."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=user_id)
        except (ValueError, TypeError, OverflowError, User.DoesNotExist):
            return Response({"message": "This activation link is invalid."}, status=status.HTTP_400_BAD_REQUEST)

        if (
            data.get("user_id") != str(user.pk)
            or data.get("email") != user.email
        ):
            return Response({"message": "This activation link is invalid."}, status=status.HTTP_400_BAD_REQUEST)

        if user.is_active:
            return Response({"message": "Your account is already active"})

        user.is_active = True
        user.save(update_fields=["is_active"])

        return Response({"message": "Account successfully activated."})