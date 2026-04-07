"""Board command group."""

import click


@click.group()
def board() -> None:
    """Board commands."""
    pass


@board.command("list")
@click.option("--plain", is_flag=True, help="Plain text output")
@click.pass_context
def list_boards(ctx: click.Context, plain: bool) -> None:
    """List boards in the project."""
    from rich.console import Console
    from rich.table import Table

    from jira_cli.api.client import get_client

    console = Console()
    config = ctx.obj.get("config", {})
    project_key = config.get("project", {}).get("key", "")

    if not project_key:
        console.print("[red]No project configured.[/red]")
        return

    client = get_client(ctx)
    console.print("[dim]Fetching boards...[/dim]")

    try:
        boards = client.get_boards(project_key)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID")
    table.add_column("Name", style="green")
    table.add_column("Type")

    for board in boards:
        table.add_row(str(board.id), board.name, board.type)

    console.print(table)


@board.command("get")
@click.argument("board_id", type=int)
@click.pass_context
def get_board(ctx: click.Context, board_id: int) -> None:
    """Get a board by ID."""
    from rich.console import Console

    from jira_cli.api.client import get_client
    from jira_cli.pkg.jira.board import BoardOps

    console = Console()
    client = get_client(ctx)
    ops = BoardOps(client)

    try:
        b = ops.get(board_id)
        console.print(f"[bold]{b.name}[/bold]  (ID: {b.id}, Type: {b.type})")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@board.command("search")
@click.argument("query")
@click.pass_context
def search_boards(ctx: click.Context, query: str) -> None:
    """Search boards by name."""
    from rich.console import Console
    from rich.table import Table

    from jira_cli.api.client import get_client
    from jira_cli.pkg.jira.board import BoardOps

    console = Console()
    config = ctx.obj.get("config", {})
    project_key = config.get("project", {}).get("key", "")

    if not project_key:
        console.print("[red]No project configured.[/red]")
        return

    client = get_client(ctx)
    ops = BoardOps(client)

    try:
        result = ops.search(project_key, query)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID")
    table.add_column("Name", style="green")
    table.add_column("Type")

    for b in result.boards:
        table.add_row(str(b.id), b.name, b.type)

    console.print(table)