#!/bin/sh
# tests/test_install_update_smoke.sh — T034 independent QA smoke suite.
#
# Written independently by QA (not copy-pasted from T031/T032/T033's own unit
# tests: tests/test_harness_fetch.sh, tests/test_setup.sh, tests/test_update.sh)
# per the Stage 4 Evidence Gate's independent-oracle rule. This suite exercises
# the PUBLIC setup.sh/update.sh CLI surface end-to-end from a scratch directory,
# the way a real user would invoke them — it does not re-test lib/harness-fetch.sh
# internals in isolation (T031's job).
#
# Fetch source: SUPERVISOR_REPO is pointed at THIS worktree's own local path
# rather than a real GitHub URL. `git clone --depth 1 <local-path>` clones the
# last commit's tree, needs no network, and so this suite has no network
# dependency to tolerate/report at all (the Edge Case Checklist's network
# concern is designed out, not handled reactively).
#
# Scenarios covered (Acceptance Criteria 1-4 of TASK_GUIDE_T034.md):
#   1. Fresh setup.sh install -> every MANIFEST path + CLAUDE.md land as real
#      files (not symlinks).
#   2. Immediate no-op update.sh run -> silent, no conflict prompts.
#   3. Local edit to an installed file -> update.sh's conflict prompt is
#      reached; both the "overwrite" and "skip" sub-cases are exercised.
#   4. Non-git target directory -> both setup.sh and update.sh reject before
#      writing anything.

REPO_ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
SETUP="$REPO_ROOT/setup.sh"
UPDATE="$REPO_ROOT/update.sh"

PASS_COUNT=0
FAIL_COUNT=0

pass() { printf 'PASS: %s\n' "$*"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { printf 'FAIL: %s\n' "$*" >&2; FAIL_COUNT=$((FAIL_COUNT + 1)); }

# ── Scratch-dir registry + cleanup trap (runs on pass AND fail) ──────────────
SCRATCH_DIRS=""
register_scratch() { SCRATCH_DIRS="$SCRATCH_DIRS $1"; }
cleanup() {
  for _d in $SCRATCH_DIRS; do
    [ -n "$_d" ] && [ -d "$_d" ] && rm -rf "$_d"
  done
}
trap cleanup EXIT INT TERM HUP

# Sets $SCRATCH_DIR_RESULT rather than printing to stdout: `$(fn)` capture would
# run register_scratch inside a command-substitution subshell, so SCRATCH_DIRS
# would never propagate back to this shell and the EXIT trap couldn't clean it
# up (same class of bug as lib/harness-fetch.sh's own harness_make_temp_dir).
SCRATCH_DIR_RESULT=""
make_scratch() {
  SCRATCH_DIR_RESULT=$(mktemp -d "${TMPDIR:-/tmp}/t034-smoke.XXXXXX") || {
    fail "mktemp failed while creating a scratch directory"
    exit 1
  }
  register_scratch "$SCRATCH_DIR_RESULT"
}

# Local fetch source for both scripts — no network needed for this whole suite.
SUPERVISOR_REPO="$REPO_ROOT"
export SUPERVISOR_REPO

# =============================================================================
# Scenario 1+2: fresh install, then an immediate no-op update
# =============================================================================
make_scratch
TARGET1="$SCRATCH_DIR_RESULT"
(
  cd "$TARGET1" || exit 1
  git init -q
  git config user.email "t034-smoke@test.local"
  git config user.name "T034 Smoke Suite"
)

INSTALL_OUT=$(cd "$TARGET1" && bash "$SETUP" </dev/null 2>&1)
INSTALL_STATUS=$?

if [ "$INSTALL_STATUS" -ne 0 ]; then
  fail "setup.sh exited $INSTALL_STATUS on a fresh, empty git repo (expected 0)"
  printf '%s\n' "$INSTALL_OUT" >&2
else
  pass "setup.sh exits 0 on a fresh git repo"
fi

# AC1: every MANIFEST path (as listed in THIS repo's own MANIFEST) + CLAUDE.md
# exist as real files/directories, never symlinks.
AC1_OK=1
while IFS= read -r line; do
  line=$(printf '%s' "$line" | tr -d '\r')
  case "$line" in '#'*|'') continue ;; esac
  installed_path="$TARGET1/$line"
  if [ ! -e "$installed_path" ]; then
    AC1_OK=0
    fail "AC1: MANIFEST path '$line' missing from target after setup.sh"
  elif [ -L "$installed_path" ]; then
    AC1_OK=0
    fail "AC1: MANIFEST path '$line' is a symlink after setup.sh (must be a real copy)"
  fi
