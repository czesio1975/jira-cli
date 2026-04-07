"""JIRA Issue creation operations.

Converted from pkg/jira/create.go
"""

from typing import Dict, List, Any, Optional

from pydantic import BaseModel

from jira_cli.pkg.jira.client import Client
from jira_cli.pkg.jira.types import Issue


class CreateMetaRequest(BaseModel):
    """Create metadata request."""

    projects: str
    expand: str = "projects.issuetypes.fields"


class CreateMetaProject(BaseModel):
    """Create metadata project."""

    id: str
    key: str
    name: str
    issue_types: List[Dict[str, Any]] = []


class CreateMetaResponse(BaseModel):
    """Create metadata response."""

    projects: List[CreateMetaProject] = []


class CreateOps:
    """Issue creation operations."""

    def __init__(self, client: Client) -> None:
        self.client = client

    def get_create_meta(
        self,
        project_key: str,
        expand: str = "projects.issuetypes.fields",
    ) -> CreateMetaResponse:
        """Get create metadata for a project."""
        params = {"projectKeys": project_key, "expand": expand}
        response = self.client.get_v2("/issue/createmeta", params=params)
        return CreateMetaResponse.model_validate(response)

    def create(
        self,
        project_key: str,
        summary: str,
        issue_type: str,
        description: Optional[str] = None,
        parent: Optional[str] = None,
        assignee: Optional[str] = None,
        priority: Optional[str] = None,
        labels: Optional[List[str]] = None,
        components: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        api_version: str = "v3",
    ) -> Dict[str, str]:
        """Create a new issue."""
        fields: Dict[str, Any] = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }

        if description:
            if api_version == "v3":
                # ADF format for v3
                fields["description"] = {
                    "version": 1,
                    "type": "doc",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}],
                        }
                    ],
                }
            else:
                fields["description"] = description

        if parent:
            fields["parent"] = {"key": parent}
        if assignee:
            if api_version == "v3":
                fields["assignee"] = {"accountId": assignee}
            else:
                fields["assignee"] = {"name": assignee}
        if priority:
            fields["priority"] = {"name": priority}
        if labels:
            fields["labels"] = labels
        if components:
            fields["components"] = [{"name": c} for c in components]
        if custom_fields:
            fields.update(custom_fields)

        body = {"fields": fields}

        if api_version == "v2":
            return self.client.post_v2("/issue", body)
        return self.client.post("/issue", body)

    def create_v2(
        self,
        project_key: str,
        summary: str,
        issue_type: str,
        description: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, str]:
        """Create issue using v2 API."""
        return self.create(
            project_key=project_key,
            summary=summary,
            issue_type=issue_type,
            description=description,
            api_version="v2",
            **kwargs,
        )


def create_issue(client: Client, project_key: str, summary: str, issue_type: str) -> Dict[str, str]:
    """Create a new issue."""
    return CreateOps(client).create(project_key, summary, issue_type)