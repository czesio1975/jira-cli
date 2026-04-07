"""Issue worklog command.

Wires up IssueOps.add_worklog() to the CLI.
"""

from typing import Optional

import click
from rich.console import Console

from jira_cli.api.client import get_client
from jira_cli.pkg.jira.issue import IssueOps

console = Console()


@click.command("worklog")
@click.argument("issue_key")
@click.argument("time_spent")
@click.option("-m", "--comment", default="", help="Worklog comment")
@click.option("--started", default="", help="Start time (Jira format, e.g. 2024-01-15T09:00:00.000+0000)")
@click.option("--new-estimate", default="", help="New remaining estimate (e.g. 2h, 1d)")
@click.pass_context
def worklog_cmd(
    ctx: click.Context,
    issue_key: str,
    time_spent: str,
    comment: str,
    started: str,
    new_estimate: str,
) -> None:
    """Add a worklog entry to an issue.

    TIME_SPENT is a Jira duration string (e.g. 1h, 30m, 1d, 2h 30m).
    """
    client = get_client(ctx)
    ops = IssueOps(client)

    try:
        ops.add_worklog(issue_key, time_spent, comment=comment, started=started, new_estimate=new_estimate)
        console.print(f"[green]Logged {time_spent} on {issue_key}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
