"""JIRA Board operations.

Converted from pkg/jira/board.go
"""

from typing import Dict, List, Optional

from pydantic import BaseModel

from jira_cli.pkg.jira.client import Client
from jira_cli.pkg.jira.types import Board


class BoardSearchResult(BaseModel):
    """Board search result."""

    start_at: int = 0
    max_results: int = 50
    total: int = 0
    is_last: bool = True
    values: List[Board] = []

    @property
    def boards(self) -> List[Board]:
        return self.values


class BoardOps:
    """Board operations."""

    def __init__(self, client: Client) -> None:
        self.client = client

    def list(
        self,
        project_key: Optional[str] = None,
        board_name: Optional[str] = None,
        board_type: Optional[str] = None,
        start_at: int = 0,
        max_results: int = 50,
    ) -> BoardSearchResult:
        """List boards."""
        params = {
            "startAt": start_at,
            "maxResults": max_results,
        }
        if project_key:
            params["projectKeyOrId"] = project_key
        if board_name:
            params["name"] = board_name
        if board_type:
            params["type"] = board_type

        response = self.client.get_v1("/board", params=params)
        return BoardSearchResult.model_validate(response)

    def search(self, project_key: str, query: str, max_results: int = 50) -> BoardSearchResult:
        """Search boards by name."""
        params = {
            "projectKeyOrId": project_key,
            "name": query,
            "maxResults": max_results,
        }
        response = self.client.get_v1("/board", params=params)
        return BoardSearchResult.model_validate(response)

    def get(self, board_id: int) -> Board:
        """Get board by ID."""
        response = self.client.get_v1(f"/board/{board_id}")
        return Board.model_validate(response)


def get_boards(client: Client, project_key: str) -> List[Board]:
    """Get boards for a project."""
    ops = BoardOps(client)
    result = ops.list(project_key=project_key)
    return result.boards