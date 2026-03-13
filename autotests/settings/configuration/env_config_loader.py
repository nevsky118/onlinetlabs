# Загрузчик конфигурации из .env-файла или переменных окружения.

import os

from dotenv import dotenv_values

from autotests.settings.configuration.config_model import Account, ConfigModel


class EnvConfigLoader:
    """
    Загружает переменные из .env-файла или os.environ и формирует ConfigModel.
    """

    def load(self, env_path: str) -> ConfigModel:
        """
        Загружает переменные из .env-файла и экспортирует в os.environ.

        :param env_path: Путь к .env-файлу.
        :return: Объект ConfigModel.
        """
        values = dotenv_values(env_path)
        for key, value in values.items():
            os.environ[key] = value
        return self._build(values)

    def load_from_environ(self) -> ConfigModel:
        """
        Загружает конфигурацию из переменных окружения.

        :return: Объект ConfigModel.
        """
        return self._build(dict(os.environ))

    @staticmethod
    def _build(values: dict) -> ConfigModel:
        """
        Собирает ConfigModel из словаря переменных.

        :param values: Словарь с переменными окружения.
        :return: Объект ConfigModel.
        """
        accounts = {
            "ANON_ACCOUNT": Account(
                sub=values.get("ANON_ACCOUNT__SUB", "anon_test_user_001"),
                email=values.get("ANON_ACCOUNT__EMAIL", "anon@test.local"),
            ),
            "REGISTERED_ACCOUNT": Account(
                sub=values.get("REGISTERED_ACCOUNT__SUB", "registered_user_001"),
                email=values.get("REGISTERED_ACCOUNT__EMAIL", "user@test.local"),
            ),
        }

        return ConfigModel(
            base_url=values.get("BASE_URL", "http://localhost:8000"),
            gns3_base_url=values.get("GNS3_BASE_URL", "http://localhost:8101"),
            gns3_lab_template_project_id=values.get("GNS3_LAB_TEMPLATE_PROJECT_ID", ""),
            accounts=accounts,
        )
