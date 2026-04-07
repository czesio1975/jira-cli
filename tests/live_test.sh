#!/usr/bin/env bash
#
# Live integration test script for jira-cli
# Tests all CLI commands against a real Jira server.
#
# Usage:  ./tests/live_test.sh
# Config: Uses ~/.jira/.config.yml (project NTA, user damianp)
#
# The script creates test issues of various types, exercises every
# command and parameter combination, then cleans up after itself.

set -uo pipefail

# ── Configuration ───────────────────────────────────────────────────
PROJECT="NTA"
USER="damianp"
CLI=".venv/bin/python -m jira_cli"

TS=$(date +%s)

# Counters
PASS=0
FAIL=0
TOTAL=0

# Resources to clean up (space-separated issue keys)
CLEANUP_ISSUES=""
CLEANUP_VERSION_IDS=""

# IDs captured during tests
TASK_KEY=""
BUG_KEY=""
STORY_KEY=""
IMPROVEMENT_KEY=""
SUBTASK_KEY=""
BOARD_ID=""
VERSION_ID=""
SPRINT_ID=""

# ── Helpers ─────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

run_test() {
    local name="$1"
    shift
    local expect_success="${1:-true}"
    shift

    TOTAL=$((TOTAL + 1))
    echo -e "\n${CYAN}[$TOTAL] $name${NC}"
    echo "  CMD: $*"

    set +e
    OUTPUT=$("$@" 2>&1)
    EXIT_CODE=$?
    set -e

    if [ "$expect_success" = "true" ]; then
        if [ $EXIT_CODE -eq 0 ] && ! echo "$OUTPUT" | strip_ansi | grep -q "^Error:"; then
            echo -e "  ${GREEN}PASS${NC} (exit $EXIT_CODE)"
            PASS=$((PASS + 1))
        else
            echo -e "  ${RED}FAIL${NC} (exit $EXIT_CODE)"
            echo "  OUTPUT: $OUTPUT"
            FAIL=$((FAIL + 1))
        fi
    else
        if [ $EXIT_CODE -ne 0 ] || echo "$OUTPUT" | strip_ansi | grep -qi "error\|no transition\|no link\|no project\|not found"; then
            echo -e "  ${GREEN}PASS${NC} (expected failure, exit $EXIT_CODE)"
            PASS=$((PASS + 1))
        else
            echo -e "  ${RED}FAIL${NC} (expected failure but got exit $EXIT_CODE)"
            echo "  OUTPUT: $OUTPUT"
            FAIL=$((FAIL + 1))
        fi
    fi

    echo "  OUTPUT: ${OUTPUT:0:300}"
    return 0
}

# run_capture: like run_test but stores OUTPUT for later extraction
run_capture() {
    local name="$1"
    shift

    TOTAL=$((TOTAL + 1))
    echo -e "\n${CYAN}[$TOTAL] $name${NC}"
    echo "  CMD: $*"

    set +e
    OUTPUT=$("$@" 2>&1)
    EXIT_CODE=$?
    set -e

    if [ $EXIT_CODE -eq 0 ] && ! echo "$OUTPUT" | grep -q "^Error:"; then
        echo -e "  ${GREEN}PASS${NC} (exit $EXIT_CODE)"
        PASS=$((PASS + 1))
    else
        echo -e "  ${RED}FAIL${NC} (exit $EXIT_CODE)"
        FAIL=$((FAIL + 1))
    fi
    echo "  OUTPUT: ${OUTPUT:0:300}"
    return 0
}

strip_ansi() {
    # Remove all ANSI/VT escape sequences for clean grep matching
    perl -pe 's/\e\[[0-9;]*[a-zA-Z]//g; s/\e\].*?\a//g; s/\e\[.*?m//g'
}

