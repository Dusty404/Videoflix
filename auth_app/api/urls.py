from django.urls import path
from .views import CookieTokenObtainPairView, CookieRefreshTokenView, RegisterView, AccountActivationView, LogoutView, PasswordResetView, SafeResetPasswordView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', LogoutView.as_view(), name="logout"),
    path('token/refresh/', CookieRefreshTokenView.as_view(), name='token_refresh'),
    path('activate/<str:uidb64>/<str:token>/', AccountActivationView.as_view(), name="activate"),
    path('password_reset/', PasswordResetView.as_view(), name="password_reset_send"),
    path('password_confirm/<str:uidb64>/<str:token>/', SafeResetPasswordView.as_view(), name="password_reset"),
]