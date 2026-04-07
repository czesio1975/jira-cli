"""Issue delete command.

Wires up pkg/jira/delete.py to the CLI.
"""

import click
from rich.console import Console

from jira_cli.api.client import get_client
from jira_cli.pkg.jira.delete import DeleteOps

console = Console()


@click.command("delete")
@click.argument("issue_key")
@click.option("--cascade", is_flag=True, help="Delete subtasks as well")
@click.confirmation_option(prompt="Are you sure you want to delete this issue?")
@click.pass_context
def delete_cmd(ctx: click.Context, issue_key: str, cascade: bool) -> None:
    """Delete an issue."""
    client = get_client(ctx)
    ops = DeleteOps(client)

    try:
        if cascade:
            ops.delete_issue_with_subtasks(issue_key)
        else:
            ops.delete_issue(issue_key)
        console.print(f"[green]Deleted {issue_key}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
