"""Tenant organization context resolution tests."""

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework_simplejwt.tokens import AccessToken

from apps.organizations.context import (
    ORGANIZATION_INVALID_CODE,
    ORGANIZATION_REQUIRED_CODE,
    OrganizationContextError,
    resolve_organization_id,
)
from apps.organizations.models import Membership, MembershipRole


@pytest.mark.django_db
class TestResolveOrganizationId:
    def test_resolves_from_jwt_claim(
        self,
        user,
        organization,
        owner_membership,
    ) -> None:
        factory = APIRequestFactory()
        request = factory.get("/api/v1/projects/")
        token = AccessToken.for_user(user)
        token["organization_id"] = str(organization.id)
        force_authenticate(request, user=user, token=token)

        resolved = resolve_organization_id(request, user)
        assert resolved == organization.id

    def test_resolves_from_header_when_no_claim(
        self,
        user,
        organization,
        owner_membership,
    ) -> None:
        factory = APIRequestFactory()
        request = factory.get(
            "/api/v1/projects/",
            HTTP_X_ORGANIZATION_ID=str(organization.id),
        )
        force_authenticate(request, user=user)

        resolved = resolve_organization_id(request, user)
        assert resolved == organization.id

    def test_header_must_match_membership(
        self,
        user,
        other_organization,
    ) -> None:
        factory = APIRequestFactory()
        request = factory.get(
            "/api/v1/projects/",
            HTTP_X_ORGANIZATION_ID=str(other_organization.id),
        )
        force_authenticate(request, user=user)

        with pytest.raises(OrganizationContextError) as exc_info:
            resolve_organization_id(request, user)

        assert exc_info.value.get_codes() == ORGANIZATION_INVALID_CODE

    def test_missing_context_raises_organization_required(self, user) -> None:
        factory = APIRequestFactory()
        request = factory.get("/api/v1/projects/")
        force_authenticate(request, user=user)

        with pytest.raises(OrganizationContextError) as exc_info:
            resolve_organization_id(request, user)

        assert exc_info.value.get_codes() == ORGANIZATION_REQUIRED_CODE

    def test_conflicting_claim_and_header_raises_invalid(
        self,
        user,
        organization,
        other_organization,
        owner_membership,
    ) -> None:
        Membership.objects.create(
            user=user,
            organization=other_organization,
            role=MembershipRole.MEMBER,
        )
        factory = APIRequestFactory()
        request = factory.get(
            "/api/v1/projects/",
            HTTP_X_ORGANIZATION_ID=str(other_organization.id),
        )
        token = AccessToken.for_user(user)
        token["organization_id"] = str(organization.id)
        force_authenticate(request, user=user, token=token)

        with pytest.raises(OrganizationContextError) as exc_info:
            resolve_organization_id(request, user)

        assert exc_info.value.get_codes() == ORGANIZATION_INVALID_CODE

    def test_invalid_header_uuid_raises_required(self, user, owner_membership) -> None:
        factory = APIRequestFactory()
        request = factory.get(
            "/api/v1/projects/",
            HTTP_X_ORGANIZATION_ID="not-a-uuid",
        )
        force_authenticate(request, user=user)

        with pytest.raises(OrganizationContextError) as exc_info:
            resolve_organization_id(request, user)

        assert exc_info.value.get_codes() == ORGANIZATION_REQUIRED_CODE
