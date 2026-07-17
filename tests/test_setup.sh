#!/bin/sh
# tests/test_setup.sh — POSIX-sh test harness for setup.sh (T032)
#
# Self-contained: builds a throwaway local git "harness" fixture repo, then runs
# the real setup.sh against a scratch git-initialized target directory using a
# file:// repo URL (no network). Asserts:
#   - fresh install produces REAL file copies (not symlinks) of MANIFEST paths + CLAUDE.md
#   - .claude/harness-lock.json is written with one hash entry per installed file
#   - a non-git target directory is rejected non-zero, before any file is written
#   - a second run overwrites edited files unconditionally (setup always overwrites)
#   - no $SUPERVISOR_PATH / ~/.supervisor directory is created or required
#
# Runs non-interactively by redirecting stdin from /dev/null (so setup.sh's
# `[ -t 0 ]` prompts default to greenfield / no packs).
#
# Run: bash tests/test_setup.sh   (or: sh tests/test_setup.sh)
set -u

# ── Locate setup.sh under test (relative to this script) ─────────────────────
SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)
SETUP="$REPO_ROOT/setup.sh"

if [ ! -f "$SETUP" ]; then
  printf 'FATAL: setup.sh not found at %s\n' "$SETUP" >&2
  exit 2
fi

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1" >&2; }

