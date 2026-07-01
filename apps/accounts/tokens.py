"""JWT token customization with organization claims."""

from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Embed organization_id in the JWT when the user belongs to exactly one org."""

    @classmethod
    def get_token(cls, user: Any):
        token = super().get_token(user)
        organization_ids = list(
            user.memberships.values_list("organization_id", flat=True)
        )
        if len(organization_ids) == 1:
            token["organization_id"] = str(organization_ids[0])
        return token


@extend_schema(
    tags=["auth"],
    description=(
        "Obtain JWT access and refresh tokens. When the user belongs to exactly "
        "one organization, the access token includes an `organization_id` claim."
    ),
)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
