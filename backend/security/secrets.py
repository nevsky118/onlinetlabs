"""Fernet wrapper for encrypting the GNS3 password and JWT before writing to the DB."""

from functools import lru_cache

from cryptography.fernet import Fernet

from config import settings


@lru_cache(maxsize=1)
def _cipher() -> Fernet:
    """Creates and caches a Fernet instance with the encryption key from settings."""
    return Fernet(settings.security.cred_encryption_key.encode())


def encrypt_secret(plaintext: str) -> str:
    """Encrypts a string, returns a base64 token."""
    return _cipher().encrypt(plaintext.encode()).decode()


def decrypt_secret(token: str) -> str:
    """Decrypts a base64 token back into the original string."""
    return _cipher().decrypt(token.encode()).decode()