assert_contains() {
    local name="$1"
    local needle="$2"

    TOTAL=$((TOTAL + 1))
    if grep -qiP "$needle" <<< "$(strip_ansi <<< "$OUTPUT")"; then
        echo -e "  ${GREEN}PASS${NC} - $name (contains '$needle')"
        PASS=$((PASS + 1))
    else
        echo -e "  ${RED}FAIL${NC} - $name (missing '$needle')"
        FAIL=$((FAIL + 1))
    fi
    return 0
}

assert_not_contains() {
    local name="$1"
    local needle="$2"

    TOTAL=$((TOTAL + 1))
    if grep -qiP "$needle" <<< "$(strip_ansi <<< "$OUTPUT")"; then
        echo -e "  ${RED}FAIL${NC} - $name (should not contain '$needle')"
        FAIL=$((FAIL + 1))
    else
        echo -e "  ${GREEN}PASS${NC} - $name (correctly missing '$needle')"
        PASS=$((PASS + 1))
    fi
    return 0
}

extract_key() {
    echo "$1" | grep -oP "${PROJECT}-\d+" | head -1 || true
}

extract_id() {
    echo "$1" | grep -oP 'ID:\s*\K\d+' | head -1 || true
}

track_issue() {
    [ -n "$1" ] && CLEANUP_ISSUES="$CLEANUP_ISSUES $1"
}

track_version() {
    [ -n "$1" ] && CLEANUP_VERSION_IDS="$CLEANUP_VERSION_IDS $1"
}

cleanup() {
    echo -e "\n${YELLOW}── Cleanup ───────────────────────────────────────────${NC}"
    for key in $CLEANUP_ISSUES; do
        echo "  Deleting $key..."
        $CLI -p "$PROJECT" issue delete "$key" --yes 2>/dev/null || true
    done
    echo "  Cleanup done."
}

trap cleanup EXIT

# ── Start ───────────────────────────────────────────────────────────
echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  jira-cli Live Integration Tests${NC}"
echo -e "${BOLD}  Project: $PROJECT  |  User: $USER  |  TS: $TS${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"


# ════════════════════════════════════════════════════════════════════
# 1. HELP & VERSION
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 1. Help & Version ──────────────────────────────────${NC}"

run_capture "root --help" $CLI --help
assert_contains "root help lists commands" "issue"
assert_contains "root help lists me" "me"
assert_contains "root help lists release" "release"

run_capture "root --version" $CLI --version
assert_contains "version string" "version"

run_test "issue --help" true $CLI issue --help
run_test "issue list --help" true $CLI issue list --help
run_test "issue create --help" true $CLI issue create --help
run_test "issue edit --help" true $CLI issue edit --help
run_test "issue delete --help" true $CLI issue delete --help
run_test "issue assign --help" true $CLI issue assign --help
run_test "issue move --help" true $CLI issue move --help
run_test "issue comment --help" true $CLI issue comment --help
run_test "issue link --help" true $CLI issue link --help
run_test "issue unlink --help" true $CLI issue unlink --help
run_test "issue watch --help" true $CLI issue watch --help
run_test "issue worklog --help" true $CLI issue worklog --help
run_test "issue remote-link --help" true $CLI issue remote-link --help
run_test "board --help" true $CLI board --help
run_test "sprint --help" true $CLI sprint --help
run_test "project --help" true $CLI project --help
run_test "release --help" true $CLI release --help
run_test "epic --help" true $CLI epic --help


# ════════════════════════════════════════════════════════════════════
# 2. ME
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 2. Me ─────────────────────────────────────────────${NC}"

run_capture "me" $CLI me
assert_contains "me: account id" "account id"
assert_contains "me: email" "email"
assert_contains "me: active" "active"
assert_contains "me: timezone" "timezone"


# ════════════════════════════════════════════════════════════════════
# 3. PROJECT
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 3. Project ─────────────────────────────────────────${NC}"

run_capture "project list" $CLI project list
assert_contains "project list shows projects" "Fetching"

run_capture "project get $PROJECT" $CLI project get "$PROJECT"
assert_contains "project get: key" "$PROJECT"
assert_contains "project get: type" "software"
assert_contains "project get: lead" "Lead"

