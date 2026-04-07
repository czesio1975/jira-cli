"""Client extension with convenience methods."""

from typing import Dict, Any

from jira_cli.pkg.jira.board import BoardOps
from jira_cli.pkg.jira.sprint import SprintOps
from jira_cli.pkg.jira.project import ProjectOps
from jira_cli.pkg.jira.issue import IssueOps
from jira_cli.pkg.jira.types import SearchResult, Issue


class ClientExtensions:
    """Mixin class with convenience methods."""

    def search_issues(self, jql: str, max_results: int = 100, start_at: int = 0) -> SearchResult:
        """Search for issues using JQL."""
        return IssueOps(self).search(jql, start_at=start_at, max_results=max_results, api_version=self.default_api_version)

    def get_issue(self, key: str) -> Issue:
        """Get issue by key."""
        return IssueOps(self).get(key, api_version=self.default_api_version)

    def get_boards(self, project_key: str) -> list:
        """Get boards for a project."""
        from jira_cli.pkg.jira.board import get_boards
        return get_boards(self, project_key)

    def get_sprints(self, board_id: int) -> list:
        """Get sprints for a board."""
        from jira_cli.pkg.jira.sprint import get_sprints_for_board
        return get_sprints_for_board(self, board_id)

    def get_projects(self) -> list:
        """Get all projects."""
        from jira_cli.pkg.jira.project import get_projects
        return get_projects(self)


# Apply extensions to Client
from jira_cli.pkg.jira.client import Client as BaseClient

BaseClient.search_issues = ClientExtensions.search_issues
BaseClient.get_issue = ClientExtensions.get_issue
BaseClient.get_boards = ClientExtensions.get_boards
BaseClient.get_sprints = ClientExtensions.get_sprints
BaseClient.get_projects = ClientExtensions.get_projects