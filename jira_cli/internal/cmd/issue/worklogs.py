"""Issue worklogs list command."""

import click
from rich.console import Console
from rich.table import Table

from jira_cli.api.client import get_client
from jira_cli.pkg.jira.issue import IssueOps
from jira_cli.pkg.jira.markdown import from_jira_md


@click.command(name="worklogs")
@click.argument("issue_key")
@click.option("--raw", is_flag=True, help="Output raw JSON")
@click.pass_context
def worklogs_cmd(ctx: click.Context, issue_key: str, raw: bool) -> None:
    """List worklog entries on an issue.

    Displays author, time spent, date, and comment for each worklog entry.
    """
    console = Console()
    client = get_client(ctx)
    ops = IssueOps(client)

    try:
        worklogs = ops.get_worklogs(issue_key, api_version=client.default_api_version)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    if not worklogs.worklogs:
        console.print(f"[dim]No worklogs on {issue_key}[/dim]")
        return

    if raw:
        import json
        console.print_json(json.dumps([w.model_dump(exclude_none=True, mode="json") for w in worklogs.worklogs]))
        return

    console.print(f"[bold]Worklog for {issue_key}:[/bold]")
    console.print()

    total_seconds = 0

    for wl in worklogs.worklogs:
        # Author
        author = wl.author.get("displayName", "")
        if not author and wl.author.get("name"):
            author = wl.author.get("name")
        if not author:
            author = "Unknown"

        # Time spent
        time_spent = wl.time_spent or "-"
        total_seconds += wl.time_spent_seconds

        # Date
        started = wl.started[:19].replace("T", " ") if wl.started else ""

        # Comment
        comment = from_jira_md(wl.comment) if wl.comment else ""

        # Format: [date] author: time "comment"
        time_str = f"[cyan]{time_spent:>8}[/cyan]"
        console.print(f"[dim][{started}][/dim] {author}: {time_str}  {comment}")

    # Total
    if total_seconds > 0:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        total_str = f"{hours}h {minutes}m".strip()
        console.print()
        console.print(f"[bold]Total: {total_str} ({total_seconds} seconds)[/bold]")