"""Issue view command."""

import json

import click
from rich.console import Console
from rich.table import Table
from rich.text import Text

from jira_cli.api.client import get_client
from jira_cli.pkg.jira.issue import IssueOps
from jira_cli.pkg.jira.markdown import from_jira_md


@click.command()
@click.argument("issue_key")
@click.option("--raw", is_flag=True, help="Output raw JSON")
@click.pass_context
def view_cmd(ctx: click.Context, issue_key: str, raw: bool) -> None:
    """View issue details.

    Display key, summary, status, priority, assignee, description,
    labels, components, dates, parent (for sub-tasks), and sub-tasks.
    """
    console = Console()
    client = get_client(ctx)
    ops = IssueOps(client)

    try:
        # Use v2 API for better compatibility with Local/Server
        issue = ops.get(issue_key, api_version=client.default_api_version)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    if raw:
        # Output raw JSON
        console.print_json(json.dumps(issue.model_dump(exclude_none=True, mode="json")))
        return

    # Format output
    fields = issue.fields

    # Header: KEY: Summary
    summary = Text()
    summary.append(issue.key, style="bold cyan")
    summary.append(": ", style="dim")
    summary.append(fields.summary)
    console.print(summary)

    # Details table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="dim")
    table.add_column("Value")

    # Type
    issue_type = fields.issue_type.name or fields.issue_type.handle or "-"
    table.add_row("Type:", issue_type)

    # Status
    status = fields.status.get("name", "-") if fields.status else "-"
    table.add_row("Status:", status)

    # Priority
    priority = fields.priority.get("name", "-") if fields.priority else "-"
    table.add_row("Priority:", priority)

    # Assignee
    assignee = fields.assignee.get("displayName", "-") if fields.assignee else "-"
    if assignee == "-" and fields.assignee and fields.assignee.get("name"):
        assignee = fields.assignee.get("name")
    table.add_row("Assignee:", assignee)

    # Reporter
    reporter = fields.reporter.get("displayName", "-") if fields.reporter else "-"
    if reporter == "-" and fields.reporter and fields.reporter.get("name"):
        reporter = fields.reporter.get("name")
    table.add_row("Reporter:", reporter)

    # Labels
    if fields.labels:
        table.add_row("Labels:", ", ".join(fields.labels))

    # Components
    if fields.components:
        components = [c.get("name", "") for c in fields.components]
        table.add_row("Components:", ", ".join(components))

    # Fix Versions
    if fields.fix_versions:
        versions = [v.get("name", "") for v in fields.fix_versions]
        table.add_row("Fix Versions:", ", ".join(versions))

    # Parent (for sub-tasks)
    if fields.parent:
        parent_key = fields.parent.get("key", "")
        parent_summary = fields.parent.get("fields", {}).get("summary", "")
        table.add_row("Parent:", f"{parent_key} {parent_summary}".strip())

    # Dates
    table.add_row("Created:", fields.created[:19].replace("T", " ") if fields.created else "-")
    table.add_row("Updated:", fields.updated[:19].replace("T", " ") if fields.updated else "-")

    console.print(table)

    # Description
    description = fields.description
    if description:
        console.print()
        console.print("[dim]Description:[/dim]")
        # Handle ADF (dict) or plain text
        if isinstance(description, dict):
            from jira_cli.pkg.adf.adf import adf_to_markdown
            description_text = adf_to_markdown(description)
        else:
            description_text = from_jira_md(str(description))
        console.print(description_text)

    # Sub-tasks
    if fields.subtasks:
        console.print()
        console.print("[dim]Sub-tasks:[/dim]")
        for subtask in fields.subtasks:
            sub_key = subtask.key
            sub_summary = subtask.fields.summary
            sub_status = subtask.fields.status.get("name", "-") if subtask.fields.status else "-"
            console.print(f"  {sub_key}: {sub_summary} [{sub_status}]")

    # Issue Links
    if fields.issue_links:
        console.print()
        console.print("[dim]Issue Links:[/dim]")
        for link in fields.issue_links:
            link_type = link.get("type", {}).get("name", "")
            inward_key = link.get("inwardIssue", {}).get("key", "")
            outward_key = link.get("outwardIssue", {}).get("key", "")
            if outward_key:
                console.print(f"  {link_type} -> {outward_key}")
            elif inward_key:
                console.print(f"  {inward_key} -> {link_type}")