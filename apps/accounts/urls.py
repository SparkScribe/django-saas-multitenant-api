"""Accounts URL routes."""

from django.urls import path

from apps.accounts.tokens import CustomTokenObtainPairView
from apps.accounts.views import MeView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("token/", CustomTokenObtainPairView.as_view(), name="auth-token"),
    path("me/", MeView.as_view(), name="auth-me"),
]
