"""Issue edit command.

Wires up pkg/jira/edit.py to the CLI.
"""

from typing import Optional

import click
from rich.console import Console

from jira_cli.api.client import get_client
from jira_cli.pkg.jira.edit import EditOps

console = Console()


@click.command("edit")
@click.argument("issue_key")
@click.option("-s", "--summary", help="New summary")
@click.option("-d", "--description", help="New description")
@click.option("-y", "--priority", help="New priority")
@click.option("-a", "--assignee", help="New assignee")
@click.option("-l", "--label", multiple=True, help="Set labels (replaces existing)")
@click.option("-C", "--component", multiple=True, help="Set components (replaces existing)")
@click.pass_context
def edit_cmd(
    ctx: click.Context,
    issue_key: str,
    summary: Optional[str],
    description: Optional[str],
    priority: Optional[str],
    assignee: Optional[str],
    label: tuple[str, ...],
    component: tuple[str, ...],
) -> None:
    """Edit an existing issue."""
    client = get_client(ctx)
    ops = EditOps(client)

    try:
        ops.edit(
            key=issue_key,
            summary=summary,
            description=description,
            priority=priority,
            assignee=assignee,
            labels=list(label) if label else None,
            components=list(component) if component else None,
            api_version=client.default_api_version,
        )
        console.print(f"[green]Updated {issue_key}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