done < "$REPO_ROOT/MANIFEST"

if [ ! -e "$TARGET1/CLAUDE.md" ]; then
  AC1_OK=0
  fail "AC1: CLAUDE.md missing from target after setup.sh"
elif [ -L "$TARGET1/CLAUDE.md" ]; then
  AC1_OK=0
  fail "AC1: CLAUDE.md is a symlink after setup.sh (must be a real copy)"
fi

if [ ! -f "$TARGET1/.claude/harness-lock.json" ]; then
  AC1_OK=0
  fail "AC1: .claude/harness-lock.json was not written by setup.sh"
fi

[ "$AC1_OK" -eq 1 ] && pass "AC1: fresh install lands every MANIFEST path + CLAUDE.md as real files (no symlinks)"

# AC2: an immediate re-run of update.sh (no local edits yet) is silent — zero
# conflict prompts, all files silently refreshed, clean exit.
UPDATE1_OUT=$(cd "$TARGET1" && bash "$UPDATE" </dev/null 2>&1)
UPDATE1_STATUS=$?

if [ "$UPDATE1_STATUS" -ne 0 ]; then
  fail "AC2: no-op update.sh exited $UPDATE1_STATUS (expected 0 - nothing was edited)"
  printf '%s\n' "$UPDATE1_OUT" >&2
elif printf '%s' "$UPDATE1_OUT" | grep -qi 'conflict'; then
  fail "AC2: no-op update.sh printed a conflict, but nothing was edited locally"
  printf '%s\n' "$UPDATE1_OUT" >&2
elif printf '%s' "$UPDATE1_OUT" | grep -q 'Resolve:'; then
  fail "AC2: no-op update.sh emitted an interactive conflict prompt unexpectedly"
  printf '%s\n' "$UPDATE1_OUT" >&2
else
  pass "AC2: no-op update.sh run is silent (exit 0, no conflict prompts)"
fi

# =============================================================================
# Scenario 3: a real local edit triggers update.sh's conflict prompt, both the
# "overwrite" and "skip" sub-cases are exercised.
# =============================================================================
EDIT_FILE="$TARGET1/.claude/agents/qa.md"
if [ ! -f "$EDIT_FILE" ]; then
  fail "AC3 setup: expected editable file '.claude/agents/qa.md' not present after install"
