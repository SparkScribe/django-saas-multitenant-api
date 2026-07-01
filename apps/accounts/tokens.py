"""JWT token customization with organization claims."""

from typing import Any

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


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
