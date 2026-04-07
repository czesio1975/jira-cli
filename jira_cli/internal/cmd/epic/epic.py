"""Epic command group."""

import click


@click.group()
def epic() -> None:
    """Epic commands."""
    pass


@epic.command("list")
@click.option("--plain", is_flag=True, help="Plain text output")
@click.pass_context
def list_epics(ctx: click.Context, plain: bool) -> None:
    """List epics in the project."""
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
    console.print("[dim]Fetching epics...[/dim]")

    # Search for epics
    jql = f'project = "{project_key}" AND issuetype = "Epic"'
    result = client.search_issues(jql, max_results=100)

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Key", style="green")
    table.add_column("Summary")
    table.add_column("Status")
    table.add_column("Priority")

    for issue in result.issues:
        table.add_row(
            issue.key,
            issue.fields.summary[:60],
            (issue.fields.status or {}).get("name", ""),
            (issue.fields.priority or {}).get("name", ""),
        )

    console.print(table)