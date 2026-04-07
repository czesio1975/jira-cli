"""Issue link command.

Wires up IssueOps.link() to the CLI.
"""

import click
from rich.console import Console

from jira_cli.api.client import get_client
from jira_cli.pkg.jira.issue import IssueOps

console = Console()


@click.command("link")
@click.argument("inward_issue")
@click.argument("outward_issue")
@click.option("-t", "--type", "link_type", default="Blocks", help="Link type name (e.g. Blocks, Cloners, Duplicate)")
@click.pass_context
def link_cmd(ctx: click.Context, inward_issue: str, outward_issue: str, link_type: str) -> None:
    """Link two issues.

    INWARD_ISSUE blocks/is cloned by/etc. OUTWARD_ISSUE.
    """
    client = get_client(ctx)
    ops = IssueOps(client)

    try:
        ops.link(inward_issue, outward_issue, link_type)
        console.print(f"[green]Linked {inward_issue} -> {outward_issue} ({link_type})[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
