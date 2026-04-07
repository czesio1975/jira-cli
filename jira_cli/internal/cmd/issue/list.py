"""Issue list command.

Converted from internal/cmd/issue/list/list.go
"""

import json
from datetime import datetime
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from jira_cli.api.client import get_client
from jira_cli.internal.query.issue import IssueQuery

console = Console()


@click.command("list")  # type: ignore[misc]
@click.argument("search_query", required=False)
@click.option("-t", "--type", "issue_type", help="Filter by issue type")
@click.option("-s", "--status", multiple=True, help="Filter by status")
@click.option("-y", "--priority", help="Filter by priority")
@click.option("-r", "--reporter", help="Filter by reporter")
@click.option("-a", "--assignee", help="Filter by assignee")
@click.option("-l", "--label", multiple=True, help="Filter by label")
@click.option("--jql", "-q", help="Custom JQL query")
@click.option("--raw", is_flag=True, help="Raw JSON output")
@click.option("--paginate", default="0:100", help="Pagination (from:limit)")
@click.pass_context
def list_cmd(
    ctx: click.Context,
    search_query: Optional[str],
    issue_type: Optional[str],
    status: tuple[str, ...],
    priority: Optional[str],
    reporter: Optional[str],
    assignee: Optional[str],
    label: tuple[str, ...],
    jql: Optional[str],
    raw: bool,
    paginate: str,
) -> None:
    """List issues in a project."""
    config = ctx.obj.get("config", {})
    project_key = config.get("project", {}).get("key", "")

    if not project_key:
        console.print("[red]No project configured. Run 'jira init' first.[/red]")
        return

    # Parse pagination
    from_idx, limit = 0, 100
    if ":" in paginate:
        parts = paginate.split(":")
        from_idx = int(parts[0]) if parts[0] else 0
        limit = int(parts[1]) if parts[1] else 100
    else:
        limit = int(paginate)

    # Build JQL query
    query = IssueQuery(project_key)
    query.set_type(issue_type)
    query.set_status(list(status) if status else None)
    query.set_priority(priority)
    query.set_reporter(reporter)
    query.set_assignee(assignee)
    query.set_labels(list(label) if label else None)
    if jql:
        query.add_jql(jql)
    if search_query:
        query.add_search(search_query)

    # Get client and search
    client = get_client(ctx)

    console.print("[dim]Fetching issues...[/dim]")

    try:
        result = client.search_issues(query.build(), max_results=limit, start_at=from_idx)
        issues = result.issues

        if raw:
            # Output raw JSON
            data = [issue.model_dump() for issue in issues]
            console.print_json(json.dumps(data, indent=2))
            return

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Key", style="green")
        table.add_column("Type")
        table.add_column("Summary")
        table.add_column("Status")
        table.add_column("Priority")
        table.add_column("Assignee")

        for issue in issues:
            table.add_row(
                issue.key,
                issue.fields.issue_type.name,
                issue.fields.summary[:60],
                (issue.fields.status or {}).get("name", ""),
                (issue.fields.priority or {}).get("name", ""),
                (issue.fields.assignee or {}).get("displayName", "-") or "-",
            )

        console.print(table)
        console.print(f"\n[dim]Showing {len(issues)} of {result.total} results[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")