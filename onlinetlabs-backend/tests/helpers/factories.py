"""Data builders with sensible defaults for backend tests."""

from typing import Any


def build_register_request(**overrides: Any) -> dict:
    defaults = {"email": "test@example.com", "password": "securepass123", "name": "Test User"}
    return defaults | overrides


def build_login_request(**overrides: Any) -> dict:
    defaults = {"email": "test@example.com", "password": "securepass123"}
    return defaults | overrides


def build_github_callback_request(**overrides: Any) -> dict:
    defaults = {
        "email": "gh@example.com",
        "name": "GitHub User",
        "image": "https://avatar.url",
        "provider_account_id": "12345",
    }
    return defaults | overrides


def build_exchange_request(**overrides: Any) -> dict:
    defaults = {"user_id": "user-123", "email": "test@example.com"}
    return defaults | overrides
