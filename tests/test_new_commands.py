"""Tests for newly added CLI commands.

Covers: issue link/unlink/watch/worklog/remote-link,
        board get/search, project get/versions,
        release list/create/release, me.

All tests invoke the CLI via CliRunner and assert only on
exit_code and printed output — no internal mock call inspection.
"""

from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from jira_cli.internal.cmd.root import root


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client(**overrides):
    """Create a mock Client with sensible defaults."""
    client = MagicMock()
    client.default_api_version = "v3"
    for k, v in overrides.items():
        setattr(client, k, v)
    return client


def _invoke(*args, config=None):
    """Invoke the CLI with a mocked config."""
    runner = CliRunner()
    cfg = config or {"project": {"key": "TEST"}, "server": "https://x", "login": "u"}
    with patch("jira_cli.internal.cmd.root.load_config", return_value=cfg):
        return runner.invoke(root, list(args), catch_exceptions=False)


# ---------------------------------------------------------------------------
# Help / registration
# ---------------------------------------------------------------------------

class TestHelpRegistration:

    def test_root_help_includes_me_and_release(self):
        result = _invoke("--help")
        assert "me" in result.output
        assert "release" in result.output

    def test_issue_help_includes_new_commands(self):
        result = _invoke("issue", "--help")
        for cmd in ("link", "unlink", "watch", "worklog", "remote-link"):
            assert cmd in result.output, f"{cmd} missing from issue --help"

    def test_board_help_includes_get_search(self):
        result = _invoke("board", "--help")
        assert "get" in result.output
        assert "search" in result.output

    def test_project_help_includes_get_versions(self):
        result = _invoke("project", "--help")
        assert "get" in result.output
        assert "versions" in result.output

    def test_release_help_includes_all(self):
        result = _invoke("release", "--help")
        for cmd in ("list", "create", "release"):
            assert cmd in result.output, f"{cmd} missing from release --help"


# ---------------------------------------------------------------------------
# issue link
# ---------------------------------------------------------------------------

class TestIssueLink:

    @patch("jira_cli.internal.cmd.issue.link.get_client")
    def test_link_success(self, mock_gc):
        mock_gc.return_value = _make_client()
        result = _invoke("issue", "link", "AAA-1", "BBB-2", "--type", "Duplicate")
        assert result.exit_code == 0
        assert "Linked" in result.output
        assert "AAA-1" in result.output
        assert "BBB-2" in result.output
        assert "Duplicate" in result.output

    @patch("jira_cli.internal.cmd.issue.link.get_client")
    def test_link_default_type_shows_blocks(self, mock_gc):
        mock_gc.return_value = _make_client()
        result = _invoke("issue", "link", "AAA-1", "BBB-2")
        assert result.exit_code == 0
        assert "Blocks" in result.output

    @patch("jira_cli.internal.cmd.issue.link.get_client")
    def test_link_api_error(self, mock_gc):
        client = _make_client()
        client.post_v2.side_effect = Exception("server error")
        mock_gc.return_value = client
        result = _invoke("issue", "link", "AAA-1", "BBB-2")
        assert "Error" in result.output
        assert "server error" in result.output


# ---------------------------------------------------------------------------
# issue unlink
# ---------------------------------------------------------------------------

class TestIssueUnlink:

    @patch("jira_cli.internal.cmd.issue.unlink.get_client")
    def test_unlink_success(self, mock_gc):
        client = _make_client()
        client.get.return_value = {
            "key": "AAA-1",
            "fields": {
                "summary": "x",
                "issueType": {"id": "1", "name": "Bug"},
                "issuelinks": [
                    {"id": "999", "outwardIssue": {"key": "BBB-2"}},
                ],
            },
        }
        mock_gc.return_value = client
        result = _invoke("issue", "unlink", "AAA-1", "BBB-2")
        assert result.exit_code == 0
        assert "Unlinked" in result.output
        assert "AAA-1" in result.output
        assert "BBB-2" in result.output

    @patch("jira_cli.internal.cmd.issue.unlink.get_client")
    def test_unlink_no_link_found(self, mock_gc):
        client = _make_client()
        client.get.return_value = {
            "key": "AAA-1",
            "fields": {
                "summary": "x",
                "issueType": {"id": "1", "name": "Bug"},
                "issuelinks": [],
            },
        }
        mock_gc.return_value = client
        result = _invoke("issue", "unlink", "AAA-1", "BBB-2")
        assert "No link found" in result.output

    @patch("jira_cli.internal.cmd.issue.unlink.get_client")
    def test_unlink_api_error(self, mock_gc):
        client = _make_client()
        client.get.side_effect = Exception("boom")
        mock_gc.return_value = client
        result = _invoke("issue", "unlink", "AAA-1", "BBB-2")
        assert "Error" in result.output