run_test "project versions (explicit)" true $CLI project versions "$PROJECT"
run_test "project versions (config)" true $CLI -p "$PROJECT" project versions
run_test "project get - invalid" false $CLI project get "ZZZBOGUS999"


# ════════════════════════════════════════════════════════════════════
# 4. BOARD
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 4. Board ───────────────────────────────────────────${NC}"

run_capture "board list" $CLI -p "$PROJECT" board list
BOARD_ID=$(echo "$OUTPUT" | grep -oP '\d{4,}' | head -1 || true)
echo "  Extracted board ID: ${BOARD_ID:-<none>}"

if [ -n "$BOARD_ID" ]; then
    run_capture "board get $BOARD_ID" $CLI board get "$BOARD_ID"
    assert_contains "board get: ID" "$BOARD_ID"

    run_test "board search" true $CLI -p "$PROJECT" board search "BATS"
fi

run_test "board get - invalid" false $CLI board get 999999
run_test "board get - missing arg" false $CLI board get


# ════════════════════════════════════════════════════════════════════
# 5. ISSUE LIST (read-only)
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 5. Issue List ──────────────────────────────────────${NC}"

run_test "issue list (default)" true $CLI -p "$PROJECT" issue list
run_test "issue ls (alias)" true $CLI -p "$PROJECT" issue ls
run_test "issue list --paginate 0:3" true $CLI -p "$PROJECT" issue list --paginate "0:3"
run_test "issue list -a assignee" true $CLI -p "$PROJECT" issue list -a "$USER"
run_test "issue list -t Bug" true $CLI -p "$PROJECT" issue list -t "Bug"
run_test "issue list -t Story" true $CLI -p "$PROJECT" issue list -t "Story"
run_test "issue list -t Task" true $CLI -p "$PROJECT" issue list -t "Task"
run_test "issue list -t Improvement" true $CLI -p "$PROJECT" issue list -t "Improvement"
run_test "issue list -s Open" true $CLI -p "$PROJECT" issue list -s "Open"
run_test "issue list -s Resolved" true $CLI -p "$PROJECT" issue list -s "Resolved"
run_test "issue list multi-status" true $CLI -p "$PROJECT" issue list -s "Open" -s "Resolved"
run_test "issue list -y Normal" true $CLI -p "$PROJECT" issue list -y "Normal"
run_test "issue list -r reporter" true $CLI -p "$PROJECT" issue list -r "$USER"
run_test "issue list --raw JSON" true $CLI -p "$PROJECT" issue list --paginate "0:2" --raw
run_test "issue list text search" true $CLI -p "$PROJECT" issue list "test"
run_test "issue list --jql" true $CLI -p "$PROJECT" issue list --jql "status != Done"
run_test "issue list combined" true $CLI -p "$PROJECT" issue list -a "$USER" -t "Task" --paginate "0:5"
run_test "issue list config default project" true $CLI issue list


# ════════════════════════════════════════════════════════════════════
# 6. EPIC LIST
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 6. Epic List ───────────────────────────────────────${NC}"

run_capture "epic list" $CLI -p "$PROJECT" epic list
assert_contains "epic list shows epics" "Epic"


# ════════════════════════════════════════════════════════════════════
# 7. SPRINT LIST
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 7. Sprint List ─────────────────────────────────────${NC}"

run_test "sprint list" true $CLI -p "$PROJECT" sprint list


# ════════════════════════════════════════════════════════════════════
# 8. RELEASE LIST
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 8. Release List ────────────────────────────────────${NC}"

run_test "release list (explicit)" true $CLI release list "$PROJECT"
run_test "release list (config)" true $CLI -p "$PROJECT" release list


# ════════════════════════════════════════════════════════════════════
# 9. ISSUE CREATE — multiple types
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 9. Issue Create ────────────────────────────────────${NC}"

