"""Integration tests with mocked HTTP."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from jira_cli.pkg.jira.client import Client
from jira_cli.pkg.jira.types import AuthType


class TestMockedAPI:
    """Test API calls with mocked HTTP."""

    def test_get_issue_mocked(self):
        """Test getting an issue with mocked response."""
        mock_response = {
            "key": "TEST-123",
            "fields": {
                "summary": "Test issue summary",
                "status": {"name": "In Progress"},
                "priority": {"name": "High"},
                "issueType": {"id": "1", "name": "Bug"},
                "assignee": {"displayName": "John Doe"},
            },
        }

        client = Client(
            server="https://test.atlassian.net",
            login="test@example.com",
            token="test-token",
        )

        # Mock the _request method directly
        with patch.object(client, '_request', return_value=mock_response):
            result = client.get("/issue/TEST-123")

            assert result["key"] == "TEST-123"
            assert result["fields"]["summary"] == "Test issue summary"

    def test_search_issues_mocked(self):
        """Test searching issues with mocked response."""
        mock_response = {
            "issues": [
                {
                    "key": "TEST-1",
                    "fields": {
                        "summary": "First issue",
                        "status": {"name": "Open"},
                        "issueType": {"id": "1", "name": "Bug"},
                    },
                },
                {
                    "key": "TEST-2",
                    "fields": {
                        "summary": "Second issue",
                        "status": {"name": "Done"},
                        "issueType": {"id": "1", "name": "Task"},
                    },
                },
            ],
            "total": 2,
            "startAt": 0,
            "maxResults": 100,
        }

        client = Client(
            server="https://test.atlassian.net",
            login="test@example.com",
            token="test-token",
        )

        with patch.object(client, '_request', return_value=mock_response):
            result = client.search_issues("project = TEST")

            assert len(result.issues) == 2
            assert result.issues[0].key == "TEST-1"
            assert result.issues[1].key == "TEST-2"


class TestCLICommands:
    """Test CLI commands."""

    def test_version_command(self):
        """Test version command."""
        from click.testing import CliRunner
        from jira_cli.internal.cmd.root import root

        runner = CliRunner()
        result = runner.invoke(root, ["--version"])
        assert "1.0.0" in result.output

    def test_help_command(self):
        """Test help command."""
        from click.testing import CliRunner
        from jira_cli.internal.cmd.root import root

        runner = CliRunner()
        result = runner.invoke(root, ["--help"])
        assert "Interactive Jira command line" in result.output
        assert "issue" in result.output
        assert "sprint" in result.output
        assert "board" in result.output

    def test_issue_help(self):
        """Test issue subcommand help."""
        from click.testing import CliRunner
        from jira_cli.internal.cmd.root import root

        runner = CliRunner()
        result = runner.invoke(root, ["issue", "--help"])
        assert "Issue commands" in result.output
        assert "list" in result.output