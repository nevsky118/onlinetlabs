# Модель конфигурации окружения для автотестов.

from typing import Dict, Optional

from pydantic import BaseModel, Field


class Account(BaseModel):
    """
    Учётные данные тестового пользователя.

    :param sub: Идентификатор пользователя (subject claim).
    :param email: Email пользователя.
    :param token: JWT-токен пользователя (генерируется при старте тестов).
    """

    sub: Optional[str] = Field(
        default=None,
        description="Идентификатор пользователя (subject claim).",
    )
    email: Optional[str] = Field(
        default=None,
        description="Email пользователя.",
    )
    token: Optional[str] = Field(
        default=None,
        description="JWT-токен пользователя (генерируется при старте тестов).",
    )


class ConfigModel(BaseModel):
    """
    Главная модель конфигурации окружения для автотестов.

    :param base_url: Базовый URL для обращения к тестируемому API.
    :param accounts: Словарь тестовых аккаунтов (по ключу — имя аккаунта).
    """

    base_url: str = Field(
        default="http://localhost:8000",
        description="Базовый URL для обращения к тестируемому API.",
    )
    gns3_base_url: str = Field(
        default="http://localhost:8101",
        description="Базовый URL gns3-service.",
    )
    gns3_lab_template_project_id: str = Field(
        default="",
        description="UUID шаблонного проекта GNS3 для тестов.",
    )
    accounts: Dict[str, Account] = Field(
        default={},
        description="Словарь тестовых аккаунтов (по ключу — имя аккаунта).",
    )
