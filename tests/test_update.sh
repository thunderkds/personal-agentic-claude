#!/bin/sh
# tests/test_update.sh — POSIX-sh test harness for update.sh (T033)
#
# Self-contained and offline (file:// repo URL, no network). Builds a throwaway
# local git "harness" fixture, runs the REAL setup.sh to produce an installed
# target repo + .claude/harness-lock.json, then exercises update.sh's branches:
#   1. non-git target            -> reject non-zero before any action
#   2. symlink at a MANIFEST path -> reject non-zero with migrate message, no writes
#   3. untouched install         -> silent overwrite, no prompt; upstream change propagates
#   4. edited file (conflict)     -> prompt fires; [s]kip keeps the edit + prior lock hash
#   5. edited file (conflict)     -> [o]verwrite restores upstream + updates lock hash
#   6. conflict with no input     -> non-zero exit, file left untouched
#
# Run: bash tests/test_update.sh   (or: sh tests/test_update.sh)
set -u

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)
SETUP="$REPO_ROOT/setup.sh"
UPDATE="$REPO_ROOT/update.sh"

for f in "$SETUP" "$UPDATE"; do
  if [ ! -f "$f" ]; then
    printf 'FATAL: required script not found at %s\n' "$f" >&2
    exit 2
  fi
done

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1" >&2; }