# 9a. Task (default type)
run_capture "create Task (default type)" $CLI -p "$PROJECT" issue create "Test Task $TS"
TASK_KEY=$(extract_key "$OUTPUT")
track_issue "$TASK_KEY"
assert_contains "create Task: key" "Created"
echo "  -> TASK_KEY=$TASK_KEY"

if [ -z "$TASK_KEY" ]; then
    echo -e "${RED}FATAL: Could not create test issue. Aborting.${NC}"
    echo -e "\n${BOLD}  Results: $PASS passed, $FAIL failed, $TOTAL total${NC}"
    exit 1
fi

# 9b. Bug
run_capture "create Bug" $CLI -p "$PROJECT" issue create "Test Bug $TS" -t "Bug" -d "Bug description for live test"
BUG_KEY=$(extract_key "$OUTPUT")
track_issue "$BUG_KEY"
assert_contains "create Bug: key" "Created"
echo "  -> BUG_KEY=$BUG_KEY"

# 9c. Story
run_capture "create Story" $CLI -p "$PROJECT" issue create "Test Story $TS" -t "Story"
STORY_KEY=$(extract_key "$OUTPUT")
track_issue "$STORY_KEY"
assert_contains "create Story: key" "Created"
echo "  -> STORY_KEY=$STORY_KEY"

# 9d. Improvement
run_capture "create Improvement" $CLI -p "$PROJECT" issue create "Test Improvement $TS" -t "Improvement" -d "Improvement desc"
IMPROVEMENT_KEY=$(extract_key "$OUTPUT")
track_issue "$IMPROVEMENT_KEY"
assert_contains "create Improvement: key" "Created"
echo "  -> IMPROVEMENT_KEY=$IMPROVEMENT_KEY"

# 9e. Task with all options
run_capture "create Task with all options" \
    $CLI -p "$PROJECT" issue create "Test Full Task $TS" \
        -t "Task" \
        -d "Full description" \
        -a "$USER" \
        -y "Normal" \
        -l "test-label"
FULL_KEY=$(extract_key "$OUTPUT")
track_issue "$FULL_KEY"
assert_contains "create full: key" "Created"
echo "  -> FULL_KEY=$FULL_KEY"

# 9f. Sub-task (child of TASK_KEY)
run_capture "create Sub-task" \
    $CLI -p "$PROJECT" issue create "Test Sub-task $TS" -t "Sub-task" --parent "$TASK_KEY"
SUBTASK_KEY=$(extract_key "$OUTPUT")
track_issue "$SUBTASK_KEY"
assert_contains "create Sub-task: key" "Created"
echo "  -> SUBTASK_KEY=$SUBTASK_KEY"

# 9g. Error: missing summary
run_test "create - missing summary" false $CLI -p "$PROJECT" issue create


# ════════════════════════════════════════════════════════════════════
# 10. ISSUE EDIT
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 10. Issue Edit ─────────────────────────────────────${NC}"

run_test "edit summary" true \
    $CLI -p "$PROJECT" issue edit "$TASK_KEY" -s "Edited Task Summary $TS"

run_test "edit description" true \
    $CLI -p "$PROJECT" issue edit "$TASK_KEY" -d "Edited description $TS"

run_test "edit priority" true \
    $CLI -p "$PROJECT" issue edit "$TASK_KEY" -y "Minor"

run_test "edit assignee" true \
    $CLI -p "$PROJECT" issue edit "$TASK_KEY" -a "$USER"

run_test "edit Bug summary" true \
    $CLI -p "$PROJECT" issue edit "$BUG_KEY" -s "Edited Bug $TS"

run_test "edit multiple fields at once" true \
    $CLI -p "$PROJECT" issue edit "$STORY_KEY" -s "Edited Story $TS" -d "New story desc" -y "Normal"

run_test "edit - invalid key" false \
    $CLI -p "$PROJECT" issue edit "INVALID-99999" -s "nope"


