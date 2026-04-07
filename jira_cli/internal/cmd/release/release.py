"""Release/version command group."""

from typing import Optional

import click


@click.group()
def release() -> None:
    """Release/version commands."""
    pass


@release.command("list")
@click.argument("project_key", required=False)
@click.pass_context
def list_releases(ctx: click.Context, project_key: str | None) -> None:
    """List versions/releases for a project.

    Uses the configured project if PROJECT_KEY is omitted.
    """
    from rich.console import Console
    from rich.table import Table

    from jira_cli.api.client import get_client
    from jira_cli.pkg.jira.release import ReleaseOps

    console = Console()

    if not project_key:
        config = ctx.obj.get("config", {})
        project_key = config.get("project", {}).get("key", "")

    if not project_key:
        console.print("[red]No project specified or configured.[/red]")
        return

    client = get_client(ctx)
    ops = ReleaseOps(client)

    try:
        versions = ops.list(project_key)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID")
    table.add_column("Name", style="green")
    table.add_column("Released")
    table.add_column("Archived")
    table.add_column("Description")

    for v in versions:
        table.add_row(v.id, v.name, str(v.released), str(v.archived), v.description or "")

    console.print(table)


@release.command("create")
@click.argument("name")
@click.option("-d", "--description", help="Version description")
@click.option("--release-date", help="Release date (YYYY-MM-DD)")
@click.option("--released", is_flag=True, help="Mark as already released")
@click.pass_context
def create_release(
    ctx: click.Context,
    name: str,
    description: Optional[str],
    release_date: Optional[str],
    released: bool,
) -> None:
    """Create a new version/release."""
    from rich.console import Console

    from jira_cli.api.client import get_client
    from jira_cli.pkg.jira.release import ReleaseOps

    console = Console()
    config = ctx.obj.get("config", {})
    project_key = config.get("project", {}).get("key", "")

    if not project_key:
        console.print("[red]No project configured.[/red]")
        return

    client = get_client(ctx)
    ops = ReleaseOps(client)

    try:
        v = ops.create(
            project_key,
            name,
            description=description,
            released=released,
            release_date=release_date,
        )
        console.print(f"[green]Created version '{v.name}' (ID: {v.id})[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@release.command("release")
@click.argument("version_id")
@click.option("--release-date", help="Release date (YYYY-MM-DD, defaults to today)")
@click.pass_context
def release_version(ctx: click.Context, version_id: str, release_date: Optional[str]) -> None:
    """Release a version."""
    from rich.console import Console

    from jira_cli.api.client import get_client
    from jira_cli.pkg.jira.release import ReleaseOps

    console = Console()
    client = get_client(ctx)
    ops = ReleaseOps(client)

    try:
        v = ops.release(version_id, release_date=release_date)
        console.print(f"[green]Released version '{v.name}'[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
