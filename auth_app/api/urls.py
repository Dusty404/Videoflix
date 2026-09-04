from django.urls import path
from .views import CookieTokenObtainPairView, CookieRefreshTokenView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CookieRefreshTokenView.as_view(), name='token_refresh'),
]