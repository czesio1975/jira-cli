"""JIRA Issue operations.

Converted from pkg/jira/issue.go
"""

from typing import Dict, List, Any, Optional

from jira_cli.pkg.jira.client import Client, UnexpectedResponseError
from jira_cli.pkg.jira.types import (
    Issue,
    SearchResult,
    Transition,
    IssueLinkType,
    Field,
    ASSIGNEE_NONE,
    ASSIGNEE_DEFAULT,
)


class IssueOps:
    """Issue operations."""

    def __init__(self, client: Client) -> None:
        self.client = client

    def get(self, key: str, api_version: str = "v3") -> Issue:
        """Get issue by key."""
        path = f"/issue/{key}"
        response = self.client.get(path, api_version=api_version)
        return Issue.model_validate(response)

    def get_v2(self, key: str) -> Issue:
        """Get issue using v2 API."""
        return self.get(key, api_version="v2")

    def get_raw(self, key: str, api_version: str = "v3") -> str:
        """Get raw issue response."""
        import json
        path = f"/issue/{key}"
        response = self.client.get(path, api_version=api_version)
        return json.dumps(response)

    def search(
        self,
        jql: str,
        start_at: int = 0,
        max_results: int = 100,
        api_version: str = "v3",
    ) -> SearchResult:
        """Search for issues using JQL."""
        path = "/search"
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
        }
        response = self.client.get(path, api_version=api_version, params=params)
        return SearchResult.model_validate(response)

    def search_v2(self, jql: str, start_at: int = 0, max_results: int = 100) -> SearchResult:
        """Search using v2 API."""
        return self.search(jql, start_at, max_results, api_version="v2")

    def assign(self, key: str, assignee: str, api_version: str = "v3") -> None:
        """Assign issue to a user."""
        path = f"/issue/{key}/assignee"

        # Handle special assignee values
        account_id: Optional[str]
        if assignee == ASSIGNEE_NONE:
            account_id = "-1"
        elif assignee == ASSIGNEE_DEFAULT:
            account_id = None
        else:
            account_id = assignee

        if api_version == "v2":
            body = {"name": account_id}
        else:
            body = {"accountId": account_id}

        self.client.put(path, body, api_version=api_version)

    def assign_v2(self, key: str, assignee: str) -> None:
        """Assign issue using v2 API."""
        self.assign(key, assignee, api_version="v2")

    def get_transitions(self, key: str, api_version: str = "v3") -> List[Transition]:
        """Get available transitions for an issue."""
        path = f"/issue/{key}/transitions"
        response = self.client.get(path, api_version=api_version)
        transitions = response.get("transitions", [])
        return [Transition.model_validate(t) for t in transitions]

    def get_transitions_v2(self, key: str) -> List[Transition]:
        """Get transitions using v2 API."""
        return self.get_transitions(key, api_version="v2")

    def transition(self, key: str, transition_id: str, fields: Optional[Dict[str, Any]] = None, api_version: str = "v3") -> None:
        """Transition issue to a new status."""
        path = f"/issue/{key}/transitions"
        body: Dict[str, Any] = {"transition": {"id": transition_id}}
        if fields:
            body["fields"] = fields
        self.client.post(path, body, api_version=api_version)

    def add_comment(self, key: str, comment: str, internal: bool = False) -> None:
        """Add comment to an issue."""
        from jira_cli.pkg.jira.markdown import to_jira_md

        path = f"/issue/{key}/comment"
        body: Dict[str, Any] = {
            "body": to_jira_md(comment),
            "properties": [{"key": "sd.public.comment", "value": {"internal": internal}}],
        }
        self.client.post_v2(path, body)

    def get_link_types(self) -> List[IssueLinkType]:
        """Get all issue link types."""
        response = self.client.get_v2("/issueLinkType")
        link_types = response.get("issueLinkTypes", [])
        return [IssueLinkType.model_validate(lt) for lt in link_types]

    def link(self, inward_issue: str, outward_issue: str, link_type: str) -> None:
        """Link two issues."""
        body = {
            "inwardIssue": {"key": inward_issue},
            "outwardIssue": {"key": outward_issue},
            "type": {"name": link_type},
        }
        self.client.post_v2("/issueLink", body)

    def unlink(self, link_id: str) -> None:
        """Unlink issues by link ID."""
        self.client.delete(f"/issueLink/{link_id}")

    def get_link_id(self, issue_key: str, other_issue: str) -> Optional[str]:
        """Get link ID between two issues."""
        issue = self.get_v2(issue_key)
        for link in issue.fields.issue_links:
            if link.get("inwardIssue", {}).get("key") == other_issue:
                return link.get("id")
            if link.get("outwardIssue", {}).get("key") == other_issue:
                return link.get("id")
        return None

    def watch(self, key: str, watcher: str, api_version: str = "v3") -> None:
        """Add watcher to an issue."""
        path = f"/issue/{key}/watchers"
        # The watchers API expects a raw JSON string, not a JSON object
        self.client.post_raw(path, f'"{watcher}"', api_version=api_version)

    def watch_v2(self, key: str, watcher: str) -> None:
        """Add watcher using v2 API."""
        self.watch(key, watcher, api_version="v2")

    def get_fields(self) -> List[Field]:
        """Get all fields configured for Jira instance."""
        response = self.client.get_v2("/field")
        return [Field.model_validate(f) for f in response]

    def remote_link(self, issue_id: str, title: str, url: str) -> None:
        """Add remote link to an issue."""
        body = {"object": {"title": title, "url": url}}
        self.client.post_v2(f"/issue/{issue_id}/remotelink", body)

    def add_worklog(
        self,
        key: str,
        time_spent: str,
        comment: str = "",
        started: str = "",
        new_estimate: str = "",
    ) -> None:
        """Add worklog to an issue."""
        from jira_cli.pkg.jira.markdown import to_jira_md

        body: Dict[str, Any] = {
            "timeSpent": time_spent,
            "comment": to_jira_md(comment),
        }
        if started:
            body["started"] = started

        path = f"/issue/{key}/worklog"
        if new_estimate:
            path += f"?adjustEstimate=new&newEstimate={new_estimate}"

        self.client.post_v2(path, body)


# Standalone functions for convenience
def get_issue(client: Client, key: str) -> Issue:
    """Get issue by key."""
    return IssueOps(client).get(key)


def search_issues(client: Client, jql: str, max_results: int = 100) -> SearchResult:
    """Search for issues."""
    return IssueOps(client).search(jql, max_results=max_results)