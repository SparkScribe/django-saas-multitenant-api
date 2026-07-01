"""Organization serializers."""

from rest_framework import serializers

from apps.organizations.models import Membership, Organization


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "slug", "created_at")
        read_only_fields = fields


class MembershipSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ("id", "organization", "role", "created_at")
        read_only_fields = fields
