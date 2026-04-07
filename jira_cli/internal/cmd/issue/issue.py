"""Issue command group.

Converted from internal/cmd/issue/issue.go
"""

import click

from jira_cli.internal.cmd.issue.list import list_cmd
from jira_cli.internal.cmd.issue.create import create_cmd
from jira_cli.internal.cmd.issue.edit import edit_cmd
from jira_cli.internal.cmd.issue.delete import delete_cmd
from jira_cli.internal.cmd.issue.assign import assign_cmd
from jira_cli.internal.cmd.issue.move import move_cmd
from jira_cli.internal.cmd.issue.comment import comment_cmd
from jira_cli.internal.cmd.issue.link import link_cmd
from jira_cli.internal.cmd.issue.unlink import unlink_cmd
from jira_cli.internal.cmd.issue.watch import watch_cmd
from jira_cli.internal.cmd.issue.worklog import worklog_cmd
from jira_cli.internal.cmd.issue.remote_link import remote_link_cmd
from jira_cli.internal.cmd.issue.view import view_cmd
from jira_cli.internal.cmd.issue.comments import comments_cmd
from jira_cli.internal.cmd.issue.worklogs import worklogs_cmd


@click.group()
def issue() -> None:
    """Issue commands."""
    pass


# Add subcommands
issue.add_command(list_cmd, name="list")
issue.add_command(list_cmd, name="ls")
issue.add_command(view_cmd)
issue.add_command(create_cmd)
issue.add_command(edit_cmd)
issue.add_command(delete_cmd)
issue.add_command(assign_cmd)
issue.add_command(move_cmd)
issue.add_command(comment_cmd)
issue.add_command(comments_cmd)
issue.add_command(link_cmd)
issue.add_command(unlink_cmd)
issue.add_command(watch_cmd)
issue.add_command(worklog_cmd)
issue.add_command(worklogs_cmd)
issue.add_command(remote_link_cmd)