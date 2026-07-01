"""Shared test fixtures for accounts and organizations."""

import pytest

from apps.accounts.models import User
from apps.organizations.models import Membership, MembershipRole, Organization


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
