# jira-cli

A command-line interface for Jira. Designed for automation, scripting, and AI agent workflows.

Supports both Jira Cloud and Jira Server/Data Center installations.

## Installation

```bash
git clone <repo-url> && cd jira-cli
python -m venv .venv
.venv/bin/pip install -e .
```

### Optional: Keyring Support

For secure credential storage in the system keyring:

```bash
.venv/bin/pip install -e ".[keyring]"
```

## Configuration

The CLI reads configuration from `~/.jira/.config.yml` (or `%USERPROFILE%\.jira\.config.yml` on Windows). Run the interactive setup or create the file manually.

### Interactive Setup

```bash
jira init
```

### Configuration File

```yaml
# ~/.jira/.config.yml
# Jira server URL
server: https://your-company.atlassian.net

# Login identifier (email for Cloud, username for Server/Data Center)
login: your-email@example.com

# API token or password (optional - can use env var, keyring, or netrc instead)
api_token: your-api-token-here

# Authentication type: basic, bearer, or mtls
#   basic  - Jira Server/Data Center with username + token/password
#   bearer - Jira Cloud with personal access token (PAT)
#   mtls   - Mutual TLS with client certificates
auth_type: basic

# Installation type: Cloud or Local
#   Cloud - Jira Cloud (uses API v3, ADF format)
#   Local - Jira Server/Data Center (uses API v2, plain text)
installation: Cloud

# Default project key (can be overridden with -p flag)
project:
  key: MYPROJECT

# Skip TLS certificate verification (for self-signed certs)
# insecure: false

# mTLS configuration (only when auth_type: mtls)
# mtls:
#   ca_cert: /path/to/ca.pem
#   client_cert: /path/to/client.pem
#   client_key: /path/to/client.key
```

### Authentication Methods

The tool looks for credentials in this order:

1. `JIRA_API_TOKEN` environment variable
2. `api_token` field in config file
3. System keyring (requires `pip install -e ".[keyring]"`)
4. `~/.netrc` file (`~/_netrc` on Windows)

| Type | Use Case |
|------|----------|
| `basic` | Jira Server/Data Center with username + API token or password |
| `bearer` | Jira Cloud with personal access token |
| `mtls` | Mutual TLS with client certificates |

### Configuration Locations

| Platform | Default Config Path |
|----------|---------------------|
| Linux/macOS | `~/.jira/.config.yml` |
| Windows | `%USERPROFILE%\.jira\.config.yml` |

Override with `-c` flag or `JIRA_CONFIG_FILE` environment variable.

### Multiple Projects

Override the project per command with `-p`:

```bash
jira -p OTHER issue list
```

Or load a different config file:

```bash
jira -c /path/to/other-config.yml issue list
```

## Usage

```
jira [global-options] <command> [command-options]
```

### Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--config PATH` | `-c` | Config file path (overrides default) |
| `--project TEXT` | `-p` | Project key (overrides config) |
| `--debug` | | Enable debug output |
| `--version` | | Show version |
| `--help` | | Show help |

---

## Commands

### me

Show current authenticated user info.

```bash
jira me
```

Output includes display name, account ID, email, active status, timezone, and locale.

---

### issue list

List and search issues in a project.

```bash
jira issue list [SEARCH_QUERY] [options]
```

Alias: `jira issue ls`

| Option | Short | Description |
|--------|-------|-------------|
| `--type TEXT` | `-t` | Filter by issue type (Bug, Task, Story, Epic, etc.) |
| `--status TEXT` | `-s` | Filter by status (repeatable for multiple) |
| `--priority TEXT` | `-y` | Filter by priority |
| `--reporter TEXT` | `-r` | Filter by reporter username |
| `--assignee TEXT` | `-a` | Filter by assignee username |
| `--label TEXT` | `-l` | Filter by label (repeatable) |
| `--jql TEXT` | `-q` | Custom JQL (appended to filters) |
| `--raw` | | Output raw JSON instead of table |
| `--paginate TEXT` | | Pagination as `from:limit` (default `0:100`) |

**Examples:**

```bash
# List all issues
jira -p NTA issue list

# Filter by assignee and type
jira -p NTA issue list -a damianp -t Bug

# Multiple status filters
jira -p NTA issue list -s Open -s "In Progress"

# Text search
jira -p NTA issue list "login error"

# Custom JQL
jira -p NTA issue list --jql "priority = High AND status != Done"

# First 5 results as JSON
jira -p NTA issue list --paginate 0:5 --raw

# Combined filters
jira -p NTA issue list -a damianp -t Task -y Normal --paginate 0:10
```

---

### issue view

View details of a single issue.

