"""JIRA Issue edit operations.

Converted from pkg/jira/edit.go
"""

from typing import Dict, List, Any, Optional

from jira_cli.pkg.jira.client import Client


class EditOps:
    """Issue edit operations."""

    def __init__(self, client: Client) -> None:
        self.client = client

    def edit(
        self,
        key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        components: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        api_version: str = "v3",
    ) -> None:
        """Edit an existing issue."""
        fields: Dict[str, Any] = {}

        if summary:
            fields["summary"] = summary

        if description is not None:
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

        if priority:
            fields["priority"] = {"name": priority}

        if assignee is not None:
            if api_version == "v3":
                fields["assignee"] = {"accountId": assignee} if assignee else None
            else:
                fields["assignee"] = {"name": assignee} if assignee else None

        if labels is not None:
            fields["labels"] = labels

        if components is not None:
            fields["components"] = [{"name": c} for c in components]

        if custom_fields:
            fields.update(custom_fields)

        body = {"fields": fields}
        self.client.put(f"/issue/{key}", body, api_version=api_version)

    def edit_v2(self, key: str, **kwargs: Any) -> None:
        """Edit issue using v2 API."""
        self.edit(key, api_version="v2", **kwargs)


def edit_issue(client: Client, key: str, **kwargs: Any) -> None:
    """Edit an issue."""
    EditOps(client).edit(key, **kwargs)