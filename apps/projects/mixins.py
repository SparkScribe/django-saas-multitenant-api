"""Organization queryset mixins for tenant-scoped views."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from django.db.models import QuerySet

if TYPE_CHECKING:
    from apps.projects.models import Project


class OrganizationQuerysetMixin:
    """Filter querysets to the active organization on the request."""

    def get_organization_id(self) -> uuid.UUID | None:
        return getattr(self.request, "organization_id", None)

    def filter_queryset_by_organization(self, queryset: QuerySet) -> QuerySet:
        organization_id = self.get_organization_id()
        if organization_id is None:
            return queryset.none()
        return queryset.filter(organization_id=organization_id)
