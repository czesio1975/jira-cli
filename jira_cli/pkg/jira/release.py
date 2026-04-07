"""JIRA Release/Version operations.

Converted from pkg/jira/release.go
"""

from typing import Dict, List, Optional

from pydantic import BaseModel

from jira_cli.pkg.jira.client import Client
from jira_cli.pkg.jira.types import ProjectVersion


class ReleaseOps:
    """Release/Version operations."""

    def __init__(self, client: Client) -> None:
        self.client = client

    def list(self, project_key: str) -> List[ProjectVersion]:
        """List versions for a project."""
        response = self.client.get_v2(f"/project/{project_key}/versions")
        return [ProjectVersion.model_validate(v) for v in response]

    def create(
        self,
        project_key: str,
        name: str,
        description: Optional[str] = None,
        released: bool = False,
        release_date: Optional[str] = None,
    ) -> ProjectVersion:
        """Create a new version."""
        from jira_cli.pkg.jira.project import ProjectOps

        # Resolve project key to numeric ID (required by Jira Server/Local)
        project = ProjectOps(self.client).get(project_key)
        body: dict = {
            "name": name,
            "projectId": int(project.id),
            "released": released,
        }
        if description:
            body["description"] = description
        if release_date:
            body["releaseDate"] = release_date

        response = self.client.post_v2("/version", body)
        return ProjectVersion.model_validate(response)

    def release(self, version_id: str, release_date: Optional[str] = None) -> ProjectVersion:
        """Release a version."""
        body: dict = {"released": True}
        if release_date:
            body["releaseDate"] = release_date

        response = self.client.put_v2(f"/version/{version_id}", body)
        return ProjectVersion.model_validate(response)


def get_versions(client: Client, project_key: str) -> List[ProjectVersion]:
    """Get versions for a project."""
    return ReleaseOps(client).list(project_key)