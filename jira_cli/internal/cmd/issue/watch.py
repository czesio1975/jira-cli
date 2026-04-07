"""Issue watch command.

Wires up IssueOps.watch() to the CLI.
"""

import click
from rich.console import Console

from jira_cli.api.client import get_client
from jira_cli.pkg.jira.issue import IssueOps

console = Console()


@click.command("watch")
@click.argument("issue_key")
@click.argument("watcher")
@click.pass_context
def watch_cmd(ctx: click.Context, issue_key: str, watcher: str) -> None:
    """Add a watcher to an issue.

    WATCHER is an account ID or username.
    """
    client = get_client(ctx)
    ops = IssueOps(client)

    try:
        ops.watch(issue_key, watcher, api_version=client.default_api_version)
        console.print(f"[green]Added {watcher} as watcher on {issue_key}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
