"""Root CLI command.

Converted from internal/cmd/root/root.go
"""

import os
from pathlib import Path
from typing import Optional

import click
import yaml
from rich.console import Console

from jira_cli import __version__

console = Console()

# Config directory and file (same as Go version)
CONFIG_DIR = ".jira"
CONFIG_FILE = ".config"
CONFIG_EXT = "yml"


def get_config_home() -> Path:
    """Get the config home directory."""
    # Follow XDG Base Directory Specification
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config)
    return Path.home()


def get_config_path() -> Path:
    """Get the config file path."""
    return get_config_home() / CONFIG_DIR / f"{CONFIG_FILE}.{CONFIG_EXT}"


def load_config(config_path: Optional[str] = None) -> dict:
    """Load configuration from file.

    Compatible with config files created by the Go version of jira-cli.
    """
    if config_path:
        path = Path(config_path)
    else:
        # Check environment variable
        env_config = os.environ.get("JIRA_CONFIG_FILE")
        if env_config:
            path = Path(env_config)
        else:
            path = get_config_path()

    if not path.exists():
        return {}

    with open(path) as f:
        return yaml.safe_load(f) or {}


# Global config (loaded once)
_config: Optional[dict] = None


def get_config() -> dict:
    """Get the global config."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reset_config() -> None:
    """Reset the global config (for testing)."""
    global _config
    _config = None


@click.group()
@click.option("-c", "--config", type=click.Path(exists=True), help="Config file path")
@click.option("-p", "--project", "project_key", help="Jira project key")
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.version_option(version=__version__, prog_name="jira")
@click.pass_context
def root(
    ctx: click.Context,
    config: Optional[str],
    project_key: Optional[str],
    debug: bool,
) -> None:
    """Interactive Jira command line tool."""
    # Ensure context has a dict for passing data
    ctx.ensure_object(dict)

    # Load config
    cfg = load_config(config) if config else load_config()
    ctx.obj["config"] = cfg
    ctx.obj["config_path"] = config
    ctx.obj["debug"] = debug

    # Override project if specified
    if project_key:
        cfg["project"] = {"key": project_key}

    # Store in context
    ctx.obj["project_key"] = project_key or cfg.get("project", {}).get("key", "")


# Import and register subcommands
def register_commands() -> None:
    """Register all subcommands."""
    from jira_cli.internal.cmd.init import init
    from jira_cli.internal.cmd.issue.issue import issue
    from jira_cli.internal.cmd.epic.epic import epic
    from jira_cli.internal.cmd.sprint.sprint import sprint
    from jira_cli.internal.cmd.board.board import board
    from jira_cli.internal.cmd.project.project import project
    from jira_cli.internal.cmd.release.release import release
    from jira_cli.internal.cmd.me import me_cmd

    root.add_command(init)
    root.add_command(issue)
    root.add_command(epic)
    root.add_command(sprint)
    root.add_command(board)
    root.add_command(project)
    root.add_command(release)
    root.add_command(me_cmd)


# Register commands on import
register_commands()