# ---------------------------------------------------------------------------
# issue watch
# ---------------------------------------------------------------------------

class TestIssueWatch:

    @patch("jira_cli.internal.cmd.issue.watch.get_client")
    def test_watch_success(self, mock_gc):
        mock_gc.return_value = _make_client()
        result = _invoke("issue", "watch", "AAA-1", "user123")
        assert result.exit_code == 0
        assert "Added user123 as watcher" in result.output
        assert "AAA-1" in result.output

    @patch("jira_cli.internal.cmd.issue.watch.get_client")
    def test_watch_api_error(self, mock_gc):
        client = _make_client()
        client.post_raw.side_effect = Exception("forbidden")
        mock_gc.return_value = client
        result = _invoke("issue", "watch", "AAA-1", "user123")
        assert "Error" in result.output
        assert "forbidden" in result.output


# ---------------------------------------------------------------------------
# issue worklog
# ---------------------------------------------------------------------------

class TestIssueWorklog:

    @patch("jira_cli.internal.cmd.issue.worklog.get_client")
    def test_worklog_basic(self, mock_gc):
        mock_gc.return_value = _make_client()
        result = _invoke("issue", "worklog", "AAA-1", "2h")
        assert result.exit_code == 0
        assert "Logged 2h on AAA-1" in result.output

    @patch("jira_cli.internal.cmd.issue.worklog.get_client")
    def test_worklog_with_comment(self, mock_gc):
        mock_gc.return_value = _make_client()
        result = _invoke("issue", "worklog", "AAA-1", "30m", "-m", "Fixed bug")
        assert result.exit_code == 0
        assert "Logged 30m on AAA-1" in result.output

    @patch("jira_cli.internal.cmd.issue.worklog.get_client")
    def test_worklog_with_started(self, mock_gc):
        mock_gc.return_value = _make_client()
        result = _invoke("issue", "worklog", "AAA-1", "1h", "--started", "2024-01-15T09:00:00.000+0000")
        assert result.exit_code == 0
        assert "Logged 1h on AAA-1" in result.output

    @patch("jira_cli.internal.cmd.issue.worklog.get_client")
    def test_worklog_with_new_estimate(self, mock_gc):
        mock_gc.return_value = _make_client()
        result = _invoke("issue", "worklog", "AAA-1", "1h", "--new-estimate", "2h")
        assert result.exit_code == 0
        assert "Logged 1h on AAA-1" in result.output

    @patch("jira_cli.internal.cmd.issue.worklog.get_client")
    def test_worklog_api_error(self, mock_gc):
        client = _make_client()
        client.post_v2.side_effect = Exception("timeout")
        mock_gc.return_value = client
        result = _invoke("issue", "worklog", "AAA-1", "1h")
        assert "Error" in result.output
        assert "timeout" in result.output


# ---------------------------------------------------------------------------
# issue remote-link
# ---------------------------------------------------------------------------

class TestIssueRemoteLink:

    @patch("jira_cli.internal.cmd.issue.remote_link.get_client")
    def test_remote_link_success(self, mock_gc):
        mock_gc.return_value = _make_client()
        result = _invoke("issue", "remote-link", "AAA-1", "https://example.com", "-t", "Docs")
        assert result.exit_code == 0
        assert "Added remote link" in result.output
        assert "AAA-1" in result.output
        assert "Docs" in result.output

    def test_remote_link_requires_title(self):
        """--title is required; Click should reject the invocation."""
        runner = CliRunner()
        result = runner.invoke(root, ["issue", "remote-link", "AAA-1", "https://example.com"])
        assert result.exit_code != 0

    @patch("jira_cli.internal.cmd.issue.remote_link.get_client")
    def test_remote_link_api_error(self, mock_gc):
        client = _make_client()
        client.post_v2.side_effect = Exception("boom")
        mock_gc.return_value = client
        result = _invoke("issue", "remote-link", "AAA-1", "https://example.com", "-t", "X")
        assert "Error" in result.output


# ---------------------------------------------------------------------------
# board get
# ---------------------------------------------------------------------------

class TestBoardGet:

    @patch("jira_cli.api.client.get_client")
    def test_get_success(self, mock_gc):
        client = _make_client()
        client.get_v1.return_value = {"id": 42, "name": "My Board", "type": "scrum"}
        mock_gc.return_value = client
        result = _invoke("board", "get", "42")
        assert result.exit_code == 0
        assert "My Board" in result.output
        assert "42" in result.output
        assert "scrum" in result.output

    @patch("jira_cli.api.client.get_client")
    def test_get_api_error(self, mock_gc):
        client = _make_client()
        client.get_v1.side_effect = Exception("not found")
        mock_gc.return_value = client
        result = _invoke("board", "get", "999")
        assert "Error" in result.output
        assert "not found" in result.output


