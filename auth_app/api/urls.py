from django.urls import path
from .views import CookieTokenObtainPairView, CookieRefreshTokenView, RegisterView, AccountActivationView, LogoutView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', LogoutView.as_view(), name="logout"),
    path('token/refresh/', CookieRefreshTokenView.as_view(), name='token_refresh'),
    path('activate/<str:uidb64>/<str:token>/', AccountActivationView.as_view(), name="activate")
]