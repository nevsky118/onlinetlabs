"""Fernet-обёртка для шифрования GNS3-пароля и JWT перед записью в БД."""

from functools import lru_cache

from cryptography.fernet import Fernet

from config import settings


@lru_cache(maxsize=1)
def _cipher() -> Fernet:
    """Создаёт и кеширует Fernet с ключом шифрования из настроек."""
    return Fernet(settings.security.cred_encryption_key.encode())


def encrypt_secret(plaintext: str) -> str:
    """Зашифровать строку, вернуть base64-токен."""
    return _cipher().encrypt(plaintext.encode()).decode()


def decrypt_secret(token: str) -> str:
    """Расшифровать base64-токен в исходную строку."""
    return _cipher().decrypt(token.encode()).decode()
