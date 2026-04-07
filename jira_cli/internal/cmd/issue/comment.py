"""Issue comment command.

Wires up IssueOps.add_comment() to the CLI.
"""

import click
from rich.console import Console

from jira_cli.api.client import get_client
from jira_cli.pkg.jira.issue import IssueOps

console = Console()


@click.command("comment")
@click.argument("issue_key")
@click.argument("body")
@click.option("--internal", is_flag=True, help="Mark as internal comment (Service Desk)")
@click.pass_context
def comment_cmd(ctx: click.Context, issue_key: str, body: str, internal: bool) -> None:
    """Add a comment to an issue."""
    client = get_client(ctx)
    ops = IssueOps(client)

    try:
        ops.add_comment(issue_key, body, internal=internal)
        console.print(f"[green]Comment added to {issue_key}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
