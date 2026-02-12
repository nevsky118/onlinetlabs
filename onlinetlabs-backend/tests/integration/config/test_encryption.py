import sys

import pytest

from app.config.encryption import decrypt_file, encrypt_file, main
from tests.report import autotests

pytestmark = [pytest.mark.integration, pytest.mark.config]


class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self, tmp_path):
        original = tmp_path / "test.env"
        original.write_text("SECRET=hello\nDB_HOST=localhost\n")
        password = "test-password-123"

        encrypted_path = encrypt_file(str(original), password)
        assert encrypted_path.endswith(".aes")

        decrypted_path = decrypt_file(encrypted_path, password)
        assert open(decrypted_path).read() == "SECRET=hello\nDB_HOST=localhost\n"

    def test_encrypt_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            encrypt_file("/nonexistent/file.env", "pass")

    def test_decrypt_non_aes_raises(self, tmp_path):
        f = tmp_path / "test.env"
        f.write_text("x")
        with pytest.raises(ValueError, match=".aes"):
            decrypt_file(str(f), "pass")

    @autotests.num("63")
    @autotests.external_id("c70e8966-1f5b-4c00-9683-b6a166d8fefa")
    @autotests.name("decrypt_file: отсутствующий файл вызывает FileNotFoundError")
    def test_decrypt_missing_file_raises(self):
        """Проверяет что decrypt_file с несуществующим .aes файлом вызывает FileNotFoundError."""

        # Act & Assert
        with autotests.step("Вызываем decrypt_file с несуществующим файлом"):
            with pytest.raises(FileNotFoundError):
                decrypt_file("/nonexistent/file.aes", "pass")


class TestEncryptionCLI:
    @autotests.num("64")
    @autotests.external_id("d3ea0149-bc51-4c83-b674-9d8bcb569427")
    @autotests.name("CLI: encrypt создаёт .aes файл")
    def test_cli_encrypt(self, tmp_path, monkeypatch):
        """Проверяет что CLI encrypt создаёт .aes файл."""

        # Arrange
        env_file = tmp_path / "cli-test.env"
        env_file.write_text("KEY=value\n")

        with autotests.step("Подменяем sys.argv для encrypt"):
            monkeypatch.setattr(
                sys, "argv", ["prog", "encrypt", str(env_file), "--password", "testpass"]
            )

        # Act
        with autotests.step("Вызываем main()"):
            main()

        # Assert
        with autotests.step("Проверяем что .aes файл создан"):
            aes_file = tmp_path / "cli-test.env.aes"
            assert aes_file.exists()

    @autotests.num("65")
    @autotests.external_id("f1e5b9fe-d581-4199-ace5-59f450e3f022")
    @autotests.name("CLI: decrypt восстанавливает содержимое")
    def test_cli_decrypt(self, tmp_path, monkeypatch):
        """Проверяет что CLI decrypt восстанавливает оригинальное содержимое."""

        # Arrange
        env_file = tmp_path / "cli-dec.env"
        original_content = "SECRET=hello\n"
        env_file.write_text(original_content)

        with autotests.step("Шифруем файл"):
            encrypted_path = encrypt_file(str(env_file), "testpass")

        with autotests.step("Удаляем оригинал"):
            env_file.unlink()

        with autotests.step("Подменяем sys.argv для decrypt"):
            monkeypatch.setattr(
                sys, "argv", ["prog", "decrypt", encrypted_path, "--password", "testpass"]
            )

        # Act
        with autotests.step("Вызываем main()"):
            main()

        # Assert
        with autotests.step("Проверяем что файл восстановлен"):
            assert env_file.read_text() == original_content

    @autotests.num("66")
    @autotests.external_id("52f95576-fbe8-4165-a2fd-ddabb32b01d7")
    @autotests.name("CLI: без пароля выходит с кодом 1")
    def test_cli_no_password_exits(self, tmp_path, monkeypatch):
        """Проверяет что CLI без пароля выходит с SystemExit(1)."""

        # Arrange
        monkeypatch.delenv("CONFIG_PASSWORD", raising=False)

        with autotests.step("Подменяем sys.argv без --password"):
            monkeypatch.setattr(
                sys, "argv", ["prog", "encrypt", str(tmp_path / "test.env")]
            )

        # Act & Assert
        with autotests.step("Вызываем main() без пароля"):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
