"""Issue remote link command.

Wires up IssueOps.remote_link() to the CLI.
"""

import click
from rich.console import Console

from jira_cli.api.client import get_client
from jira_cli.pkg.jira.issue import IssueOps

console = Console()


@click.command("remote-link")
@click.argument("issue_key")
@click.argument("url")
@click.option("-t", "--title", required=True, help="Link title")
@click.pass_context
def remote_link_cmd(ctx: click.Context, issue_key: str, url: str, title: str) -> None:
    """Add a remote link to an issue."""
    client = get_client(ctx)
    ops = IssueOps(client)

    try:
        ops.remote_link(issue_key, title, url)
        console.print(f"[green]Added remote link to {issue_key}: {title}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
