"""Issue assign command.

Wires up IssueOps.assign() to the CLI.
"""

import click
from rich.console import Console

from jira_cli.api.client import get_client
from jira_cli.pkg.jira.issue import IssueOps

console = Console()


@click.command("assign")
@click.argument("issue_key")
@click.argument("assignee")
@click.pass_context
def assign_cmd(ctx: click.Context, issue_key: str, assignee: str) -> None:
    """Assign an issue to a user.

    ASSIGNEE is an account ID, username, "none" to unassign, or "default".
    """
    client = get_client(ctx)
    ops = IssueOps(client)

    try:
        ops.assign(issue_key, assignee, api_version=client.default_api_version)
        if assignee == "none":
            console.print(f"[green]Unassigned {issue_key}[/green]")
        else:
            console.print(f"[green]Assigned {issue_key} to {assignee}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
