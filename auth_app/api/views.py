from rest_framework import status
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView)
from .serializers import CustomTokenObtainPairSerializer, RegistrationSerializer
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from datetime import timedelta
from django.core.signing import TimestampSigner
from .functions import send_confirmation_email

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