WORK=$(mktemp -d "${TMPDIR:-/tmp}/update-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT INT TERM HUP

NO_CLONE="$WORK/should-not-exist-supervisor"

# Read a single file's recorded hash from a harness-lock.json.
lock_hash() {
  grep -F "\"$2\": \"" "$1" 2>/dev/null | head -n1 | sed -e 's/.*: "//' -e 's/".*//'
}

# ── Build a minimal fixture "harness" repo (the fresh upstream update fetches) ─
FIXTURE="$WORK/fixture-repo"
build_fixture() {
  mkdir -p "$FIXTURE/.claude/agents" \
           "$FIXTURE/.claude/skills/brainstorming" \
           "$FIXTURE/.claude/hooks" \
           "$FIXTURE/templates"
  printf 'backend-agent-content\n'  > "$FIXTURE/.claude/agents/backend.md"
  printf 'frontend-agent-content\n' > "$FIXTURE/.claude/agents/frontend.md"
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
}
build_fixture

# Run setup.sh non-interactively into a git-initialized target (offline).
run_setup() {
  _target="$1"
  ( cd "$_target" \
      && SUPERVISOR_REPO="file://$FIXTURE" SUPERVISOR_PATH="$NO_CLONE" \
         bash "$SETUP" </dev/null >"$WORK/setup.log" 2>&1 )
}

# Run update.sh with stdin from $2 (a file: /dev/null or a canned answer file).
run_update() {
  _target="$1"
  _stdin="$2"
  ( cd "$_target" \
      && SUPERVISOR_REPO="file://$FIXTURE" \
         bash "$UPDATE" <"$_stdin" >"$WORK/update.log" 2>&1 )
}

# Freshly install a target repo; returns via $NEW_TARGET.
NEW_TARGET=""
fresh_target() {
  NEW_TARGET="$WORK/$1"
  mkdir -p "$NEW_TARGET"
  git -C "$NEW_TARGET" init -q
  run_setup "$NEW_TARGET" || {
    fail "setup failed for $1 — see $WORK/setup.log"; cat "$WORK/setup.log" >&2; return 1
  }
}

# Canned stdin answers.
printf 's\n' > "$WORK/skip.in"
printf 'o\n' > "$WORK/overwrite.in"

# =============================================================================
# Test 1 — non-git target: reject non-zero, touch nothing (AC #1)
# =============================================================================
T1="$WORK/target1-not-git"
mkdir -p "$T1"
RC=0
run_update "$T1" /dev/null || RC=$?
if [ "$RC" -ne 0 ]; then
  pass "test1: update.sh rejects a non-git target (rc=$RC)"
else
  fail "test1: update.sh unexpectedly succeeded in a non-git target"
fi
if grep -qi 'not a git repository' "$WORK/update.log" 2>/dev/null; then
  pass "test1: emitted a clear 'not a git repository' error"
else
  fail "test1: no clear git-repo error message emitted"
fi
if [ ! -e "$T1/.claude" ]; then
  pass "test1: no files written to a non-git target"
else
  fail "test1: files were written despite the non-git rejection"
fi

# =============================================================================
# Test 2 — symlink at a MANIFEST path: reject non-zero, migrate message (AC #2)
# =============================================================================
if fresh_target "target2"; then
  T2="$NEW_TARGET"
  # Simulate an old symlink-model install: replace .claude/agents with a symlink.
  rm -rf "$T2/.claude/agents"
  ln -s "$FIXTURE/.claude/agents" "$T2/.claude/agents"
  LOCK2_BEFORE=$(cat "$T2/.claude/harness-lock.json")

  RC=0
  run_update "$T2" /dev/null || RC=$?
  if [ "$RC" -ne 0 ]; then
    pass "test2: update.sh refuses when a MANIFEST path is a symlink (rc=$RC)"
  else
    fail "test2: update.sh did not refuse a symlinked MANIFEST path"
  fi
  if grep -qi 'symlink' "$WORK/update.log" 2>/dev/null \
     && grep -qi 'setup.sh' "$WORK/update.log" 2>/dev/null; then
    pass "test2: emitted a symlink migration-instruction message"
  else
    fail "test2: no symlink migration message emitted"
  fi
  # Symlink not converted (still a symlink) and lock untouched (no files touched).
  if [ -L "$T2/.claude/agents" ]; then
    pass "test2: symlink was NOT converted (detect-and-refuse only)"
  else
    fail "test2: symlink was altered/converted"
  fi
  if [ "$(cat "$T2/.claude/harness-lock.json")" = "$LOCK2_BEFORE" ]; then
    pass "test2: harness-lock.json untouched after symlink refusal"
  else
    fail "test2: harness-lock.json changed despite refusal"
  fi
fi

# =============================================================================
# Test 3 — untouched install: silent overwrite + upstream change propagates (AC #3)
# =============================================================================
if fresh_target "target3"; then
  T3="$NEW_TARGET"
  # Publish a NEW upstream version of one file so we can prove propagation.
  printf 'backend-agent-content-V2\n' > "$FIXTURE/.claude/agents/backend.md"
  git -C "$FIXTURE" commit -q -am "upstream: bump backend.md to V2"

  RC=0
  run_update "$T3" /dev/null || RC=$?
  if [ "$RC" -eq 0 ]; then
    pass "test3: update.sh exited 0 on a fully-untouched install"
  else
    fail "test3: update.sh returned non-zero ($RC) — see $WORK/update.log"
    cat "$WORK/update.log" >&2
  fi
  # No interactive prompt should have fired.
  if ! grep -qi 'Resolve:' "$WORK/update.log" 2>/dev/null; then
    pass "test3: no conflict prompt fired for untouched files"
  else
    fail "test3: a conflict prompt fired when nothing was customized"
  fi
  # The untouched file received the fresh upstream content silently.
  if grep -q 'backend-agent-content-V2' "$T3/.claude/agents/backend.md" 2>/dev/null; then
    pass "test3: untouched file silently overwritten with fresh upstream (V2)"
  else
    fail "test3: untouched file was not updated to upstream V2"
  fi
  # Lock re-records the new upstream hash.
  EXP3=$(sha256sum "$FIXTURE/.claude/agents/backend.md" | awk '{print $1}')
  GOT3=$(lock_hash "$T3/.claude/harness-lock.json" ".claude/agents/backend.md")
  if [ "$EXP3" = "$GOT3" ]; then
    pass "test3: lock re-records the new upstream hash for the overwritten file"
  else
    fail "test3: lock hash not updated (expected $EXP3, got $GOT3)"
  fi
  # Restore fixture to V1 for the remaining tests.
  printf 'backend-agent-content\n' > "$FIXTURE/.claude/agents/backend.md"
  git -C "$FIXTURE" commit -q -am "upstream: restore backend.md to V1"
fi

# =============================================================================
# Test 4 — edited file (conflict) + [s]kip: keep edit, keep prior lock hash (AC #4/#5)
# =============================================================================
if fresh_target "target4"; then
  T4="$NEW_TARGET"
  HASH4_BEFORE=$(lock_hash "$T4/.claude/harness-lock.json" ".claude/agents/backend.md")
  printf 'MY LOCAL CUSTOMIZATION\n' > "$T4/.claude/agents/backend.md"

  RC=0
  run_update "$T4" "$WORK/skip.in" || RC=$?
  if [ "$RC" -eq 0 ]; then
    pass "test4: update.sh exited 0 after resolving a conflict with skip"
  else
    fail "test4: update.sh returned non-zero ($RC) on a skip resolution"
    cat "$WORK/update.log" >&2
  fi
  if grep -qi 'conflict' "$WORK/update.log" 2>/dev/null \
     && grep -qi 'Resolve:' "$WORK/update.log" 2>/dev/null; then
    pass "test4: conflict detected and prompt fired for the edited file"
  else
    fail "test4: no conflict prompt fired for the edited file"
  fi
  if grep -q 'MY LOCAL CUSTOMIZATION' "$T4/.claude/agents/backend.md" 2>/dev/null \
     && ! grep -q 'backend-agent-content' "$T4/.claude/agents/backend.md" 2>/dev/null; then
    pass "test4: [s]kip left the local customization intact"
  else
    fail "test4: [s]kip did not preserve the local edit"
  fi
  HASH4_AFTER=$(lock_hash "$T4/.claude/harness-lock.json" ".claude/agents/backend.md")
  if [ "$HASH4_AFTER" = "$HASH4_BEFORE" ]; then
    pass "test4: lock hash for the skipped file unchanged (prior hash kept)"
  else
    fail "test4: lock hash changed for a skipped file (before=$HASH4_BEFORE after=$HASH4_AFTER)"
  fi
  # Prove a non-edited file was still silently overwritten (only the edit prompted).
  if grep -q 'frontend-agent-content' "$T4/.claude/agents/frontend.md" 2>/dev/null; then
    pass "test4: untouched sibling file overwritten silently (prompt was per-file)"
  else
    fail "test4: sibling file handling incorrect"
  fi
fi

# =============================================================================
# Test 5 — edited file (conflict) + [o]verwrite: restore upstream, update lock (AC #4/#5)
# =============================================================================
if fresh_target "target5"; then
  T5="$NEW_TARGET"
  printf 'ANOTHER LOCAL EDIT\n' > "$T5/.claude/agents/backend.md"

  RC=0
  run_update "$T5" "$WORK/overwrite.in" || RC=$?
  if [ "$RC" -eq 0 ]; then
    pass "test5: update.sh exited 0 after resolving a conflict with overwrite"
  else
    fail "test5: update.sh returned non-zero ($RC) on an overwrite resolution"
    cat "$WORK/update.log" >&2
  fi
  if grep -q 'backend-agent-content' "$T5/.claude/agents/backend.md" 2>/dev/null \
     && ! grep -q 'ANOTHER LOCAL EDIT' "$T5/.claude/agents/backend.md" 2>/dev/null; then
    pass "test5: [o]verwrite replaced the local edit with fresh upstream"
  else
    fail "test5: [o]verwrite did not restore the upstream version"
  fi
  EXP5=$(sha256sum "$FIXTURE/.claude/agents/backend.md" | awk '{print $1}')
  GOT5=$(lock_hash "$T5/.claude/harness-lock.json" ".claude/agents/backend.md")
  if [ "$EXP5" = "$GOT5" ]; then
    pass "test5: lock re-records the upstream hash for the overwritten file"
  else
    fail "test5: lock hash not updated after overwrite (expected $EXP5, got $GOT5)"
  fi
fi

# =============================================================================
# Test 6 — conflict with NO input (stdin=/dev/null): refuse, leave file untouched
# =============================================================================
if fresh_target "target6"; then
  T6="$NEW_TARGET"
  printf 'UNRESOLVABLE LOCAL EDIT\n' > "$T6/.claude/agents/backend.md"

  RC=0
  run_update "$T6" /dev/null || RC=$?
  if [ "$RC" -ne 0 ]; then
    pass "test6: update.sh exits non-zero when a conflict has no interactive input (rc=$RC)"
  else
    fail "test6: update.sh guessed a resolution instead of refusing on no input"
  fi
  if grep -q 'UNRESOLVABLE LOCAL EDIT' "$T6/.claude/agents/backend.md" 2>/dev/null; then
    pass "test6: local edit left untouched when no input was available"
  else
    fail "test6: local edit was altered despite no input"
  fi
  if grep -qi 're-run interactively' "$WORK/update.log" 2>/dev/null; then
    pass "test6: instructed the user to re-run interactively"
  else
    fail "test6: no 're-run interactively' guidance emitted"
  fi
fi

printf '\n----- summary: %d passed, %d failed -----\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
