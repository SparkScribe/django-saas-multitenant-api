"""Shared test fixtures for accounts and organizations."""

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import User
from apps.organizations.models import Membership, MembershipRole, Organization


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db) -> User:
    return User.objects.create_user(email="alice@example.com", password="testpass123")


@pytest.fixture
def other_user(db) -> User:
    return User.objects.create_user(email="bob@example.com", password="testpass123")


@pytest.fixture
def organization(db) -> Organization:
    return Organization.objects.create(name="Acme Corp", slug="acme-corp")


@pytest.fixture
def other_organization(db) -> Organization:
    return Organization.objects.create(name="Globex Inc", slug="globex-inc")


@pytest.fixture
def owner_membership(user: User, organization: Organization) -> Membership:
    return Membership.objects.create(
        user=user,
        organization=organization,
        role=MembershipRole.OWNER,
    )


@pytest.fixture
def member_membership(other_user: User, organization: Organization) -> Membership:
    return Membership.objects.create(
        user=other_user,
        organization=organization,
        role=MembershipRole.MEMBER,
    )


def obtain_access_token(api_client: APIClient, email: str, password: str) -> str:
    response = api_client.post(
        "/api/v1/auth/token/",
        {"email": email, "password": password},
        format="json",
    )
    assert response.status_code == 200, response.data
    return response.data["access"]


@pytest.fixture
def auth_client(api_client: APIClient, user: User, owner_membership: Membership) -> APIClient:
    access = obtain_access_token(api_client, user.email, "testpass123")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return api_client


def decode_access_token(token: str) -> dict:
    return AccessToken(token).payload
