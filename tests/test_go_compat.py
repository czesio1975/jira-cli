"""Test Go config file compatibility."""

import pytest
from pathlib import Path
import yaml


class TestGoConfigCompatibility:
    """Test that Python version can read Go jira-cli config."""

    def test_go_config_format(self, tmp_path):
        """Test reading Go jira-cli config format."""
        # This is the exact format written by Go jira-cli
        go_config = {
            "installation": "Cloud",
            "server": "https://example.atlassian.net",
            "login": "user@example.com",
            "project": {
                "key": "PROJ",
                "type": "software",
            },
            "epic": {
                "name": "customfield_10014",
                "link": "customfield_10013",
            },
            "issue": {
                "types": [
                    {"id": "10001", "name": "Bug", "subtask": False},
                    {"id": "10002", "name": "Task", "subtask": False},
                ],
                "fields": {
                    "custom": [
                        {"name": "Story Points", "key": "customfield_10016", "schema": {"datatype": "number"}},
                    ]
                }
            },
            "board": {
                "id": 123,
                "name": "PROJ Board",
                "type": "scrum",
            },
            "auth_type": "basic",
            "timezone": "America/New_York",
            "version": {
                "major": 1,
                "minor": 0,
                "patch": 0,
            },
        }

        config_file = tmp_path / ".config.yml"
        with open(config_file, "w") as f:
            yaml.dump(go_config, f)

        # Load with Python loader
        from jira_cli.internal.cmd.root import load_config

        config = load_config(str(config_file))

        # Verify all fields are read correctly
        assert config["installation"] == "Cloud"
        assert config["server"] == "https://example.atlassian.net"
        assert config["login"] == "user@example.com"
        assert config["project"]["key"] == "PROJ"
        assert config["board"]["name"] == "PROJ Board"
        assert config["auth_type"] == "basic"
        assert config["epic"]["name"] == "customfield_10014"

    def test_go_config_mtls(self, tmp_path):
        """Test reading Go config with mTLS settings."""
        go_config = {
            "installation": "Local",
            "server": "https://jira.example.com",
            "login": "admin",
            "project": {"key": "PROJ"},
            "auth_type": "mtls",
            "mtls": {
                "ca_cert": "/path/to/ca.pem",
                "client_cert": "/path/to/client.pem",
                "client_key": "/path/to/client.key",
            },
        }

        config_file = tmp_path / ".config.yml"
        with open(config_file, "w") as f:
            yaml.dump(go_config, f)

        from jira_cli.internal.cmd.root import load_config

        config = load_config(str(config_file))

        assert config["auth_type"] == "mtls"
        assert config["mtls"]["ca_cert"] == "/path/to/ca.pem"
        assert config["mtls"]["client_cert"] == "/path/to/client.pem"

    def test_go_config_insecure(self, tmp_path):
        """Test reading Go config with insecure flag."""
        go_config = {
            "installation": "Local",
            "server": "https://jira.example.com",
            "login": "admin",
            "project": {"key": "PROJ"},
            "auth_type": "bearer",
            "insecure": True,
        }

        config_file = tmp_path / ".config.yml"
        with open(config_file, "w") as f:
            yaml.dump(go_config, f)

        from jira_cli.internal.cmd.root import load_config

        config = load_config(str(config_file))

        assert config["insecure"] is True

    def test_config_file_location(self):
        """Test that config file location matches Go version."""
        from jira_cli.internal.cmd.root import get_config_path

        path = get_config_path()

        # Go version uses ~/.jira/.config.yml
        assert ".jira" in str(path)
        assert ".config.yml" in str(path)