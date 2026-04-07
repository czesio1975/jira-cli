"""Init command.

Converted from internal/cmd/init/init.go
"""

import os
from pathlib import Path
from typing import Optional

import click
import questionary
import yaml
from rich.console import Console
from rich.spinner import Spinner

from jira_cli.internal.cmd.root import CONFIG_DIR, CONFIG_FILE, CONFIG_EXT, get_config_home
from jira_cli.pkg.jira import Client, AuthType

console = Console()


@click.command()
@click.option("--installation", type=click.Choice(["cloud", "local"]), default="cloud")
@click.option("--server", help="Jira server URL")
@click.option("--login", help="Login email/username")
@click.option("--project", help="Default project key")
@click.option("--board", help="Default board name")
@click.option("--force", is_flag=True, help="Overwrite existing config")
@click.pass_context
def init(
    ctx: click.Context,
    installation: str,
    server: Optional[str],
    login: Optional[str],
    project: Optional[str],
    board: Optional[str],
    force: bool,
) -> None:
    """Initialize Jira CLI configuration."""
    console.print("[bold]Jira CLI Configuration[/bold]")

    # Get config path
    config_home = get_config_home()
    config_dir = config_home / CONFIG_DIR
    config_path = config_dir / f"{CONFIG_FILE}.{CONFIG_EXT}"

    # Check if config exists
    if config_path.exists() and not force:
        overwrite = questionary.confirm(
            "Config already exists. Do you want to overwrite?",
            default=False,
        ).ask()
        if not overwrite:
            console.print("[yellow]Skipping configuration.[/yellow]")
            return

    # Ask for installation type
    if not installation:
        installation = questionary.select(
            "Installation type:",
            choices=["cloud", "local"],
            default="cloud",
        ).ask()

    # Ask for server URL
    if not server:
        server = questionary.text(
            "Link to Jira server:",
            validate=lambda x: x.startswith("http://") or x.startswith("https://"),
        ).ask()

    # Ask for login
    if not login:
        if installation == "cloud":
            login = questionary.text(
                "Login email:",
                validate=lambda x: "@" in x and len(x) > 3,
            ).ask()
        else:
            login = questionary.text(
                "Login username:",
                validate=lambda x: len(x) >= 2,
            ).ask()

    # Get API token from environment or prompt
    api_token = os.environ.get("JIRA_API_TOKEN")
    if not api_token:
        api_token = questionary.password(
            "API token (leave empty to use keyring/netrc):",
        ).ask()

    # Auth type
    auth_type = AuthType.BASIC
    if installation == "local":
        auth_type_str = questionary.select(
            "Authentication type:",
            choices=["basic", "bearer", "mtls"],
            default="basic",
        ).ask()
        auth_type = AuthType(auth_type_str)

    # Verify connection
    console.print("[dim]Verifying connection...[/dim]")

    client = Client(
        server=server,
        login=login,
        token=api_token or "",
        auth_type=auth_type,
    )

    try:
        user_info = client.get("/myself", api_version="v3")
        console.print(f"[green]Connected as: {user_info.get('displayName', login)}[/green]")
    except Exception as e:
        console.print(f"[red]Connection failed: {e}[/red]")
        if not questionary.confirm("Continue anyway?", default=False).ask():
            return

    # Get projects
    console.print("[dim]Fetching projects...[/dim]")
    projects = client.get_v2("/project")

    project_choices = [p.get("key", "") for p in projects]
    if not project:
        project = questionary.select(
            "Default project:",
            choices=project_choices,
        ).ask()

    # Get boards
    console.print("[dim]Fetching boards...[/dim]")
    boards = client.get_v1("/board", params={"projectKeyOrId": project})

    board_choices = [b.get("name", "") for b in boards.get("values", [])] + ["None"]
    if not board:
        board = questionary.select(
            "Default board:",
            choices=board_choices,
        ).ask()

    if board == "None":
        board = ""

    # Create config
    config = {
        "installation": installation.capitalize(),
        "server": server.rstrip("/"),
        "login": login,
        "project": {
            "key": project,
            "name": next((p.get("name", "") for p in projects if p.get("key") == project), ""),
        },
        "board": {"name": board} if board else "",
        "auth_type": str(auth_type),
    }

    # Write config
    config_dir.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    console.print(f"[green]Config written to: {config_path}[/green]")
    console.print("[green]Configuration complete![/green]")