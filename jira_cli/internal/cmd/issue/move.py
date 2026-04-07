"""Issue move (transition) command.

Wires up IssueOps.transition() to the CLI.
"""

from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from jira_cli.api.client import get_client
from jira_cli.pkg.jira.issue import IssueOps

console = Console()


@click.command("move")
@click.argument("issue_key")
@click.argument("status", required=False)
@click.pass_context
def move_cmd(ctx: click.Context, issue_key: str, status: Optional[str]) -> None:
    """Move an issue to a new status.

    If STATUS is omitted, lists available transitions.
    """
    client = get_client(ctx)
    ops = IssueOps(client)

    try:
        transitions = ops.get_transitions(issue_key, api_version=client.default_api_version)

        if not status:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("ID")
            table.add_column("Name")
            for t in transitions:
                table.add_row(t.id, t.name)
            console.print(table)
            return

        # Find matching transition (case-insensitive)
        match = None
        for t in transitions:
            if t.name.lower() == status.lower():
                match = t
                break

        if not match:
            names = ", ".join(t.name for t in transitions)
            console.print(f"[red]No transition '{status}' found. Available: {names}[/red]")
            return

        ops.transition(issue_key, match.id, api_version=client.default_api_version)
        console.print(f"[green]Moved {issue_key} to '{match.name}'[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