# ════════════════════════════════════════════════════════════════════
# 11. ISSUE ASSIGN
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 11. Issue Assign ───────────────────────────────────${NC}"

run_capture "assign to user" $CLI -p "$PROJECT" issue assign "$TASK_KEY" "$USER"
assert_contains "assign: confirms user" "$USER"

run_capture "unassign (none)" $CLI -p "$PROJECT" issue assign "$TASK_KEY" "none"
assert_contains "unassign: confirms" "Unassigned"

run_test "assign back" true $CLI -p "$PROJECT" issue assign "$TASK_KEY" "$USER"

run_test "assign Bug" true $CLI -p "$PROJECT" issue assign "$BUG_KEY" "$USER"

run_test "assign - missing args" false $CLI -p "$PROJECT" issue assign


# ════════════════════════════════════════════════════════════════════
# 12. ISSUE MOVE (Transitions)
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 12. Issue Move ─────────────────────────────────────${NC}"

# List transitions
run_capture "move: list transitions" $CLI -p "$PROJECT" issue move "$TASK_KEY"
assert_contains "transitions: has names" "Start Progress|Resolve|Close"

# Move Task: Open -> In Progress
run_capture "move Task to Start Progress" $CLI -p "$PROJECT" issue move "$TASK_KEY" "Start Progress"
assert_contains "move: confirms" "Moved"

# Move Bug: Open -> In Progress
run_capture "move Bug to Start Progress" $CLI -p "$PROJECT" issue move "$BUG_KEY" "Start Progress"
assert_contains "move Bug: confirms" "Moved"

# Move Story
run_test "move Story to Start Progress" true $CLI -p "$PROJECT" issue move "$STORY_KEY" "Start Progress"

# Invalid transition
run_capture "move - invalid status" $CLI -p "$PROJECT" issue move "$TASK_KEY" "NonExistentStatus"
assert_contains "move invalid: shows available" "No transition"


# ════════════════════════════════════════════════════════════════════
# 13. ISSUE COMMENT
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 13. Issue Comment ──────────────────────────────────${NC}"

run_capture "comment on Task" \
    $CLI -p "$PROJECT" issue comment "$TASK_KEY" "Test comment on Task $TS"
assert_contains "comment: confirms" "Comment added"

run_test "comment on Bug" true \
    $CLI -p "$PROJECT" issue comment "$BUG_KEY" "Test comment on Bug $TS"

run_test "comment on Story" true \
    $CLI -p "$PROJECT" issue comment "$STORY_KEY" "Test comment on Story $TS"

run_test "comment - missing body" false $CLI -p "$PROJECT" issue comment "$TASK_KEY"


# ════════════════════════════════════════════════════════════════════
# 14. ISSUE LINK / UNLINK
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 14. Issue Link / Unlink ────────────────────────────${NC}"

# Link Task -> Bug with Relates
run_capture "link Task-Bug (Relates)" \
    $CLI -p "$PROJECT" issue link "$TASK_KEY" "$BUG_KEY" -t "Relates"
assert_contains "link Relates: confirms" "Linked"
sleep 1

run_capture "unlink Task-Bug" \
    $CLI -p "$PROJECT" issue unlink "$TASK_KEY" "$BUG_KEY"
assert_contains "unlink: confirms" "Unlinked"

# Link with default type (Blocks)
run_capture "link Task-Story (Blocks default)" \
    $CLI -p "$PROJECT" issue link "$TASK_KEY" "$STORY_KEY"
assert_contains "link Blocks: confirms" "Blocks"
sleep 1

run_test "unlink Task-Story" true \
    $CLI -p "$PROJECT" issue unlink "$TASK_KEY" "$STORY_KEY"

# Link Bug -> Improvement with Duplicate
run_capture "link Bug-Improvement (Duplicate)" \
    $CLI -p "$PROJECT" issue link "$BUG_KEY" "$IMPROVEMENT_KEY" -t "Duplicate"
assert_contains "link Duplicate: confirms" "Duplicate"
sleep 1

