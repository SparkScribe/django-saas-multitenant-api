"""Phase 2 auth API tests."""

import pytest
from rest_framework import status

from apps.accounts.models import User
from apps.organizations.models import Membership, MembershipRole, Organization
from tests.conftest import decode_access_token, obtain_access_token


@pytest.mark.django_db
class TestRegisterAPI:
    def test_register_user_without_organization(self, api_client) -> None:
        response = api_client.post(
            "/api/v1/auth/register/",
            {"email": "newuser@example.com", "password": "securepass"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["email"] == "newuser@example.com"
        assert User.objects.filter(email="newuser@example.com").exists()
        assert Membership.objects.filter(user__email="newuser@example.com").count() == 0

    def test_register_user_with_organization(self, api_client) -> None:
        response = api_client.post(
            "/api/v1/auth/register/",
            {
                "email": "founder@example.com",
                "password": "securepass",
                "organization_name": "Startup Inc",
                "organization_slug": "startup-inc",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

        user = User.objects.get(email="founder@example.com")
        org = Organization.objects.get(slug="startup-inc")
        membership = Membership.objects.get(user=user, organization=org)
        assert membership.role == MembershipRole.OWNER

    def test_register_auto_generates_slug(self, api_client) -> None:
        response = api_client.post(
            "/api/v1/auth/register/",
            {
                "email": "auto@example.com",
                "password": "securepass",
                "organization_name": "Auto Slug Co",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Organization.objects.filter(slug="auto-slug-co").exists()

    def test_register_duplicate_email(self, api_client, user: User) -> None:
        response = api_client.post(
            "/api/v1/auth/register/",
            {"email": user.email, "password": "securepass"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_register_duplicate_slug(self, api_client, organization: Organization) -> None:
        response = api_client.post(
            "/api/v1/auth/register/",
            {
                "email": "another@example.com",
                "password": "securepass",
                "organization_name": "Another Org",
                "organization_slug": organization.slug,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "organization_slug" in response.data


@pytest.mark.django_db
class TestTokenAPI:
    def test_token_obtain_with_single_org_includes_organization_id(
        self,
        api_client,
        user: User,
        owner_membership: Membership,
        organization: Organization,
    ) -> None:
        access = obtain_access_token(api_client, user.email, "testpass123")
        claims = decode_access_token(access)
        assert claims["organization_id"] == str(organization.id)

    def test_token_obtain_with_multiple_orgs_omits_organization_id(
        self,
        api_client,
        user: User,
        organization: Organization,
        other_organization: Organization,
    ) -> None:
        Membership.objects.create(user=user, organization=organization, role=MembershipRole.OWNER)
        Membership.objects.create(user=user, organization=other_organization, role=MembershipRole.MEMBER)

        access = obtain_access_token(api_client, user.email, "testpass123")
        claims = decode_access_token(access)
        assert "organization_id" not in claims

    def test_token_obtain_with_no_org_omits_organization_id(self, api_client, user: User) -> None:
        access = obtain_access_token(api_client, user.email, "testpass123")
        claims = decode_access_token(access)
        assert "organization_id" not in claims

    def test_token_obtain_invalid_credentials(self, api_client, user: User) -> None:
        response = api_client.post(
            "/api/v1/auth/token/",
            {"email": user.email, "password": "wrong-password"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestMeAPI:
    def test_me_returns_user_and_memberships(
        self,
        auth_client,
        user: User,
        owner_membership: Membership,
        organization: Organization,
    ) -> None:
        response = auth_client.get("/api/v1/auth/me/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email
        assert len(response.data["memberships"]) == 1
        assert response.data["memberships"][0]["organization"]["id"] == str(organization.id)
        assert response.data["memberships"][0]["role"] == MembershipRole.OWNER

    def test_me_requires_authentication(self, api_client) -> None:
        response = api_client.get("/api/v1/auth/me/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
