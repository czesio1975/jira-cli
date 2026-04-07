"""Sprint command group."""

from typing import Optional

import click


@click.group()
def sprint() -> None:
    """Sprint commands."""
    pass


@sprint.command("create")
@click.argument("name")
@click.option("--board-id", type=int, required=True, help="Board ID")
@click.option("--start-date", help="Start date (ISO 8601)")
@click.option("--end-date", help="End date (ISO 8601)")
@click.pass_context
def create_sprint(
    ctx: click.Context,
    name: str,
    board_id: int,
    start_date: Optional[str],
    end_date: Optional[str],
) -> None:
    """Create a new sprint."""
    from rich.console import Console

    from jira_cli.api.client import get_client
    from jira_cli.pkg.jira.sprint import SprintOps

    console = Console()
    client = get_client(ctx)
    ops = SprintOps(client)

    try:
        result = ops.create(board_id, name, start_date=start_date, end_date=end_date)
        console.print(f"[green]Created sprint '{result.name}' (ID: {result.id})[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@sprint.command("start")
@click.argument("sprint_id", type=int)
@click.pass_context
def start_sprint(ctx: click.Context, sprint_id: int) -> None:
    """Start a sprint."""
    from rich.console import Console

    from jira_cli.api.client import get_client
    from jira_cli.pkg.jira.sprint import SprintOps

    console = Console()
    client = get_client(ctx)
    ops = SprintOps(client)

    try:
        result = ops.start(sprint_id)
        console.print(f"[green]Started sprint '{result.name}'[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@sprint.command("close")
@click.argument("sprint_id", type=int)
@click.pass_context
def close_sprint(ctx: click.Context, sprint_id: int) -> None:
    """Close a sprint."""
    from rich.console import Console

    from jira_cli.api.client import get_client
    from jira_cli.pkg.jira.sprint import SprintOps

    console = Console()
    client = get_client(ctx)
    ops = SprintOps(client)

    try:
        result = ops.close(sprint_id)
        console.print(f"[green]Closed sprint '{result.name}'[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@sprint.command("list")
@click.option("--plain", is_flag=True, help="Plain text output")
@click.pass_context
def list_sprints(ctx: click.Context, plain: bool) -> None:
    """List sprints in the project."""
    from rich.console import Console
    from rich.table import Table

    from jira_cli.api.client import get_client

    console = Console()
    config = ctx.obj.get("config", {})
    project_key = config.get("project", {}).get("key", "")
    board_name = config.get("board", {}).get("name", "")

    if not project_key:
        console.print("[red]No project configured.[/red]")
        return

    client = get_client(ctx)
    console.print("[dim]Fetching boards...[/dim]")

    try:
        # Get boards for project
        boards = client.get_boards(project_key)
    except Exception as e:
        console.print(f"[red]Error fetching boards: {e}[/red]")
        return

    if not boards:
        console.print("[yellow]No boards found.[/yellow]")
        return

    console.print("[dim]Fetching sprints...[/dim]")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Board")
    table.add_column("Sprint")
    table.add_column("Status")
    table.add_column("Start")
    table.add_column("End")

    for board in boards:
        try:
            sprints = client.get_sprints(board.id)
        except Exception:
            continue
        for sprint in sprints:
            table.add_row(
                board.name,
                sprint.name,
                sprint.status,
                sprint.start_date[:10] if sprint.start_date else "-",
                sprint.end_date[:10] if sprint.end_date else "-",
            )

    console.print(table)