"""Main entry point for Jira CLI."""

import sys

import click

from jira_cli.internal.cmd.root import root


def main() -> None:
    """Main entry point."""
    try:
        root()
    except KeyboardInterrupt:
        click.echo("\nAborted.")
        sys.exit(1)


if __name__ == "__main__":
    main()