# ── Test workspace (cleaned on exit) ─────────────────────────────────────────
WORK=$(mktemp -d "${TMPDIR:-/tmp}/setup-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT INT TERM HUP

# A path that must never be created by setup.sh (proves the no-central-clone rule).
NO_CLONE="$WORK/should-not-exist-supervisor"

# ── Build a minimal fixture "harness" repo to be cloned by setup.sh ───────────
FIXTURE="$WORK/fixture-repo"
mkdir -p "$FIXTURE/.claude/agents" \
         "$FIXTURE/.claude/skills/brainstorming" \
         "$FIXTURE/.claude/hooks" \
         "$FIXTURE/templates"
printf 'backend-agent-content\n'  > "$FIXTURE/.claude/agents/backend.md"
printf 'skill-content\n'          > "$FIXTURE/.claude/skills/brainstorming/SKILL.md"
printf 'hook-content\n'           > "$FIXTURE/.claude/hooks/example_hook.py"
printf 'template-content\n'       > "$FIXTURE/templates/PRD_template.md"
printf '{ "hooks": {} }\n'        > "$FIXTURE/.claude/settings.json"
printf 'GREENFIELD SUPERVISOR RULES\n' > "$FIXTURE/CLAUDE.md"
printf 'BROWNFIELD SUPERVISOR RULES\n' > "$FIXTURE/CLAUDE_LEGACY.md"
cat > "$FIXTURE/MANIFEST" <<'EOF'
# fixture MANIFEST
.claude/agents
.claude/skills
.claude/hooks
templates
EOF

git -C "$FIXTURE" init -q
git -C "$FIXTURE" config user.email "test@example.com"
git -C "$FIXTURE" config user.name "Test"
git -C "$FIXTURE" add -A
git -C "$FIXTURE" commit -q -m "fixture harness"

# Helper: run setup.sh non-interactively inside a target dir, offline (file://),
# with SUPERVISOR_PATH pointed at a path that must stay non-existent.
run_setup() {
  _target="$1"
  ( cd "$_target" \
      && SUPERVISOR_REPO="file://$FIXTURE" SUPERVISOR_PATH="$NO_CLONE" \
         bash "$SETUP" </dev/null >"$WORK/setup.log" 2>&1 )
}

# =============================================================================
# Test 1 — fresh install into a git-initialized target: real copies + lockfile
# =============================================================================
TARGET1="$WORK/target1"
mkdir -p "$TARGET1"
git -C "$TARGET1" init -q

T1_RC=0
run_setup "$TARGET1" || T1_RC=$?

if [ "$T1_RC" -eq 0 ]; then
  pass "test1: setup.sh exited 0 on a git-initialized target"
else
  fail "test1: setup.sh returned non-zero ($T1_RC) — see $WORK/setup.log"
  cat "$WORK/setup.log" >&2
fi

if [ -f "$TARGET1/.claude/agents/backend.md" ] \
   && [ -f "$TARGET1/.claude/skills/brainstorming/SKILL.md" ] \
   && [ -f "$TARGET1/.claude/hooks/example_hook.py" ] \
   && [ -f "$TARGET1/templates/PRD_template.md" ]; then
  pass "test1: all MANIFEST paths installed"
else
  fail "test1: one or more MANIFEST paths missing"
fi

# Real copies, not symlinks (AC #1).
if [ ! -L "$TARGET1/.claude/agents" ] \
   && [ ! -L "$TARGET1/.claude/agents/backend.md" ] \
   && [ ! -L "$TARGET1/CLAUDE.md" ]; then
  pass "test1: installed entries are real files, not symlinks"
else
  fail "test1: an installed entry is a symlink (expected real copy)"
fi

# CLAUDE.md is a real copy of the greenfield source (non-interactive default).
if [ -f "$TARGET1/CLAUDE.md" ] \
   && grep -q 'GREENFIELD SUPERVISOR RULES' "$TARGET1/CLAUDE.md"; then
  pass "test1: CLAUDE.md installed from greenfield source"
else
  fail "test1: CLAUDE.md missing or wrong source"
fi

# settings.json copied (copy-only behavior preserved, AC #7).
if [ -f "$TARGET1/.claude/settings.json" ] && [ ! -L "$TARGET1/.claude/settings.json" ]; then
  pass "test1: .claude/settings.json installed as a real copy"
else
  fail "test1: .claude/settings.json missing or a symlink"
fi

# harness-lock.json exists and records one hash entry per installed MANIFEST file (AC #3).
LOCK="$TARGET1/.claude/harness-lock.json"
if [ -f "$LOCK" ]; then
  pass "test1: .claude/harness-lock.json written"
else
  fail "test1: .claude/harness-lock.json missing"
fi

if grep -q '"files"' "$LOCK" 2>/dev/null \
   && grep -q '".claude/agents/backend.md"' "$LOCK" 2>/dev/null \
   && grep -q '"templates/PRD_template.md"' "$LOCK" 2>/dev/null \
   && grep -q '"CLAUDE.md"' "$LOCK" 2>/dev/null; then
  pass "test1: harness-lock.json contains a hash entry per installed file"
else
  fail "test1: harness-lock.json missing expected file entries"
fi

# Recorded hash matches the actual installed file content (content-only, permission-independent).
EXPECTED_HASH=$(sha256sum "$TARGET1/.claude/agents/backend.md" | awk '{print $1}')
if grep -q "$EXPECTED_HASH" "$LOCK" 2>/dev/null; then
  pass "test1: recorded hash matches installed file content"
else
  fail "test1: recorded hash does not match installed file content"
fi

# A chmod-only change must NOT change the recorded hash (edge-case checklist).
chmod 600 "$TARGET1/.claude/agents/backend.md"
REHASH=$(sha256sum "$TARGET1/.claude/agents/backend.md" | awk '{print $1}')
if [ "$REHASH" = "$EXPECTED_HASH" ]; then
  pass "test1: hash is permission-independent (chmod does not alter it)"
else
  fail "test1: hash changed after chmod (not content-only)"
fi

# AC #5 — no central clone directory created or required.
if [ ! -d "$NO_CLONE" ]; then
  pass "test1: no \$SUPERVISOR_PATH / central-clone directory created"
else
  fail "test1: setup.sh created a central-clone directory at $NO_CLONE"
fi

# =============================================================================
# Test 2 — non-git target directory: reject non-zero, write nothing (AC #2)
# =============================================================================
TARGET2="$WORK/target2-not-git"
mkdir -p "$TARGET2"

T2_RC=0
run_setup "$TARGET2" || T2_RC=$?

if [ "$T2_RC" -ne 0 ]; then
  pass "test2: setup.sh rejects a non-git target (rc=$T2_RC)"
else
  fail "test2: setup.sh unexpectedly succeeded in a non-git target"
fi

if [ ! -e "$TARGET2/.claude" ] && [ ! -e "$TARGET2/CLAUDE.md" ] && [ ! -e "$TARGET2/templates" ]; then
  pass "test2: no files written to a non-git target"
else
  fail "test2: files were written despite the non-git rejection"
fi

if grep -qi 'not a git repository' "$WORK/setup.log" 2>/dev/null; then
  pass "test2: emitted a clear 'not a git repository' error"
else
  fail "test2: no clear git-repo error message emitted"
fi

# =============================================================================
# Test 3 — re-run overwrites edited files unconditionally (AC #4)
# =============================================================================
# Corrupt an installed file, then re-run setup.sh and expect it restored.
printf 'USER LOCAL EDIT — should be clobbered\n' > "$TARGET1/.claude/agents/backend.md"

T3_RC=0
run_setup "$TARGET1" || T3_RC=$?

if [ "$T3_RC" -eq 0 ]; then
  pass "test3: setup.sh re-run exited 0"
else
  fail "test3: setup.sh re-run returned non-zero ($T3_RC)"
fi

if grep -q 'backend-agent-content' "$TARGET1/.claude/agents/backend.md" \
   && ! grep -q 'USER LOCAL EDIT' "$TARGET1/.claude/agents/backend.md"; then
  pass "test3: edited file overwritten back to upstream (always-overwrite)"
else
  fail "test3: edited file was not overwritten on re-run"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
printf '\n----- summary: %d passed, %d failed -----\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
