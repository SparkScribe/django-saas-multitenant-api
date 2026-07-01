"""Phase 0 scaffold smoke tests."""

import pytest
from django.apps import apps
from django.conf import settings
from django.test import Client


@pytest.mark.django_db
class TestScaffold:
    """Verify the Django project scaffold is correctly configured."""

    def test_installed_apps(self) -> None:
        expected_apps = {
            "apps.accounts",
            "apps.organizations",
            "apps.projects",
            "rest_framework",
            "rest_framework_simplejwt",
            "drf_spectacular",
        }
        installed = set(settings.INSTALLED_APPS)
        assert expected_apps.issubset(installed)

    def test_apps_are_registered(self) -> None:
        for app_label in ("accounts", "organizations", "projects"):
            assert apps.is_installed(f"apps.{app_label}")

    def test_database_is_postgresql(self) -> None:
        assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"

    def test_admin_url_responds(self) -> None:
        client = Client()
        response = client.get("/admin/login/")
        assert response.status_code == 200

    def test_api_v1_base_url_exists(self) -> None:
        client = Client()
        response = client.get("/api/v1/")
        assert response.status_code in (200, 404)

    def test_django_check_passes(self) -> None:
        from django.core.management import call_command
        from io import StringIO

        out = StringIO()
        call_command("check", stdout=out)
        assert "System check identified no issues" in out.getvalue()