else
  ORIGINAL_CONTENT=$(cat "$EDIT_FILE")

  # ── 3a: overwrite branch ───────────────────────────────────────────────────
  printf '\nSMOKE_TEST_LOCAL_EDIT_MARKER_OVERWRITE\n' >> "$EDIT_FILE"

  OVERWRITE_OUT=$(cd "$TARGET1" && printf 'o\n' | bash "$UPDATE" 2>&1)
  OVERWRITE_STATUS=$?

  if [ "$OVERWRITE_STATUS" -ne 0 ]; then
    fail "AC3a: update.sh exited $OVERWRITE_STATUS on the overwrite sub-case"
    printf '%s\n' "$OVERWRITE_OUT" >&2
  elif ! printf '%s' "$OVERWRITE_OUT" | grep -qi 'conflict'; then
    fail "AC3a: update.sh did not report a conflict for a locally-edited file"
    printf '%s\n' "$OVERWRITE_OUT" >&2
  elif grep -q 'SMOKE_TEST_LOCAL_EDIT_MARKER_OVERWRITE' "$EDIT_FILE"; then
    fail "AC3a: 'o' (overwrite) choice did not restore the upstream content"
  else
    pass "AC3a: conflict prompt reached, 'o' (overwrite) restores upstream content"
  fi

  # ── 3b: skip branch ────────────────────────────────────────────────────────
  printf '\nSMOKE_TEST_LOCAL_EDIT_MARKER_SKIP\n' >> "$EDIT_FILE"
  EXPECTED_SKIP_CONTENT=$(cat "$EDIT_FILE")

  SKIP_OUT=$(cd "$TARGET1" && printf 's\n' | bash "$UPDATE" 2>&1)
  SKIP_STATUS=$?

  if [ "$SKIP_STATUS" -ne 0 ]; then
    fail "AC3b: update.sh exited $SKIP_STATUS on the skip sub-case"
    printf '%s\n' "$SKIP_OUT" >&2
  elif ! printf '%s' "$SKIP_OUT" | grep -qi 'conflict'; then
    fail "AC3b: update.sh did not report a conflict for a locally-edited file"
    printf '%s\n' "$SKIP_OUT" >&2
  else
    ACTUAL_SKIP_CONTENT=$(cat "$EDIT_FILE")
    if [ "$ACTUAL_SKIP_CONTENT" = "$EXPECTED_SKIP_CONTENT" ]; then
      pass "AC3b: conflict prompt reached, 's' (skip) leaves the file byte-identical to the user's edit"
    else
      fail "AC3b: 's' (skip) choice altered the user's local edit (expected byte-identical)"
    fi
  fi

  # Sanity: ORIGINAL_CONTENT was captured for readability/debugging only, not a
  # separate assertion (AC3a already proves upstream content is restorable).
  : "$ORIGINAL_CONTENT"
fi

# =============================================================================
# Scenario 4: a non-git target directory is rejected by BOTH scripts, before
# either writes anything.
# =============================================================================
make_scratch
TARGET2="$SCRATCH_DIR_RESULT"
# Deliberately no `git init` here — TARGET2 is a plain directory.

SETUP_NONGIT_OUT=$(cd "$TARGET2" && bash "$SETUP" </dev/null 2>&1)
SETUP_NONGIT_STATUS=$?

if [ "$SETUP_NONGIT_STATUS" -eq 0 ]; then
  fail "AC4: setup.sh exited 0 against a non-git directory (expected a non-zero rejection)"
else
  pass "AC4: setup.sh rejects a non-git target directory (exit $SETUP_NONGIT_STATUS)"
fi

NONGIT_ENTRY_COUNT=$(find "$TARGET2" -mindepth 1 | wc -l | tr -d ' ')
if [ "$NONGIT_ENTRY_COUNT" -ne 0 ]; then
  fail "AC4: setup.sh wrote $NONGIT_ENTRY_COUNT entr(y/ies) into a non-git target before rejecting it"
else
  pass "AC4: setup.sh wrote nothing into the non-git target before rejecting it"
fi

UPDATE_NONGIT_OUT=$(cd "$TARGET2" && bash "$UPDATE" </dev/null 2>&1)
UPDATE_NONGIT_STATUS=$?

if [ "$UPDATE_NONGIT_STATUS" -eq 0 ]; then
  fail "AC4: update.sh exited 0 against a non-git directory (expected a non-zero rejection)"
else
  pass "AC4: update.sh rejects a non-git target directory (exit $UPDATE_NONGIT_STATUS)"
fi

NONGIT_ENTRY_COUNT2=$(find "$TARGET2" -mindepth 1 | wc -l | tr -d ' ')
if [ "$NONGIT_ENTRY_COUNT2" -ne 0 ]; then
  fail "AC4: update.sh wrote $NONGIT_ENTRY_COUNT2 entr(y/ies) into a non-git target before rejecting it"
else
  pass "AC4: update.sh wrote nothing into the non-git target before rejecting it"
fi

# =============================================================================
# Summary
# =============================================================================
printf '\n%d passed, %d failed\n' "$PASS_COUNT" "$FAIL_COUNT"
if [ "$FAIL_COUNT" -gt 0 ]; then
  exit 1
fi
exit 0
