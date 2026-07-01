"""Phase 1 model tests for User, Organization, and Membership."""

import uuid

import pytest
from django.db import IntegrityError

from apps.accounts.models import User
from apps.organizations.models import Membership, MembershipRole, Organization


@pytest.mark.django_db
class TestUserModel:
    def test_create_user_with_email(self) -> None:
        user = User.objects.create_user(email="user@example.com", password="securepass")
        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.email == "user@example.com"
        assert user.check_password("securepass")
        assert user.is_active is True
        assert user.is_staff is False

    def test_create_superuser(self) -> None:
        user = User.objects.create_superuser(email="admin@example.com", password="adminpass")
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_email_must_be_unique(self) -> None:
        User.objects.create_user(email="dup@example.com", password="pass")
        with pytest.raises(IntegrityError):
            User.objects.create_user(email="dup@example.com", password="pass2")

    def test_create_user_requires_email(self) -> None:
        with pytest.raises(ValueError, match="email address"):
            User.objects.create_user(email="", password="pass")

    def test_str_returns_email(self, user: User) -> None:
        assert str(user) == "alice@example.com"


@pytest.mark.django_db
class TestOrganizationModel:
    def test_create_organization(self) -> None:
        org = Organization.objects.create(name="Test Org", slug="test-org")
        assert isinstance(org.id, uuid.UUID)
        assert org.name == "Test Org"
        assert org.slug == "test-org"
        assert org.created_at is not None

    def test_slug_must_be_unique_globally(self, organization: Organization) -> None:
        with pytest.raises(IntegrityError):
            Organization.objects.create(name="Another Acme", slug=organization.slug)

    def test_str_returns_name(self, organization: Organization) -> None:
        assert str(organization) == "Acme Corp"


@pytest.mark.django_db
class TestMembershipModel:
    def test_create_owner_membership(self, user: User, organization: Organization) -> None:
        membership = Membership.objects.create(
            user=user,
            organization=organization,
            role=MembershipRole.OWNER,
        )
        assert isinstance(membership.id, uuid.UUID)
        assert membership.role == MembershipRole.OWNER

    def test_create_member_membership(self, other_user: User, organization: Organization) -> None:
        membership = Membership.objects.create(
            user=other_user,
            organization=organization,
            role=MembershipRole.MEMBER,
        )
        assert membership.role == MembershipRole.MEMBER

    def test_user_organization_membership_is_unique(
        self,
        user: User,
        organization: Organization,
        owner_membership: Membership,
    ) -> None:
        with pytest.raises(IntegrityError):
            Membership.objects.create(
                user=user,
                organization=organization,
                role=MembershipRole.MEMBER,
            )

    def test_user_can_belong_to_multiple_organizations(
        self,
        user: User,
        organization: Organization,
        other_organization: Organization,
    ) -> None:
        Membership.objects.create(user=user, organization=organization, role=MembershipRole.OWNER)
        Membership.objects.create(user=user, organization=other_organization, role=MembershipRole.MEMBER)
        assert user.memberships.count() == 2

    def test_default_role_is_member(self, other_user: User, organization: Organization) -> None:
        membership = Membership.objects.create(user=other_user, organization=organization)
        assert membership.role == MembershipRole.MEMBER

    def test_str_representation(self, owner_membership: Membership) -> None:
        assert "alice@example.com" in str(owner_membership)
        assert "Acme Corp" in str(owner_membership)
        assert "owner" in str(owner_membership)
