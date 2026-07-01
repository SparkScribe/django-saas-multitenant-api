"""API v1 URL configuration."""

from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.accounts.urls")),
    path("organizations/", include("apps.organizations.urls")),
    path("projects/", include("apps.projects.urls")),
]
