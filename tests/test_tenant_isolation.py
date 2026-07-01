"""
Mandatory tenant isolation tests (PRD §10).

These tests prove row-level data isolation between organizations and must pass
before shipping.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.context import ORGANIZATION_REQUIRED_CODE
from apps.organizations.models import Membership, MembershipRole, Organization
from apps.projects.models import Project
from tests.conftest import obtain_access_token


@dataclass
class TenantScenario:
    """Two isolated tenants with distinct owners."""

    org_1: Organization
    org_2: Organization
    user_a: User
    user_b: User


@pytest.fixture
def tenant_scenario(db) -> TenantScenario:
    org_1 = Organization.objects.create(name="Tenant One", slug="tenant-one")
    org_2 = Organization.objects.create(name="Tenant Two", slug="tenant-two")
    user_a = User.objects.create_user(email="user-a@tenant.test", password="tenant-pass-a")
    user_b = User.objects.create_user(email="user-b@tenant.test", password="tenant-pass-b")
    Membership.objects.create(user=user_a, organization=org_1, role=MembershipRole.OWNER)
    Membership.objects.create(user=user_b, organization=org_2, role=MembershipRole.OWNER)
    return TenantScenario(org_1=org_1, org_2=org_2, user_a=user_a, user_b=user_b)


def client_for_user(
    api_client: APIClient,
    user: User,
    password: str,
    *,
    organization_id: str | None = None,
) -> APIClient:
    """Return an API client authenticated as ``user`` with optional org context."""
    access = obtain_access_token(api_client, user.email, password)
    credentials = {"HTTP_AUTHORIZATION": f"Bearer {access}"}
    if organization_id is not None:
        credentials["HTTP_X_ORGANIZATION_ID"] = organization_id
    api_client.credentials(**credentials)
    return api_client


@pytest.mark.django_db
class TestTenantIsolation:
    """Critical cross-tenant isolation guarantees."""

    def test_user_a_org_1_creates_project(
        self,
        api_client: APIClient,
        tenant_scenario: TenantScenario,
    ) -> None:
        client = client_for_user(api_client, tenant_scenario.user_a, "tenant-pass-a")

        response = client.post(
            "/api/v1/projects/",
            {"name": "Org 1 Secret Project", "description": "Tenant 1 only"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["organization_id"] == str(tenant_scenario.org_1.id)
        assert Project.objects.filter(organization=tenant_scenario.org_1).count() == 1

    def test_user_b_org_2_list_projects_does_not_see_org_1_project(
        self,
        api_client: APIClient,
        tenant_scenario: TenantScenario,
    ) -> None:
        Project.objects.create(
            organization=tenant_scenario.org_1,
            name="Org 1 Secret Project",
            description="Must not leak to tenant 2",
        )
        Project.objects.create(
            organization=tenant_scenario.org_2,
            name="Org 2 Visible Project",
            description="Belongs to tenant 2",
        )

        client = client_for_user(
            api_client,
            tenant_scenario.user_b,
            "tenant-pass-b",
            organization_id=str(tenant_scenario.org_2.id),
        )
        response = client.get("/api/v1/projects/")

        assert response.status_code == status.HTTP_200_OK
        project_ids = {item["id"] for item in response.data}
        org_1_project_ids = {
            str(project_id)
            for project_id in Project.objects.filter(
                organization=tenant_scenario.org_1
            ).values_list("id", flat=True)
        }
        assert project_ids.isdisjoint(org_1_project_ids)
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Org 2 Visible Project"

    def test_user_b_get_org_1_project_id_returns_404(
        self,
        api_client: APIClient,
        tenant_scenario: TenantScenario,
    ) -> None:
        org_1_project = Project.objects.create(
            organization=tenant_scenario.org_1,
            name="Org 1 Secret Project",
            description="Must not be readable by tenant 2",
        )

        client = client_for_user(
            api_client,
            tenant_scenario.user_b,
            "tenant-pass-b",
            organization_id=str(tenant_scenario.org_2.id),
        )
        response = client.get(f"/api/v1/projects/{org_1_project.id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_missing_organization_header_when_user_has_two_orgs_returns_403(
        self,
        api_client: APIClient,
        tenant_scenario: TenantScenario,
    ) -> None:
        Membership.objects.create(
            user=tenant_scenario.user_a,
            organization=tenant_scenario.org_2,
            role=MembershipRole.MEMBER,
        )

        client = client_for_user(api_client, tenant_scenario.user_a, "tenant-pass-a")
        response = client.get("/api/v1/projects/")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == ORGANIZATION_REQUIRED_CODE

    def test_user_b_cannot_update_org_1_project(
        self,
        api_client: APIClient,
        tenant_scenario: TenantScenario,
    ) -> None:
        org_1_project = Project.objects.create(
            organization=tenant_scenario.org_1,
            name="Immutable Across Tenants",
            description="",
        )

        client = client_for_user(
            api_client,
            tenant_scenario.user_b,
            "tenant-pass-b",
            organization_id=str(tenant_scenario.org_2.id),
        )
        response = client.patch(
            f"/api/v1/projects/{org_1_project.id}/",
            {"name": "Hijacked"},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        org_1_project.refresh_from_db()
        assert org_1_project.name == "Immutable Across Tenants"

    def test_user_b_cannot_delete_org_1_project(
        self,
        api_client: APIClient,
        tenant_scenario: TenantScenario,
    ) -> None:
        org_1_project = Project.objects.create(
            organization=tenant_scenario.org_1,
            name="Protected Project",
            description="",
        )

        client = client_for_user(
            api_client,
            tenant_scenario.user_b,
            "tenant-pass-b",
            organization_id=str(tenant_scenario.org_2.id),
        )
        response = client.delete(f"/api/v1/projects/{org_1_project.id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Project.objects.filter(pk=org_1_project.pk).exists()