# ---------------------------------------------------------------------------
# board search
# ---------------------------------------------------------------------------

class TestBoardSearch:

    @patch("jira_cli.api.client.get_client")
    def test_search_success(self, mock_gc):
        client = _make_client()
        client.get_v1.return_value = {
            "startAt": 0,
            "maxResults": 50,
            "total": 1,
            "isLast": True,
            "values": [{"id": 10, "name": "Sprint Board", "type": "scrum"}],
        }
        mock_gc.return_value = client
        result = _invoke("board", "search", "Sprint")
        assert result.exit_code == 0
        assert "Sprint Board" in result.output

    @patch("jira_cli.api.client.get_client")
    def test_search_no_project(self, mock_gc):
        mock_gc.return_value = _make_client()
        result = _invoke("board", "search", "Sprint", config={"project": {}})
        assert "No project configured" in result.output

    @patch("jira_cli.api.client.get_client")
    def test_search_api_error(self, mock_gc):
        client = _make_client()
        client.get_v1.side_effect = Exception("boom")
        mock_gc.return_value = client
        result = _invoke("board", "search", "Sprint")
        assert "Error" in result.output


# ---------------------------------------------------------------------------
# project get
# ---------------------------------------------------------------------------

class TestProjectGet:

    @patch("jira_cli.api.client.get_client")
    def test_get_success(self, mock_gc):
        client = _make_client()
        client.get_v2.return_value = {
            "key": "TEST",
            "name": "Test Project",
            "style": "classic",
            "lead": {"displayName": "Alice"},
        }
        mock_gc.return_value = client
        result = _invoke("project", "get", "TEST")
        assert result.exit_code == 0
        assert "TEST" in result.output
        assert "Test Project" in result.output
        assert "Alice" in result.output

    @patch("jira_cli.api.client.get_client")
    def test_get_api_error(self, mock_gc):
        client = _make_client()
        client.get_v2.side_effect = Exception("boom")
        mock_gc.return_value = client
        result = _invoke("project", "get", "TEST")
        assert "Error" in result.output


# ---------------------------------------------------------------------------
# project versions
# ---------------------------------------------------------------------------

class TestProjectVersions:

    @patch("jira_cli.api.client.get_client")
    def test_versions_with_arg(self, mock_gc):
        client = _make_client()
        client.get_v2.return_value = [
            {"id": "1", "name": "v1.0", "released": True, "archived": False},
            {"id": "2", "name": "v2.0", "released": False, "archived": False},
        ]
        mock_gc.return_value = client
        result = _invoke("project", "versions", "TEST")
        assert result.exit_code == 0
        assert "v1.0" in result.output
        assert "v2.0" in result.output

    @patch("jira_cli.api.client.get_client")
    def test_versions_uses_config_project(self, mock_gc):
        client = _make_client()
        client.get_v2.return_value = [
            {"id": "1", "name": "v1.0", "released": False, "archived": False},
        ]
        mock_gc.return_value = client
        result = _invoke("project", "versions")
        assert result.exit_code == 0
        assert "v1.0" in result.output

    @patch("jira_cli.api.client.get_client")
    def test_versions_no_project(self, mock_gc):
        mock_gc.return_value = _make_client()
        result = _invoke("project", "versions", config={"project": {}})
        assert "No project specified" in result.output


# ---------------------------------------------------------------------------
# release list
# ---------------------------------------------------------------------------

class TestReleaseList:

    @patch("jira_cli.api.client.get_client")
    def test_list_with_arg(self, mock_gc):
        client = _make_client()
        client.get_v2.return_value = [
            {"id": "10", "name": "v1.0", "released": True, "archived": False, "description": "First"},
        ]
        mock_gc.return_value = client
        result = _invoke("release", "list", "PROJ")
        assert result.exit_code == 0
        assert "v1.0" in result.output
        assert "First" in result.output

    @patch("jira_cli.api.client.get_client")
    def test_list_uses_config_project(self, mock_gc):
        client = _make_client()
        client.get_v2.return_value = []
        mock_gc.return_value = client
        result = _invoke("release", "list")
        assert result.exit_code == 0

    @patch("jira_cli.api.client.get_client")
    def test_list_no_project(self, mock_gc):
        mock_gc.return_value = _make_client()
        result = _invoke("release", "list", config={"project": {}})
        assert "No project specified" in result.output

    @patch("jira_cli.api.client.get_client")
    def test_list_api_error(self, mock_gc):
        client = _make_client()
        client.get_v2.side_effect = Exception("boom")
        mock_gc.return_value = client
        result = _invoke("release", "list", "PROJ")
        assert "Error" in result.output


