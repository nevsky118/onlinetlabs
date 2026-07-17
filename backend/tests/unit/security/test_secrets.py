import pytest
from cryptography.fernet import Fernet, InvalidToken
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from security.secrets import _cipher, decrypt_secret, encrypt_secret

pytestmark = [pytest.mark.unit]


class TestSecrets:
    @pytest.fixture(autouse=True)
    def clear_cipher_cache(self):
        # _cipher() lru_cached. Сбрасываем перед каждым тестом, чтобы
        # подмена ключа в env не игнорировалась.
        _cipher.cache_clear()
        yield
        _cipher.cache_clear()

    @autotest.num("740")
    @autotest.external_id("a1b2c3d4-7407-4001-aabb-ccddeeff0001")
    @autotest.name("Secrets: encrypt → decrypt round-trip")
    def test_a1b2c3d4_encrypt_decrypt_round_trip(self):
        with autotest.step("Шифруем известный plaintext"):
            plaintext = "super-secret-password-123"
            token = encrypt_secret(plaintext)

        with autotest.step("Расшифровываем обратно"):
            assert_equal(decrypt_secret(token), plaintext, "round-trip совпадает")

    @autotest.num("741")
    @autotest.external_id("b2c3d4e5-7407-4002-aabb-ccddeeff0002")
    @autotest.name("Secrets: испорченный токен → InvalidToken")
    def test_b2c3d4e5_corrupted_token_raises(self):
        with autotest.step("Шифруем и портим середину токена"):
            token = encrypt_secret("plain")
            corrupted = token[:5] + "XXXXX" + token[10:]

        with autotest.step("Расшифровка испорченного блока бросает InvalidToken"):
            with pytest.raises(InvalidToken):
                decrypt_secret(corrupted)

    @autotest.num("742")
    @autotest.external_id("c3d4e5f6-7407-4003-aabb-ccddeeff0003")
    @autotest.name("Secrets: расшифровка чужим ключом → InvalidToken")
    def test_c3d4e5f6_wrong_key_raises(self):
        with autotest.step("Шифруем под одним ключом"):
            other_key = Fernet.generate_key().decode()
            other_cipher = Fernet(other_key.encode())
            token = other_cipher.encrypt(b"plain").decode()

        with autotest.step("Пытаемся расшифровать дефолтным ключом приложения"):
            with pytest.raises(InvalidToken):
                decrypt_secret(token)
