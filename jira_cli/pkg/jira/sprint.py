"""JIRA Sprint operations.

Converted from pkg/jira/sprint.go
"""

from typing import Dict, Optional, List

from pydantic import BaseModel

from jira_cli.pkg.jira.client import Client
from jira_cli.pkg.jira.types import Sprint


class SprintSearchResult(BaseModel):
    """Sprint search result."""

    start_at: int = 0
    max_results: int = 50
    total: int = 0
    is_last: bool = True
    values: list[Sprint] = []

    @property
    def sprints(self) -> list[Sprint]:
        return self.values


class SprintOps:
    """Sprint operations."""

    def __init__(self, client: Client) -> None:
        self.client = client

    def list(
        self,
        board_id: int,
        state: Optional[str] = None,
        start_at: int = 0,
        max_results: int = 50,
    ) -> SprintSearchResult:
        """List sprints for a board."""
        params = {
            "startAt": start_at,
            "maxResults": max_results,
        }
        if state:
            params["state"] = state

        response = self.client.get_v1(f"/board/{board_id}/sprint", params=params)
        return SprintSearchResult.model_validate(response)

    def get(self, sprint_id: int) -> Sprint:
        """Get sprint by ID."""
        response = self.client.get_v1(f"/sprint/{sprint_id}")
        return Sprint.model_validate(response)

    def create(self, board_id: int, name: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Sprint:
        """Create a new sprint."""
        body: dict = {"name": name, "originBoardId": board_id}
        if start_date:
            body["startDate"] = start_date
        if end_date:
            body["endDate"] = end_date

        response = self.client.post_v1("/sprint", body)
        return Sprint.model_validate(response)

    def update(
        self,
        sprint_id: int,
        name: Optional[str] = None,
        state: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Sprint:
        """Update sprint."""
        # The Jira Agile API requires name and state in every update,
        # and start/end dates when transitioning to active
        current = self.get(sprint_id)
        body: dict = {
            "name": name or current.name,
            "state": state or current.status,
        }
        sd = start_date or current.start_date
        ed = end_date or current.end_date
        if sd:
            body["startDate"] = sd
        if ed:
            body["endDate"] = ed

        response = self.client.put_v1(f"/sprint/{sprint_id}", body)
        return Sprint.model_validate(response)

    def start(self, sprint_id: int) -> Sprint:
        """Start a sprint."""
        return self.update(sprint_id, state="active")

    def close(self, sprint_id: int) -> Sprint:
        """Close a sprint."""
        return self.update(sprint_id, state="closed")

    def list_for_boards(self, board_ids: List[int], state: Optional[str] = None) -> List[Sprint]:
        """List sprints for multiple boards (sync version)."""
        results: list[Sprint] = []
        for board_id in board_ids:
            result = self.list(board_id, state=state)
            results.extend(result.sprints)
        return results


def get_sprints_for_board(client: Client, board_id: int) -> List[Sprint]:
    """Get sprints for a board."""
    ops = SprintOps(client)
    result = ops.list(board_id)
    return result.sprints