run_test "unlink Bug-Improvement" true \
    $CLI -p "$PROJECT" issue unlink "$BUG_KEY" "$IMPROVEMENT_KEY"

# Unlink when no link exists
run_capture "unlink - no link" \
    $CLI -p "$PROJECT" issue unlink "$TASK_KEY" "$IMPROVEMENT_KEY"
assert_contains "unlink no link: message" "No link found"


# ════════════════════════════════════════════════════════════════════
# 15. ISSUE WATCH
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 15. Issue Watch ────────────────────────────────────${NC}"

run_capture "watch Task" $CLI -p "$PROJECT" issue watch "$TASK_KEY" "$USER"
assert_contains "watch: confirms" "Added"

run_test "watch Bug" true $CLI -p "$PROJECT" issue watch "$BUG_KEY" "$USER"


# ════════════════════════════════════════════════════════════════════
# 16. ISSUE WORKLOG
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 16. Issue Worklog ──────────────────────────────────${NC}"

run_capture "worklog 30m" $CLI -p "$PROJECT" issue worklog "$TASK_KEY" "30m"
assert_contains "worklog basic: confirms" "Logged 30m"

run_capture "worklog 1h with comment" \
    $CLI -p "$PROJECT" issue worklog "$TASK_KEY" "1h" -m "Test worklog comment"
assert_contains "worklog comment: confirms" "Logged 1h"

run_capture "worklog 15m with new-estimate" \
    $CLI -p "$PROJECT" issue worklog "$TASK_KEY" "15m" --new-estimate "2h"
assert_contains "worklog estimate: confirms" "Logged 15m"

run_test "worklog on Bug" true $CLI -p "$PROJECT" issue worklog "$BUG_KEY" "45m" -m "Bug worklog"

run_test "worklog - missing time" false $CLI -p "$PROJECT" issue worklog "$TASK_KEY"


# ════════════════════════════════════════════════════════════════════
# 17. ISSUE REMOTE-LINK
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 17. Issue Remote Link ──────────────────────────────${NC}"

run_capture "remote-link on Task" \
    $CLI -p "$PROJECT" issue remote-link "$TASK_KEY" "https://example.com/task-$TS" -t "Task Link"
assert_contains "remote-link: confirms" "Added remote link"

run_test "remote-link on Bug" true \
    $CLI -p "$PROJECT" issue remote-link "$BUG_KEY" "https://example.com/bug-$TS" -t "Bug Link"

run_test "remote-link - missing title" false \
    $CLI -p "$PROJECT" issue remote-link "$TASK_KEY" "https://example.com"


# ════════════════════════════════════════════════════════════════════
# 18. RELEASE CREATE / RELEASE
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 18. Release ────────────────────────────────────────${NC}"

# Create basic version
run_capture "release create" \
    $CLI -p "$PROJECT" release create "test-rel-$TS" -d "Live test release"
VERSION_ID=$(extract_id "$OUTPUT")
track_version "$VERSION_ID"
assert_contains "release create: confirms" "Created version"
echo "  -> VERSION_ID=$VERSION_ID"

# Create with release date
run_capture "release create (with date)" \
    $CLI -p "$PROJECT" release create "test-rel-dated-$TS" --release-date "2026-12-31"
VERSION_ID2=$(extract_id "$OUTPUT")
track_version "$VERSION_ID2"
assert_contains "release create dated: confirms" "Created version"

# Create with --released flag
run_capture "release create (pre-released)" \
    $CLI -p "$PROJECT" release create "test-rel-done-$TS" --released --release-date "2026-01-01"
VERSION_ID3=$(extract_id "$OUTPUT")
track_version "$VERSION_ID3"
assert_contains "release create released: confirms" "Created version"

# Release a version
if [ -n "$VERSION_ID" ]; then
    run_capture "release release" \
        $CLI release release "$VERSION_ID" --release-date "2026-04-04"
    assert_contains "release release: confirms" "Released version"
