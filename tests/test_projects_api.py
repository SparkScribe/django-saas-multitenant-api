"""Phase 3 projects and organizations API tests."""

import pytest
from rest_framework import status

from apps.organizations.models import Membership, MembershipRole, Organization
from apps.projects.models import Project
from tests.conftest import obtain_access_token


@pytest.fixture
def auth_client_with_org(api_client, user, owner_membership, organization):
    access = obtain_access_token(api_client, user.email, "testpass123")
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {access}",
        HTTP_X_ORGANIZATION_ID=str(organization.id),
    )
    return api_client


@pytest.fixture
def other_org_owner_client(api_client, other_user, other_organization):
    Membership.objects.create(
        user=other_user,
        organization=other_organization,
        role=MembershipRole.OWNER,
    )
    access = obtain_access_token(api_client, other_user.email, "testpass123")
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {access}",
        HTTP_X_ORGANIZATION_ID=str(other_organization.id),
    )
    return api_client


@pytest.fixture
def project_in_org(organization) -> Project:
    return Project.objects.create(
        organization=organization,
        name="Org 1 Project",
        description="Visible only to org 1",
    )


@pytest.fixture
def project_in_other_org(other_organization) -> Project:
    return Project.objects.create(
        organization=other_organization,
        name="Org 2 Project",
        description="Visible only to org 2",
    )


@pytest.mark.django_db
class TestOrganizationAPI:
    def test_list_organizations_for_authenticated_user(
        self,
        auth_client,
        user,
        organization,
        owner_membership,
    ) -> None:
        response = auth_client.get("/api/v1/organizations/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == str(organization.id)

    def test_create_organization(self, api_client, user) -> None:
        access = obtain_access_token(api_client, user.email, "testpass123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = api_client.post(
            "/api/v1/organizations/",
            {"name": "New Org", "slug": "new-org"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["slug"] == "new-org"
        assert Membership.objects.filter(
            user=user,
            organization_id=response.data["id"],
            role=MembershipRole.OWNER,
        ).exists()

    def test_list_organizations_requires_authentication(self, api_client) -> None:
        response = api_client.get("/api/v1/organizations/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProjectAPI:
    def test_create_project(self, auth_client, organization, owner_membership) -> None:
        response = auth_client.post(
            "/api/v1/projects/",
            {"name": "New Project", "description": "A tenant project"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Project"
        assert response.data["organization_id"] == str(organization.id)
        assert Project.objects.filter(organization=organization).count() == 1

    def test_list_projects_only_in_current_org(
        self,
        auth_client_with_org,
        organization,
        other_organization,
        project_in_org,
        project_in_other_org,
        owner_membership,
    ) -> None:
        response = auth_client_with_org.get("/api/v1/projects/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == str(project_in_org.id)

    def test_retrieve_project_in_current_org(
        self,
        auth_client,
        project_in_org,
        owner_membership,
    ) -> None:
        response = auth_client.get(f"/api/v1/projects/{project_in_org.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == project_in_org.name

    def test_retrieve_project_in_other_org_returns_404(
        self,
        auth_client,
        project_in_other_org,
        owner_membership,
    ) -> None:
        response = auth_client.get(f"/api/v1/projects/{project_in_other_org.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_project(self, auth_client, project_in_org, owner_membership) -> None:
        response = auth_client.patch(
            f"/api/v1/projects/{project_in_org.id}/",
            {"name": "Updated Name"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        project_in_org.refresh_from_db()
        assert project_in_org.name == "Updated Name"

    def test_delete_project(self, auth_client, project_in_org, owner_membership) -> None:
        response = auth_client.delete(f"/api/v1/projects/{project_in_org.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Project.objects.filter(pk=project_in_org.pk).exists()

    def test_missing_organization_context_returns_403(self, api_client, user) -> None:
        org_a = Organization.objects.create(name="Org A", slug="org-a")
        org_b = Organization.objects.create(name="Org B", slug="org-b")
        Membership.objects.create(user=user, organization=org_a, role=MembershipRole.OWNER)
        Membership.objects.create(user=user, organization=org_b, role=MembershipRole.MEMBER)

        access = obtain_access_token(api_client, user.email, "testpass123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = api_client.get("/api/v1/projects/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "organization_required"

    def test_other_org_user_cannot_see_foreign_project(
        self,
        other_org_owner_client,
        project_in_org,
    ) -> None:
        response = other_org_owner_client.get("/api/v1/projects/")
        assert response.status_code == status.HTTP_200_OK
        project_ids = {item["id"] for item in response.data}
        assert str(project_in_org.id) not in project_ids

    def test_projects_require_authentication(self, api_client) -> None:
        response = api_client.get("/api/v1/projects/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