```bash
jira issue view ISSUE_KEY [--raw]
```

| Option | Description |
|--------|-------------|
| `--raw` | Output raw JSON |

Displays: key, summary, type, status, priority, assignee, reporter, labels, components, fix versions, parent (for sub-tasks), created/updated dates, description, sub-tasks, and issue links.

```bash
jira -p NTA issue view NTA-123
jira -p NTA issue view NTA-123 --raw
```

---

### issue comments

List all comments on an issue.

```bash
jira issue comments ISSUE_KEY
```

Displays author, date, and comment body for each comment.

```bash
jira -p NTA issue comments NTA-123
```

---

### issue worklogs

List all worklog entries on an issue.

```bash
jira issue worklogs ISSUE_KEY [--raw]
```

| Option | Description |
|--------|-------------|
| `--raw` | Output raw JSON |

Displays author, time spent, date, and comment for each worklog entry, plus total time.

```bash
jira -p NTA issue worklogs NTA-123
jira -p NTA issue worklogs NTA-123 --raw
```

---

### issue create

Create a new issue.

```bash
jira issue create SUMMARY [options]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--type TEXT` | `-t` | Issue type (default: Task) |
| `--description TEXT` | `-d` | Issue description |
| `--assignee TEXT` | `-a` | Assignee username or account ID |
| `--priority TEXT` | `-y` | Priority name |
| `--label TEXT` | `-l` | Labels (repeatable) |
| `--component TEXT` | `-C` | Components (repeatable) |
| `--parent TEXT` | | Parent issue key (for sub-tasks) |

**Examples:**

```bash
# Simple task (default type)
jira -p NTA issue create "Fix login page"

# Bug with description
jira -p NTA issue create "Crash on startup" -t Bug -d "App crashes on open"

# Story assigned to user
jira -p NTA issue create "User dashboard" -t Story -a damianp

# Sub-task under a parent
jira -p NTA issue create "Write tests" -t Sub-task --parent NTA-123

# Task with labels and priority
jira -p NTA issue create "Update docs" -l documentation -l urgent -y Normal

# Improvement
jira -p NTA issue create "Optimize queries" -t Improvement -d "Reduce DB load"
```

---

### issue edit

Edit an existing issue.

```bash
jira issue edit ISSUE_KEY [options]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--summary TEXT` | `-s` | New summary |
| `--description TEXT` | `-d` | New description |
| `--priority TEXT` | `-y` | New priority |
| `--assignee TEXT` | `-a` | New assignee |
| `--label TEXT` | `-l` | Set labels (replaces existing, repeatable) |
| `--component TEXT` | `-C` | Set components (replaces existing, repeatable) |

**Examples:**

```bash
jira -p NTA issue edit NTA-123 -s "Updated title"
jira -p NTA issue edit NTA-123 -y Minor -d "New description"
jira -p NTA issue edit NTA-123 -s "New title" -d "New desc" -y Normal
```

---

### issue delete

Delete an issue.

```bash
jira issue delete ISSUE_KEY [options]
```

| Option | Description |
|--------|-------------|
| `--cascade` | Also delete sub-tasks |
| `--yes` | Skip confirmation prompt |

```bash
jira -p NTA issue delete NTA-123 --yes
jira -p NTA issue delete NTA-123 --cascade --yes
```

---

### issue assign

Assign or unassign an issue.

```bash
jira issue assign ISSUE_KEY ASSIGNEE
```

`ASSIGNEE` can be a username, account ID, `none` (unassign), or `default`.

```bash
jira -p NTA issue assign NTA-123 damianp
jira -p NTA issue assign NTA-123 none
```

---

### issue move

Transition an issue to a new status.

```bash
jira issue move ISSUE_KEY [STATUS]
```

If `STATUS` is omitted, lists available transitions. Matching is case-insensitive.

```bash
# List available transitions
jira -p NTA issue move NTA-123

# Move to a status
jira -p NTA issue move NTA-123 "Start Progress"
jira -p NTA issue move NTA-123 "Resolve Issue"
jira -p NTA issue move NTA-123 "Close Issue"
```

---

### issue comment

Add a comment to an issue.

```bash
jira issue comment ISSUE_KEY BODY [options]
```

| Option | Description |
|--------|-------------|
| `--internal` | Mark as internal comment (Jira Service Desk) |

```bash
jira -p NTA issue comment NTA-123 "Fixed in commit abc123"
jira -p NTA issue comment NTA-123 "Internal note" --internal
```

---

### issue link

Link two issues together.

```bash
jira issue link INWARD_ISSUE OUTWARD_ISSUE [options]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--type TEXT` | `-t` | Link type (default: `Blocks`) |

