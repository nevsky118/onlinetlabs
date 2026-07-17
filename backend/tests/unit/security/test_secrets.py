import pytest
from cryptography.fernet import Fernet, InvalidToken
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

from security.secrets import _cipher, decrypt_secret, encrypt_secret

pytestmark = [pytest.mark.unit]


class TestSecrets:
    @pytest.fixture(autouse=True)
    def clear_cipher_cache(self):
        # _cipher() lru_cached. Reset before each test so that
        # swapping the key in env isn't ignored.
        _cipher.cache_clear()
        yield
        _cipher.cache_clear()

    @autotest.num("740")
    @autotest.external_id("390a784d-d6be-4f32-99fc-3f0224648829")
    @autotest.name("Secrets: encrypt → decrypt round-trip")
    def test_390a784d_encrypt_decrypt_round_trip(self):
        with autotest.step("Шифруем известный plaintext"):
            plaintext = "super-secret-password-123"
            token = encrypt_secret(plaintext)

        with autotest.step("Расшифровываем обратно"):
            assert_equal(decrypt_secret(token), plaintext, "round-trip совпадает")

    @autotest.num("741")
    @autotest.external_id("01ebaa5c-008a-4abf-acf5-1e5802fceb72")
    @autotest.name("Secrets: испорченный токен → InvalidToken")
    def test_01ebaa5c_corrupted_token_raises(self):
        with autotest.step("Шифруем и портим середину токена"):
            token = encrypt_secret("plain")
            corrupted = token[:5] + "XXXXX" + token[10:]

        with autotest.step("Расшифровка испорченного блока бросает InvalidToken"):
            with pytest.raises(InvalidToken):
                decrypt_secret(corrupted)

    @autotest.num("742")
    @autotest.external_id("8d4d5f16-a427-4b9f-82eb-2e6d7e36a12c")
    @autotest.name("Secrets: расшифровка чужим ключом → InvalidToken")
    def test_8d4d5f16_wrong_key_raises(self):
        with autotest.step("Шифруем под одним ключом"):
            other_key = Fernet.generate_key().decode()
            other_cipher = Fernet(other_key.encode())
            token = other_cipher.encrypt(b"plain").decode()

        with autotest.step("Пытаемся расшифровать дефолтным ключом приложения"):
            with pytest.raises(InvalidToken):
                decrypt_secret(token)
