"""Shared OpenAPI schema helpers."""

from drf_spectacular.utils import OpenApiParameter

ORGANIZATION_HEADER = OpenApiParameter(
    name="X-Organization-Id",
    type=str,
    location=OpenApiParameter.HEADER,
    required=False,
    description=(
        "UUID of the active organization. Required when the authenticated user "
        "belongs to multiple organizations and the JWT access token has no "
        "`organization_id` claim."
    ),
)