Common link types: `Blocks`, `Relates`, `Duplicate`, `Cloners`.

```bash
# NTA-100 blocks NTA-200
jira -p NTA issue link NTA-100 NTA-200

# Relates
jira -p NTA issue link NTA-100 NTA-200 -t Relates

# Duplicate
jira -p NTA issue link NTA-100 NTA-200 -t Duplicate
```

---

### issue unlink

Remove a link between two issues. The link ID is resolved automatically.

```bash
jira issue unlink ISSUE_KEY OTHER_ISSUE
```

```bash
jira -p NTA issue unlink NTA-100 NTA-200
```

---

### issue watch

Add a watcher to an issue.

```bash
jira issue watch ISSUE_KEY WATCHER
```

```bash
jira -p NTA issue watch NTA-123 damianp
```

---

### issue worklog

Add a worklog entry to an issue.

```bash
jira issue worklog ISSUE_KEY TIME_SPENT [options]
```

`TIME_SPENT` uses Jira duration format: `30m`, `1h`, `2h 30m`, `1d`.

| Option | Short | Description |
|--------|-------|-------------|
| `--comment TEXT` | `-m` | Worklog comment |
| `--started TEXT` | | Start time (e.g. `2024-01-15T09:00:00.000+0000`) |
| `--new-estimate TEXT` | | New remaining estimate (e.g. `2h`) |

```bash
jira -p NTA issue worklog NTA-123 30m
jira -p NTA issue worklog NTA-123 2h -m "Code review"
jira -p NTA issue worklog NTA-123 1h --new-estimate 4h
```

---

### issue remote-link

Add an external URL link to an issue.

```bash
jira issue remote-link ISSUE_KEY URL --title TEXT
```

| Option | Short | Description |
|--------|-------|-------------|
| `--title TEXT` | `-t` | Link title (required) |

```bash
jira -p NTA issue remote-link NTA-123 "https://github.com/org/repo/pull/42" -t "PR #42"
```

---

### epic list

List epics in a project.

```bash
jira -p NTA epic list
```

---

### sprint list

List sprints across all boards in the project.

```bash
jira -p NTA sprint list
```

### sprint create

Create a new sprint on a board.

```bash
jira sprint create NAME --board-id ID [--start-date DATE] [--end-date DATE]
```

```bash
jira sprint create "Sprint 42" --board-id 51301
jira sprint create "Sprint 43" --board-id 51301 --start-date 2026-04-07 --end-date 2026-04-21
```

### sprint start / close

```bash
jira sprint start SPRINT_ID
jira sprint close SPRINT_ID
```

---

### board list

List boards in the project.

```bash
jira -p NTA board list
```

### board get

Get a board by ID.

```bash
jira board get 51301
```

### board search

Search boards by name.

```bash
jira -p NTA board search "BATS"
```

---

### project list

List all accessible projects.

```bash
jira project list
```

### project get

Get project details.

```bash
jira project get NTA
```

### project versions

List versions for a project. Uses the configured project if omitted.

```bash
jira project versions NTA
jira -p NTA project versions
```

---

### release list

List all versions/releases for a project.

```bash
jira release list NTA
jira -p NTA release list
```

### release create

Create a new version.

```bash
jira release create NAME [options]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--description TEXT` | `-d` | Version description |
| `--release-date TEXT` | | Release date (`YYYY-MM-DD`) |
| `--released` | | Mark as already released |

```bash
jira -p NTA release create "v2.0"
jira -p NTA release create "v2.1" -d "Bug fixes" --release-date 2026-06-01
jira -p NTA release create "v1.9" --released --release-date 2026-01-01
```

### release release

Release a version by ID.

```bash
jira release release VERSION_ID [--release-date YYYY-MM-DD]
```

```bash
jira release release 628280
jira release release 628280 --release-date 2026-04-04
```

---

## API Version Handling

The CLI automatically selects the correct API version based on your `installation` setting:

| Installation | API | Notes |
|-------------|-----|-------|
| `Cloud` | v3 (`/rest/api/3`) | Uses ADF for rich text |
| `Local` | v2 (`/rest/api/2`) | Uses plain text / wiki markup |

Agile endpoints (boards, sprints) always use v1 (`/rest/agile/1.0`).

## Testing

```bash
# Unit tests (mocked, no server needed)
.venv/bin/python -m pytest tests/ -v

# Live integration tests (requires configured Jira server)
./tests/live_test.sh
```

The live test suite creates temporary issues (Task, Bug, Story, Improvement, Sub-task), exercises every command and option, then cleans up all created resources.

## License

MIT
