"""JIRA API module."""

from jira_cli.pkg.jira.types import (
    AuthType,
    Board,
    Epic,
    Field,
    Issue,
    IssueFields,
    IssueLinkType,
    IssueType,
    IssueTypeField,
    MTLSConfig,
    Project,
    ProjectVersion,
    SearchResult,
    Sprint,
    Transition,
    User,
)
from jira_cli.pkg.jira.client import Client

# Import extensions to apply methods to Client
import jira_cli.pkg.jira.client_ext  # noqa: F401

__all__ = [
    "AuthType",
    "Board",
    "Client",
    "Epic",
    "Field",
    "Issue",
    "IssueFields",
    "IssueLinkType",
    "IssueType",
    "IssueTypeField",
    "MTLSConfig",
    "Project",
    "ProjectVersion",
    "SearchResult",
    "Sprint",
    "Transition",
    "User",
]