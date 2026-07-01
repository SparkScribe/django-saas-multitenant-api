"""Organization business logic."""

from django.db import transaction
from django.utils.text import slugify

from apps.accounts.models import User
from apps.organizations.models import Membership, MembershipRole, Organization


def generate_unique_slug(name: str) -> str:
    """Return a globally unique slug derived from an organization name."""
    base_slug = slugify(name)
    if not base_slug:
        raise ValueError("Organization name must produce a valid slug.")

    slug = base_slug
    counter = 1
    while Organization.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


@transaction.atomic
def create_organization_with_owner(*, name: str, slug: str, owner: User) -> Organization:
    """Create an organization and assign the given user as owner."""
    organization = Organization.objects.create(name=name, slug=slug)
    Membership.objects.create(
        user=owner,
        organization=organization,
        role=MembershipRole.OWNER,
    )
    return organization
