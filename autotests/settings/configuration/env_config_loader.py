# Configuration loader that reads from a .env file or from environment variables.

import os

from dotenv import dotenv_values

from autotests.settings.configuration.config_model import Account, ConfigModel


class EnvConfigLoader:
    """
    Loads variables from a .env file or from os.environ and builds a ConfigModel.
    """

    def load(self, env_path: str) -> ConfigModel:
        """
        Loads variables from a .env file and exports them into os.environ.

        :param env_path: Path to the .env file.
        :return: A ConfigModel object.
        """
        values = dotenv_values(env_path)
        for key, value in values.items():
            os.environ[key] = value
        return self._build(values)

    def load_from_environ(self) -> ConfigModel:
        """
        Loads the configuration from environment variables.

        :return: A ConfigModel object.
        """
        return self._build(dict(os.environ))

    @staticmethod
    def _build(values: dict) -> ConfigModel:
        """
        Builds a ConfigModel from a dictionary of variables.

        :param values: Dictionary of environment variables.
        :return: A ConfigModel object.
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
