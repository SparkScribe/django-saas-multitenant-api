"""Project permissions."""

from __future__ import annotations

import logging

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.organizations.context import OrganizationContextError, resolve_organization_id

logger = logging.getLogger(__name__)


class IsOrganizationMember(BasePermission):
    """
    Require a resolved organization context and active membership.

    Attaches ``organization_id`` to the request for downstream queryset filtering.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False

        try:
            request.organization_id = resolve_organization_id(request, user)
        except OrganizationContextError as exc:
            logger.debug(
                "Permission denied for user %s: %s (code=%s)",
                user.pk,
                exc.detail,
                exc.get_codes(),
            )
            raise

        return True
