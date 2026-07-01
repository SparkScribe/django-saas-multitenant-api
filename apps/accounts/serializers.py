"""Account serializers."""

from django.db import transaction
from rest_framework import serializers

from apps.accounts.models import User
from apps.organizations.serializers import MembershipSerializer
from apps.organizations.services import create_organization_with_owner, generate_unique_slug


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    organization_name = serializers.CharField(required=False, allow_blank=False, max_length=255)
    organization_slug = serializers.SlugField(required=False, allow_blank=False, max_length=255)

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate(self, attrs: dict) -> dict:
        organization_name = attrs.get("organization_name")
        organization_slug = attrs.get("organization_slug")

        if organization_slug and not organization_name:
            raise serializers.ValidationError(
                {"organization_slug": "organization_name is required when providing a slug."}
            )

        if organization_name and not organization_slug:
            attrs["organization_slug"] = generate_unique_slug(organization_name)

        if organization_slug:
            from apps.organizations.models import Organization

            if Organization.objects.filter(slug=organization_slug).exists():
                raise serializers.ValidationError(
                    {"organization_slug": "An organization with this slug already exists."}
                )

        return attrs

    @transaction.atomic
    def create(self, validated_data: dict) -> User:
        organization_name = validated_data.pop("organization_name", None)
        organization_slug = validated_data.pop("organization_slug", None)
        password = validated_data.pop("password")

        user = User.objects.create_user(password=password, **validated_data)

        if organization_name:
            create_organization_with_owner(
                name=organization_name,
                slug=organization_slug,
                owner=user,
            )

        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "created_at")
        read_only_fields = fields


class UserMeSerializer(serializers.ModelSerializer):
    memberships = MembershipSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "created_at", "memberships")
        read_only_fields = fields

    def to_representation(self, instance: User) -> dict:
        instance = (
            User.objects.prefetch_related("memberships__organization")
            .get(pk=instance.pk)
        )
        return super().to_representation(instance)
