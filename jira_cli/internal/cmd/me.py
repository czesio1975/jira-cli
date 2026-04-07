"""Me command.

Wires up MeOps.get_me() to the CLI.
"""

import click
from rich.console import Console

from jira_cli.api.client import get_client
from jira_cli.pkg.jira.me import MeOps

console = Console()


@click.command("me")
@click.pass_context
def me_cmd(ctx: click.Context) -> None:
    """Show current authenticated user info."""
    client = get_client(ctx)
    ops = MeOps(client)

    try:
        user = ops.get_me(api_version=client.default_api_version)
        console.print(f"[bold]{user.display_name}[/bold]")
        console.print(f"  Account ID: {user.account_id}")
        console.print(f"  Email:      {user.email}")
        console.print(f"  Active:     {user.active}")
        if user.timezone:
            console.print(f"  Timezone:   {user.timezone}")
        if user.locale:
            console.print(f"  Locale:     {user.locale}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
