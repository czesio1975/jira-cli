"""Issue unlink command.

Wires up IssueOps.unlink() to the CLI.
"""

import click
from rich.console import Console

from jira_cli.api.client import get_client
from jira_cli.pkg.jira.issue import IssueOps

console = Console()


@click.command("unlink")
@click.argument("issue_key")
@click.argument("other_issue")
@click.pass_context
def unlink_cmd(ctx: click.Context, issue_key: str, other_issue: str) -> None:
    """Remove a link between two issues."""
    client = get_client(ctx)
    ops = IssueOps(client)

    try:
        link_id = ops.get_link_id(issue_key, other_issue)
        if not link_id:
            console.print(f"[yellow]No link found between {issue_key} and {other_issue}[/yellow]")
            return

        ops.unlink(link_id)
        console.print(f"[green]Unlinked {issue_key} and {other_issue}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
