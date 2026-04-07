"""Issue query builder.

Converted from internal/query/issue.go
"""

from datetime import datetime, timedelta
from typing import Optional


class IssueQuery:
    """JQL query builder for issues."""

    def __init__(self, project_key: str) -> None:
        self.project_key = project_key
        self.conditions: list[str] = [f'project = "{project_key}"']
        self.order_by: str = "created DESC"
        self._from: int = 0
        self._limit: int = 100

    def set_type(self, issue_type: Optional[str]) -> "IssueQuery":
        """Set issue type filter."""
        if issue_type:
            self.conditions.append(f'issuetype = "{issue_type}"')
        return self

    def set_status(self, statuses: Optional[list[str]]) -> "IssueQuery":
        """Set status filter."""
        if statuses:
            status_list = ", ".join(f'"{s}"' for s in statuses)
            self.conditions.append(f"status in ({status_list})")
        return self

    def set_priority(self, priority: Optional[str]) -> "IssueQuery":
        """Set priority filter."""
        if priority:
            self.conditions.append(f'priority = "{priority}"')
        return self

    def set_reporter(self, reporter: Optional[str]) -> "IssueQuery":
        """Set reporter filter."""
        if reporter:
            self.conditions.append(f'reporter = "{reporter}"')
        return self

    def set_assignee(self, assignee: Optional[str]) -> "IssueQuery":
        """Set assignee filter."""
        if assignee:
            if assignee.lower() == "none" or assignee == "x":
                self.conditions.append("assignee is EMPTY")
            else:
                self.conditions.append(f'assignee = "{assignee}"')
        return self

    def set_labels(self, labels: Optional[list[str]]) -> "IssueQuery":
        """Set labels filter."""
        if labels:
            for label in labels:
                self.conditions.append(f'labels = "{label}"')
        return self

    def set_component(self, component: Optional[str]) -> "IssueQuery":
        """Set component filter."""
        if component:
            self.conditions.append(f'component = "{component}"')
        return self

    def set_created(self, created: Optional[str]) -> "IssueQuery":
        """Set created date filter."""
        if created:
            date_filter = self._parse_date_filter(created, "created")
            if date_filter:
                self.conditions.append(date_filter)
        return self

    def set_updated(self, updated: Optional[str]) -> "IssueQuery":
        """Set updated date filter."""
        if updated:
            date_filter = self._parse_date_filter(updated, "updated")
            if date_filter:
                self.conditions.append(date_filter)
        return self

    def add_jql(self, jql: str) -> "IssueQuery":
        """Add custom JQL."""
        self.conditions.append(jql)
        return self

    def add_search(self, text: str) -> "IssueQuery":
        """Add text search."""
        self.conditions.append(f'text ~ "{text}"')
        return self

    def set_order_by(self, field: str, reverse: bool = False) -> "IssueQuery":
        """Set order by."""
        direction = "ASC" if reverse else "DESC"
        self.order_by = f"{field} {direction}"
        return self

    def set_pagination(self, from_idx: int, limit: int) -> "IssueQuery":
        """Set pagination."""
        self._from = from_idx
        self._limit = limit
        return self

    def _parse_date_filter(self, value: str, field: str) -> Optional[str]:
        """Parse date filter value."""
        now = datetime.now()

        # Relative dates
        if value == "today":
            return f'{field} >= startOfDay()'
        elif value == "week":
            week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")
            return f'{field} >= "{week_ago}"'
        elif value == "month":
            month_ago = (now - timedelta(days=30)).strftime("%Y-%m-%d")
            return f'{field} >= "{month_ago}"'
        elif value == "year":
            year_ago = (now - timedelta(days=365)).strftime("%Y-%m-%d")
            return f'{field} >= "{year_ago}"'

        # Period format (e.g., -10d, -2w)
        if value.startswith("-"):
            try:
                num = int(value[1:-1])
                unit = value[-1].lower()
                if unit == "d":
                    date = (now - timedelta(days=num)).strftime("%Y-%m-%d")
                elif unit == "w":
                    date = (now - timedelta(weeks=num)).strftime("%Y-%m-%d")
                elif unit == "h":
                    date = (now - timedelta(hours=num)).strftime("%Y-%m-%d")
                elif unit == "m":
                    date = (now - timedelta(minutes=num)).strftime("%Y-%m-%d")
                else:
                    return None
                return f'{field} >= "{date}"'
            except (ValueError, IndexError):
                return None

        # Exact date
        try:
            # Try parsing as YYYY-MM-DD or YYYY/MM/DD
            date_str = value.replace("/", "-")
            datetime.strptime(date_str, "%Y-%m-%d")
            return f'{field} = "{date_str}"'
        except ValueError:
            return None

    def build(self) -> str:
        """Build the JQL query string."""
        jql = " AND ".join(self.conditions)
        if self.order_by:
            jql += f" ORDER BY {self.order_by}"
        return jql

    def params(self) -> dict:
        """Get query parameters."""
        return {
            "from": self._from,
            "limit": self._limit,
        }