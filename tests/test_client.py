"""Tests for JIRA client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from jira_cli.pkg.jira.client import Client, UnexpectedResponseError
from jira_cli.pkg.jira.types import AuthType, Issue, IssueFields


class TestClient:
    """Test Client class."""

    def test_client_creation_basic(self):
        """Test creating client with basic auth."""
        client = Client(
            server="https://test.atlassian.net",
            login="user@test.com",
            token="test-token",
            auth_type=AuthType.BASIC,
        )
        assert client.server == "https://test.atlassian.net"
        assert client.login == "user@test.com"
        assert client.auth_type == AuthType.BASIC

    def test_client_creation_bearer(self):
        """Test creating client with bearer auth."""
        client = Client(
            server="https://test.atlassian.net",
            login="user@test.com",
            token="test-token",
            auth_type=AuthType.BEARER,
        )
        assert client.auth_type == AuthType.BEARER

    def test_server_trailing_slash_removed(self):
        """Test that trailing slash is removed from server URL."""
        client = Client(
            server="https://test.atlassian.net/",
            login="user@test.com",
            token="test-token",
        )
        assert client.server == "https://test.atlassian.net"


class TestUnexpectedResponseError:
    """Test UnexpectedResponseError."""

    def test_error_formatting(self):
        """Test error message formatting."""
        error = UnexpectedResponseError(
            status_code=400,
            status="Bad Request",
            body={
                "errorMessages": ["Something went wrong"],
                "errors": {"field1": "is required"},
            },
        )
        msg = str(error)
        assert "Something went wrong" in msg
        assert "field1: is required" in msg


class TestTypes:
    """Test Pydantic types."""

    def test_issue_parsing(self):
        """Test parsing issue from JSON."""
        data = {
            "key": "TEST-123",
            "fields": {
                "summary": "Test issue",
                "status": {"name": "Open"},
                "priority": {"name": "High"},
                "issueType": {"id": "1", "name": "Bug"},
            },
        }
        issue = Issue.model_validate(data)
        assert issue.key == "TEST-123"
        assert issue.fields.summary == "Test issue"

    def test_issue_defaults(self):
        """Test issue with minimal data."""
        issue = Issue(key="TEST-1")
        assert issue.key == "TEST-1"
        assert issue.fields.summary == ""

    def test_auth_type_string(self):
        """Test AuthType string conversion."""
        assert str(AuthType.BASIC) == "basic"
        assert str(AuthType.BEARER) == "bearer"


class TestQuery:
    """Test query builder."""

    def test_basic_query(self):
        """Test basic query building."""
        from jira_cli.internal.query.issue import IssueQuery

        query = IssueQuery("TEST")
        jql = query.build()
        assert 'project = "TEST"' in jql

    def test_query_with_filters(self):
        """Test query with filters."""
        from jira_cli.internal.query.issue import IssueQuery

        query = IssueQuery("TEST")
        query.set_type("Bug")
        query.set_status(["Open", "In Progress"])
        query.set_priority("High")

        jql = query.build()
        assert 'issuetype = "Bug"' in jql
        assert 'status in ("Open", "In Progress")' in jql
        assert 'priority = "High"' in jql

    def test_query_with_search(self):
        """Test query with text search."""
        from jira_cli.internal.query.issue import IssueQuery

        query = IssueQuery("TEST")
        query.add_search("important feature")

        jql = query.build()
        assert 'text ~ "important feature"' in jql


class TestADF:
    """Test ADF conversion."""

    def test_adf_to_markdown(self):
        """Test ADF to markdown conversion."""
        from jira_cli.pkg.adf.adf import ADF, adf_to_markdown

        data = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Hello world"}],
                }
            ],
        }
        result = adf_to_markdown(data)
        assert result == "Hello world"

    def test_adf_heading(self):
        """Test ADF heading conversion."""
        from jira_cli.pkg.adf.adf import adf_to_markdown

        data = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": "Title"}],
                }
            ],
        }
        result = adf_to_markdown(data)
        assert "## Title" in result

    def test_text_to_adf(self):
        """Test text to ADF conversion."""
        from jira_cli.pkg.adf.adf import text_to_adf

        result = text_to_adf("Hello world")
        assert result["type"] == "doc"
        assert result["content"][0]["type"] == "paragraph"


class TestMarkdown:
    """Test markdown conversion."""

    def test_to_jira_md_headings(self):
        """Test heading conversion to Jira format."""
        from jira_cli.pkg.jira.markdown import to_jira_md

        assert to_jira_md("# Title") == "h1. Title"
        assert to_jira_md("## Subtitle") == "h2. Subtitle"
        assert to_jira_md("### H3") == "h3. H3"

    def test_to_jira_md_bold_italic(self):
        """Test bold/italic conversion to Jira format."""
        from jira_cli.pkg.jira.markdown import to_jira_md

        # Bold: **text** -> *text*
        assert to_jira_md("**bold text**") == "*bold text*"
        # Italic: *text* -> _text_ (after protecting bold)
        assert to_jira_md("*italic*") == "_italic_"
        # Combined
        result = to_jira_md("**bold** and *italic*")
        assert "*bold*" in result
        assert "_italic_" in result

    def test_to_jira_md_code(self):
        """Test code conversion to Jira format."""
        from jira_cli.pkg.jira.markdown import to_jira_md

        # Inline code
        assert to_jira_md("`code`") == "{{code}}"
        # Code block
        result = to_jira_md("```python\nprint('hello')\n```")
        assert "{code:python}" in result
        assert "print('hello')" in result

    def test_to_jira_md_links(self):
        """Test link conversion to Jira format."""
        from jira_cli.pkg.jira.markdown import to_jira_md

        assert to_jira_md("[text](url)") == "[text|url]"

    def test_to_jira_md_lists(self):
        """Test list conversion to Jira format."""
        from jira_cli.pkg.jira.markdown import to_jira_md

        # Unordered
        assert to_jira_md("- item") == "* item"
        # Ordered
        assert to_jira_md("1. item") == "# item"

    def test_from_jira_md_headings(self):
        """Test heading conversion from Jira format."""
        from jira_cli.pkg.jira.markdown import from_jira_md

        assert from_jira_md("h1. Title") == "# Title"
        assert from_jira_md("h2. Subtitle") == "## Subtitle"

    def test_from_jira_md_bold_italic(self):
        """Test bold/italic conversion from Jira format."""
        from jira_cli.pkg.jira.markdown import from_jira_md

        # Bold: *text* -> **text**
        assert from_jira_md("*bold*") == "**bold**"
        # Italic: _text_ -> *text*
        assert from_jira_md("_italic_") == "*italic*"

    def test_from_jira_md_code(self):
        """Test code conversion from Jira format."""
        from jira_cli.pkg.jira.markdown import from_jira_md

        # Inline code
        assert from_jira_md("{{code}}") == "`code`"
        # Code block
        result = from_jira_md("{code}\nprint('hello')\n{code}")
        assert "```" in result
        assert "print('hello')" in result

    def test_from_jira_md_links(self):
        """Test link conversion from Jira format."""
        from jira_cli.pkg.jira.markdown import from_jira_md

        assert from_jira_md("[text|url]") == "[text](url)"

    def test_from_jira_md_lists(self):
        """Test list conversion from Jira format."""
        from jira_cli.pkg.jira.markdown import from_jira_md

        # Unordered
        assert from_jira_md("* item") == "- item"
        assert from_jira_md("** nested") == "  - nested"
        # Ordered
        assert from_jira_md("# item") == "1. item"

    def test_roundtrip(self):
        """Test that conversions are reversible."""
        from jira_cli.pkg.jira.markdown import to_jira_md, from_jira_md

        # Simple roundtrip
        md = "# Title\n\n**bold** and _italic_"
        jira = to_jira_md(md)
        back = from_jira_md(jira)
        assert "#" in back
        assert "**" in back or "*" in back


class TestConfig:
    """Test config loading."""

    def test_config_path(self, tmp_path):
        """Test config path resolution."""
        from jira_cli.internal.cmd.root import get_config_path

        # This uses the default path
        path = get_config_path()
        assert ".jira" in str(path)
        assert ".config.yml" in str(path)

    def test_load_config(self, tmp_path):
        """Test loading config from file."""
        import yaml

        config_file = tmp_path / ".config.yml"
        config_data = {
            "server": "https://test.atlassian.net",
            "login": "test@example.com",
            "project": {"key": "TEST"},
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        from jira_cli.internal.cmd.root import load_config

        config = load_config(str(config_file))
        assert config["server"] == "https://test.atlassian.net"
        assert config["project"]["key"] == "TEST"