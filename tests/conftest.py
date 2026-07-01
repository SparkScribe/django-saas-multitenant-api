"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Ensure migrations run before the test session."""
    with django_db_blocker.unblock():
        from django.core.management import call_command

        call_command("migrate", "--noinput")
