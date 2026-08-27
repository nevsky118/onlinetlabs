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
        description="User identifier (subject claim).",
    )
    email: Optional[str] = Field(
        default=None,
        description="User email.",
    )
    token: Optional[str] = Field(
        default=None,
        description="User JWT token (generated when the tests start).",
    )


class ConfigModel(BaseModel):
    """
    Main environment configuration model for the autotests.

    :param base_url: Base URL used to reach the API under test.
    :param accounts: Dictionary of test accounts, keyed by account name.
    """

    base_url: str = Field(
        default="http://localhost:8000",
        description="Base URL used to reach the API under test.",
    )
    gns3_base_url: str = Field(
        default="http://localhost:8101",
        description="Base URL of gns3-service.",
    )
    gns3_lab_template_project_id: str = Field(
        default="",
        description="UUID of the GNS3 template project for the tests.",
    )
    gns3_url: str = Field(
        default="http://localhost:3080",
        description="GNS3 server URL.",
    )
    gns3_mcp_url: str = Field(
        default="http://localhost:8100",
        description="GNS3 MCP server URL.",
    )
    gns3_admin_user: str = Field(
        default="admin",
        description="GNS3 admin login.",
    )
    gns3_admin_password: str = Field(
        default="admin",
        description="GNS3 admin password.",
    )
    accounts: Dict[str, Account] = Field(
        default={},
        description="Dictionary of test accounts, keyed by account name.",
    )