fi

# Verify new versions show in list
run_capture "release list after creates" $CLI release list "$PROJECT"
assert_contains "release list: shows test version" "test-rel-$TS"


# ════════════════════════════════════════════════════════════════════
# 19. SPRINT CREATE
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 19. Sprint ─────────────────────────────────────────${NC}"

if [ -n "$BOARD_ID" ]; then
    run_capture "sprint create" \
        $CLI sprint create "Test Sprint $TS" --board-id "$BOARD_ID"
    SPRINT_ID=$(extract_id "$OUTPUT")
    assert_contains "sprint create: confirms" "Created sprint"
    echo "  -> SPRINT_ID=$SPRINT_ID"

    # sprint start/close require dates — test the error handling
    if [ -n "$SPRINT_ID" ]; then
        run_test "sprint start (no dates)" false \
            $CLI sprint start "$SPRINT_ID"

        run_test "sprint close (not started)" false \
            $CLI sprint close "$SPRINT_ID"
    fi
else
    echo -e "  ${YELLOW}SKIP${NC} - No board ID, skipping sprint create/start/close"
fi


# ════════════════════════════════════════════════════════════════════
# 20. ISSUE DELETE
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 20. Issue Delete ───────────────────────────────────${NC}"

# Delete sub-task first (parent can't be deleted with children)
if [ -n "$SUBTASK_KEY" ]; then
    run_capture "delete Sub-task" $CLI -p "$PROJECT" issue delete "$SUBTASK_KEY" --yes
    assert_contains "delete subtask: confirms" "Deleted"
    CLEANUP_ISSUES=$(echo "$CLEANUP_ISSUES" | sed "s/$SUBTASK_KEY//")
fi

# Delete each created issue type
for key_var in FULL_KEY IMPROVEMENT_KEY STORY_KEY BUG_KEY TASK_KEY; do
    eval "key=\$$key_var"
    if [ -n "$key" ]; then
        run_capture "delete $key_var ($key)" $CLI -p "$PROJECT" issue delete "$key" --yes
        assert_contains "delete $key_var: confirms" "Deleted"
        CLEANUP_ISSUES=$(echo "$CLEANUP_ISSUES" | sed "s/$key//")
    fi
done

# Delete nonexistent
run_test "delete - nonexistent" false \
    $CLI -p "$PROJECT" issue delete "FAKEFAKE-99999" --yes


# ════════════════════════════════════════════════════════════════════
# 21. ERROR HANDLING & EDGE CASES
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}── 21. Error Handling ─────────────────────────────────${NC}"

run_test "issue list (config default project)" true $CLI issue list
run_test "issue create - missing summary" false $CLI -p "$PROJECT" issue create
run_test "issue assign - missing args" false $CLI -p "$PROJECT" issue assign
run_test "issue comment - missing body" false $CLI -p "$PROJECT" issue comment NTA-1
run_test "issue worklog - missing time" false $CLI -p "$PROJECT" issue worklog NTA-1
run_test "issue remote-link - missing title" false $CLI -p "$PROJECT" issue remote-link NTA-1 "https://x"
run_test "issue link - missing args" false $CLI -p "$PROJECT" issue link
run_test "issue unlink - missing args" false $CLI -p "$PROJECT" issue unlink
run_test "issue watch - missing args" false $CLI -p "$PROJECT" issue watch
run_test "board get - missing arg" false $CLI board get
run_test "sprint create - missing board-id" false $CLI sprint create "x"
run_test "release create - no project" false $CLI -c /dev/null release create "x"


# ════════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════════
echo -e "\n${BOLD}═══════════════════════════════════════════════════════${NC}"
if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}${BOLD}  ALL TESTS PASSED: $PASS/$TOTAL${NC}"
else
    echo -e "${RED}${BOLD}  FAILURES: $FAIL failed, $PASS passed, $TOTAL total${NC}"
fi
echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"

exit $FAIL
