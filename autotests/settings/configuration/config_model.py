# Environment configuration model for the autotests.

from typing import Dict, Optional

from pydantic import BaseModel, Field


class Account(BaseModel):
    """
    Credentials of a test user.

    :param sub: User identifier (subject claim).
    :param email: User email.
    :param token: User JWT token (generated when the tests start).
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
    Main environment configuration model for the autotests.

    :param base_url: Base URL used to reach the API under test.
    :param accounts: Dictionary of test accounts, keyed by account name.
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
    gns3_url: str = Field(
        default="http://localhost:3080",
        description="URL GNS3 сервера.",
    )
    gns3_mcp_url: str = Field(
        default="http://localhost:8100",
        description="URL GNS3 MCP сервера.",
    )
    gns3_admin_user: str = Field(
        default="admin",
        description="Логин администратора GNS3.",
    )
    gns3_admin_password: str = Field(
        default="admin",
        description="Пароль администратора GNS3.",
    )
    accounts: Dict[str, Account] = Field(
        default={},
        description="Словарь тестовых аккаунтов (по ключу — имя аккаунта).",
    )