# ---------------------------------------------------------------------------
# release create
# ---------------------------------------------------------------------------

class TestReleaseCreate:

    def _project_and_version(self, client, version_resp):
        """Set up mock to return project for ID lookup, then version for create."""
        project_resp = {"id": "12345", "key": "TEST", "name": "Test", "projectTypeKey": "software", "lead": {"displayName": "Lead"}}
        client.get_v2.return_value = project_resp
        client.post_v2.return_value = version_resp

    @patch("jira_cli.api.client.get_client")
    def test_create_success(self, mock_gc):
        client = _make_client()
        self._project_and_version(client, {"id": "11", "name": "v2.0", "released": False, "archived": False})
        mock_gc.return_value = client
        result = _invoke("release", "create", "v2.0")
        assert result.exit_code == 0
        assert "Created version" in result.output
        assert "v2.0" in result.output

    @patch("jira_cli.api.client.get_client")
    def test_create_with_all_options(self, mock_gc):
        client = _make_client()
        self._project_and_version(client, {"id": "12", "name": "v3.0", "released": True, "archived": False})
        mock_gc.return_value = client
        result = _invoke(
            "release", "create", "v3.0",
            "-d", "Big release",
            "--release-date", "2024-06-01",
            "--released",
        )
        assert result.exit_code == 0
        assert "Created version" in result.output
        assert "v3.0" in result.output

    @patch("jira_cli.api.client.get_client")
    def test_create_no_project(self, mock_gc):
        mock_gc.return_value = _make_client()
        result = _invoke("release", "create", "v1.0", config={"project": {}})
        assert "No project configured" in result.output

    @patch("jira_cli.api.client.get_client")
    def test_create_api_error(self, mock_gc):
        client = _make_client()
        client.get_v2.return_value = {"id": "12345", "key": "TEST", "name": "Test", "projectTypeKey": "software", "lead": {"displayName": "Lead"}}
        client.post_v2.side_effect = Exception("conflict")
        mock_gc.return_value = client
        result = _invoke("release", "create", "v1.0")
        assert "Error" in result.output
        assert "conflict" in result.output


# ---------------------------------------------------------------------------
# release release
# ---------------------------------------------------------------------------

class TestReleaseRelease:

    @patch("jira_cli.api.client.get_client")
    def test_release_success(self, mock_gc):
        client = _make_client()
        client.put_v2.return_value = {"id": "10", "name": "v1.0", "released": True, "archived": False}
        mock_gc.return_value = client
        result = _invoke("release", "release", "10")
        assert result.exit_code == 0
        assert "Released version" in result.output
        assert "v1.0" in result.output

    @patch("jira_cli.api.client.get_client")
    def test_release_with_date(self, mock_gc):
        client = _make_client()
        client.put_v2.return_value = {"id": "10", "name": "v1.0", "released": True, "archived": False}
        mock_gc.return_value = client
        result = _invoke("release", "release", "10", "--release-date", "2024-06-01")
        assert result.exit_code == 0
        assert "Released version" in result.output

    @patch("jira_cli.api.client.get_client")
    def test_release_api_error(self, mock_gc):
        client = _make_client()
        client.put_v2.side_effect = Exception("not found")
        mock_gc.return_value = client
        result = _invoke("release", "release", "10")
        assert "Error" in result.output
        assert "not found" in result.output


# ---------------------------------------------------------------------------
# me
# ---------------------------------------------------------------------------

class TestMe:

    @patch("jira_cli.internal.cmd.me.get_client")
    def test_me_success(self, mock_gc):
        client = _make_client()
        client.get.return_value = {
            "accountId": "abc123",
            "emailAddress": "alice@example.com",
            "displayName": "Alice Smith",
            "active": True,
            "timeZone": "America/New_York",
            "locale": "en_US",
        }
        mock_gc.return_value = client
        result = _invoke("me")
        assert result.exit_code == 0
        assert "Alice Smith" in result.output
        assert "abc123" in result.output
        assert "alice@example.com" in result.output
        assert "America/New_York" in result.output
        assert "en_US" in result.output

    @patch("jira_cli.internal.cmd.me.get_client")
    def test_me_api_error(self, mock_gc):
        client = _make_client()
        client.get.side_effect = Exception("unauthorized")
        mock_gc.return_value = client
        result = _invoke("me")
        assert "Error" in result.output
        assert "unauthorized" in result.output
