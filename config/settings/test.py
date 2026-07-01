"""Test settings — uses PostgreSQL with a dedicated test database."""

from .base import *  # noqa: F403

DEBUG = False

DATABASES["default"]["TEST"] = {  # noqa: F405
    "NAME": "test_django_saas_multitenant",
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
