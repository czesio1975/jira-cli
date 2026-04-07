"""Issue create command.

Wires up pkg/jira/create.py to the CLI.
"""

from typing import Optional

import click
from rich.console import Console

from jira_cli.api.client import get_client
from jira_cli.pkg.jira.create import CreateOps

console = Console()


@click.command("create")
@click.argument("summary")
@click.option("-t", "--type", "issue_type", default="Task", help="Issue type (default: Task)")
@click.option("-d", "--description", help="Issue description")
@click.option("-a", "--assignee", help="Assignee account ID or username")
@click.option("-y", "--priority", help="Priority (e.g. High, Medium, Low)")
@click.option("-l", "--label", multiple=True, help="Labels")
@click.option("-C", "--component", multiple=True, help="Components")
@click.option("--parent", help="Parent issue key (for subtasks)")
@click.pass_context
def create_cmd(
    ctx: click.Context,
    summary: str,
    issue_type: str,
    description: Optional[str],
    assignee: Optional[str],
    priority: Optional[str],
    label: tuple[str, ...],
    component: tuple[str, ...],
    parent: Optional[str],
) -> None:
    """Create a new issue."""
    config = ctx.obj.get("config", {})
    project_key = config.get("project", {}).get("key", "")

    if not project_key:
        console.print("[red]No project configured. Run 'jira init' first.[/red]")
        return

    client = get_client(ctx)
    ops = CreateOps(client)

    try:
        result = ops.create(
            project_key=project_key,
            summary=summary,
            issue_type=issue_type,
            description=description,
            parent=parent,
            assignee=assignee,
            priority=priority,
            labels=list(label) if label else None,
            components=list(component) if component else None,
            api_version=client.default_api_version,
        )
        console.print(f"[green]Created {result.get('key', '')}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
