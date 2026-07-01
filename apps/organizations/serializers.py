"""Organization serializers."""

from rest_framework import serializers

from apps.organizations.models import Membership, Organization
from apps.organizations.services import create_organization_with_owner, generate_unique_slug


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "slug", "created_at")
        read_only_fields = ("id", "created_at")


class OrganizationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("name", "slug")

    def validate_slug(self, value: str) -> str:
        if Organization.objects.filter(slug=value).exists():
            raise serializers.ValidationError("An organization with this slug already exists.")
        return value

    def validate(self, attrs: dict) -> dict:
        if not attrs.get("slug"):
            attrs["slug"] = generate_unique_slug(attrs["name"])
        return attrs

    def create(self, validated_data: dict) -> Organization:
        request = self.context["request"]
        return create_organization_with_owner(
            name=validated_data["name"],
            slug=validated_data["slug"],
            owner=request.user,
        )


class MembershipSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ("id", "organization", "role", "created_at")
        read_only_fields = fields
