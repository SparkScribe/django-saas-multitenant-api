"""Tenant organization context resolution."""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from django.http import HttpRequest
from rest_framework.exceptions import PermissionDenied

from apps.organizations.models import Membership

if TYPE_CHECKING:
    from apps.accounts.models import User

logger = logging.getLogger(__name__)

ORGANIZATION_HEADER = "HTTP_X_ORGANIZATION_ID"
ORGANIZATION_REQUIRED_CODE = "organization_required"
ORGANIZATION_INVALID_CODE = "organization_invalid"


class OrganizationContextError(PermissionDenied):
    """Raised when tenant organization context cannot be resolved."""

    default_detail = "Organization context is required."
    default_code = ORGANIZATION_REQUIRED_CODE


def _parse_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return None


def _get_request_token(request: HttpRequest):
    """Return the validated JWT token attached to the request, if any."""
    token = getattr(request, "auth", None)
    if token is not None:
        return token
    return getattr(request, "_force_auth_token", None)


def get_organization_id_from_token(request: HttpRequest) -> uuid.UUID | None:
    """Extract organization_id claim from the validated JWT, if present."""
    token = _get_request_token(request)
    if token is None:
        return None

    claim = token.get("organization_id")
    if claim is None:
        return None

    return _parse_uuid(claim)


def get_organization_id_from_header(request: HttpRequest) -> uuid.UUID | None:
    """Extract organization ID from the X-Organization-Id header."""
    header_value = request.META.get(ORGANIZATION_HEADER)
    if not header_value:
        return None
    return _parse_uuid(header_value)


def resolve_organization_id(request: HttpRequest, user: User) -> uuid.UUID:
    """
    Resolve the active organization for a request.

    Precedence:
    1. JWT ``organization_id`` claim
    2. ``X-Organization-Id`` header (must match a user membership)
    """
    token_org_id = get_organization_id_from_token(request)
    header_org_id = get_organization_id_from_header(request)

    if token_org_id and header_org_id and token_org_id != header_org_id:
        logger.debug(
            "Organization context denied: JWT claim %s conflicts with header %s for user %s",
            token_org_id,
            header_org_id,
            user.pk,
        )
        raise OrganizationContextError(
            detail="Organization header conflicts with token claim.",
            code=ORGANIZATION_INVALID_CODE,
        )

    organization_id = token_org_id or header_org_id
    if organization_id is None:
        logger.debug("Organization context denied: missing context for user %s", user.pk)
        raise OrganizationContextError(
            detail="Organization context is required.",
            code=ORGANIZATION_REQUIRED_CODE,
        )

    is_member = Membership.objects.filter(
        user=user,
        organization_id=organization_id,
    ).exists()
    if not is_member:
        logger.debug(
            "Organization context denied: user %s is not a member of org %s",
            user.pk,
            organization_id,
        )
        raise OrganizationContextError(
            detail="You are not a member of this organization.",
            code=ORGANIZATION_INVALID_CODE,
        )

    return organization_id
