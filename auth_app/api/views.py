from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView)

class RegisterView(APIView):
     pass

class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh = response.data.get("refresh")
        access = response.data.get("access")

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

        response.data = {"message": "Login erfolgreich"}


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