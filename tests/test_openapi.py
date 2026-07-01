"""OpenAPI schema tests."""

import yaml
import pytest


@pytest.mark.django_db
class TestOpenAPISchema:
    def test_schema_endpoint_returns_200(self, api_client) -> None:
        response = api_client.get("/api/schema/")
        assert response.status_code == 200
        assert response["Content-Type"].startswith("application/vnd.oai.openapi")

    def test_schema_contains_core_paths(self, api_client) -> None:
        response = api_client.get("/api/schema/")
        schema = yaml.safe_load(response.content)
        paths = schema.get("paths", {})
        assert "/api/v1/auth/register/" in paths
        assert "/api/v1/auth/token/" in paths
        assert "/api/v1/auth/me/" in paths
        assert "/api/v1/organizations/" in paths
        assert "/api/v1/projects/" in paths

    def test_swagger_ui_returns_200(self, api_client) -> None:
        response = api_client.get("/api/docs/")
        assert response.status_code == 200

    def test_redoc_returns_200(self, api_client) -> None:
        response = api_client.get("/api/redoc/")
        assert response.status_code == 200

    def test_spectacular_validate_command(self) -> None:
        from io import StringIO

        from django.core.management import call_command

        out = StringIO()
        call_command("spectacular", "--validate", stdout=out)
        assert out.getvalue().startswith("openapi:")
