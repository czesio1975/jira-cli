"""JIRA Issue delete operations.

Converted from pkg/jira/delete.go
"""

from jira_cli.pkg.jira.client import Client


class DeleteOps:
    """Issue delete operations."""

    def __init__(self, client: Client) -> None:
        self.client = client

    def delete_issue(self, key: str) -> None:
        """Delete an issue."""
        self.client.delete(f"/issue/{key}")

    def delete_issue_with_subtasks(self, key: str) -> None:
        """Delete an issue and its subtasks."""
        self.client.delete(f"/issue/{key}", params={"deleteSubtasks": "true"})


def delete_issue(client: Client, key: str) -> None:
    """Delete an issue."""
    DeleteOps(client).delete_issue(key)