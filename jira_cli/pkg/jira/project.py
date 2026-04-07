"""JIRA Project operations.

Converted from pkg/jira/project.go
"""

from typing import Dict, List, Optional

from jira_cli.pkg.jira.client import Client
from jira_cli.pkg.jira.types import Project, ProjectVersion


class ProjectOps:
    """Project operations."""

    def __init__(self, client: Client) -> None:
        self.client = client

    def list(self) -> List[Project]:
        """List all projects."""
        response = self.client.get_v2("/project")
        return [Project.model_validate(p) for p in response]

    def get(self, project_key: str) -> Project:
        """Get project by key."""
        response = self.client.get_v2(f"/project/{project_key}")
        return Project.model_validate(response)

    def get_versions(self, project_key: str) -> List[ProjectVersion]:
        """Get project versions/releases."""
        response = self.client.get_v2(f"/project/{project_key}/versions")
        return [ProjectVersion.model_validate(v) for v in response]


def get_projects(client: Client) -> List[Project]:
    """Get all projects."""
    return ProjectOps(client).list()