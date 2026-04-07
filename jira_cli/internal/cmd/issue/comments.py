"""Issue comments list command."""

import click
from rich.console import Console

from jira_cli.api.client import get_client
from jira_cli.pkg.jira.issue import IssueOps
from jira_cli.pkg.jira.markdown import from_jira_md


@click.command(name="comments")
@click.argument("issue_key")
@click.pass_context
def comments_cmd(ctx: click.Context, issue_key: str) -> None:
    """List comments on an issue.

    Displays author, date, and comment body for each comment.
    """
    console = Console()
    client = get_client(ctx)
    ops = IssueOps(client)

    try:
        comments = ops.get_comments(issue_key, api_version=client.default_api_version)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    if not comments.comments:
        console.print(f"[dim]No comments on {issue_key}[/dim]")
        return

    console.print(f"[bold]Comments on {issue_key}:[/bold]")
    console.print()

    for comment in comments.comments:
        # Author
        author = comment.author.get("displayName", "")
        if not author and comment.author.get("name"):
            author = comment.author.get("name")
        if not author:
            author = "Unknown"

        # Date
        created = comment.created[:19].replace("T", " ") if comment.created else ""

        # Body - handle ADF or plain text
        body = comment.body
        if isinstance(body, dict):
            from jira_cli.pkg.adf.adf import adf_to_markdown
            body_text = adf_to_markdown(body)
        else:
            body_text = from_jira_md(str(body)) if body else ""

        console.print(f"[dim][{created}][/] [cyan]{author}:[/cyan]")
        # Indent comment body
        for line in body_text.split("\n"):
            console.print(f"  {line}")
        console.print()