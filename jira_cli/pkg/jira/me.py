"""JIRA User info operations.

Converted from pkg/jira/me.go
"""

from typing import Dict, Optional

from pydantic import AliasChoices, BaseModel, Field as PydanticField

from jira_cli.pkg.jira.client import Client
from jira_cli.pkg.jira.types import User


class UserInfo(BaseModel):
    """Extended user info."""

    account_id: str = PydanticField(
        default="",
        validation_alias=AliasChoices("accountId", "account_id", "key"),
    )
    email: str = PydanticField(
        default="",
        validation_alias=AliasChoices("emailAddress", "email"),
    )
    display_name: str = PydanticField(
        default="",
        validation_alias=AliasChoices("displayName", "display_name"),
    )
    active: bool = True
    timezone: str = PydanticField(
        default="",
        validation_alias=AliasChoices("timeZone", "timezone"),
    )
    locale: str = ""

    @property
    def login(self) -> str:
        """Get login identifier."""
        return self.email


class MeOps:
    """User info operations."""

    def __init__(self, client: Client) -> None:
        self.client = client

    def get_me(self, api_version: Optional[str] = None) -> UserInfo:
        """Get current user info."""
        version = api_version or self.client.default_api_version
        response = self.client.get("/myself", api_version=version)
        return UserInfo.model_validate(response)


def get_current_user(client: Client) -> UserInfo:
    """Get current user."""
    return MeOps(client).get_me()