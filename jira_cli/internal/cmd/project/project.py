"""Project command group."""

import click


@click.group()
def project() -> None:
    """Project commands."""
    pass


@project.command("list")
@click.option("--plain", is_flag=True, help="Plain text output")
@click.pass_context
def list_projects(ctx: click.Context, plain: bool) -> None:
    """List projects."""
    from rich.console import Console
    from rich.table import Table

    from jira_cli.api.client import get_client

    console = Console()
    client = get_client(ctx)

    console.print("[dim]Fetching projects...[/dim]")

    projects = client.get_projects()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Key", style="green")
    table.add_column("Name")
    table.add_column("Type")

    for p in projects:
        table.add_row(p.key, p.name, p.type)

    console.print(table)


@project.command("get")
@click.argument("project_key")
@click.pass_context
def get_project(ctx: click.Context, project_key: str) -> None:
    """Get a project by key."""
    from rich.console import Console

    from jira_cli.api.client import get_client
    from jira_cli.pkg.jira.project import ProjectOps

    console = Console()
    client = get_client(ctx)
    ops = ProjectOps(client)

    try:
        p = ops.get(project_key)
        lead_name = p.lead.get("displayName", "")
        console.print(f"[bold]{p.key}[/bold] - {p.name}")
        console.print(f"  Type: {p.type}")
        if lead_name:
            console.print(f"  Lead: {lead_name}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@project.command("versions")
@click.argument("project_key", required=False)
@click.pass_context
def project_versions(ctx: click.Context, project_key: str | None) -> None:
    """List versions for a project.

    Uses the configured project if PROJECT_KEY is omitted.
    """
    from rich.console import Console
    from rich.table import Table

    from jira_cli.api.client import get_client
    from jira_cli.pkg.jira.project import ProjectOps

    console = Console()

    if not project_key:
        config = ctx.obj.get("config", {})
        project_key = config.get("project", {}).get("key", "")

    if not project_key:
        console.print("[red]No project specified or configured.[/red]")
        return

    client = get_client(ctx)
    ops = ProjectOps(client)

    try:
        versions = ops.get_versions(project_key)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID")
    table.add_column("Name", style="green")
    table.add_column("Released")
    table.add_column("Archived")

    for v in versions:
        table.add_row(v.id, v.name, str(v.released), str(v.archived))

    console.print(table)