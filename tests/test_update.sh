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
#  T137: [o]verwrite first moves the edit to <file>.bak-<old kit commit>; [s]kip
#        and no-input make no backup; the lock's "kit_commit" is never a file.
#
# Run: bash tests/test_update.sh   (or: sh tests/test_update.sh)
set -u

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)
# shellcheck source=tests/lib/pty.sh
. "$SCRIPT_DIR/lib/pty.sh"
detach_from_terminal "$0" "$@"
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
  mkdir -p "$FIXTURE/agents" \
           "$FIXTURE/skills/brainstorming" \
           "$FIXTURE/.claude/hooks" \
           "$FIXTURE/templates"
  printf 'backend-agent-content\n'  > "$FIXTURE/agents/backend.md"
  printf 'frontend-agent-content\n' > "$FIXTURE/agents/frontend.md"
  printf 'skill-content\n'          > "$FIXTURE/skills/brainstorming/SKILL.md"
  printf 'hook-content\n'           > "$FIXTURE/.claude/hooks/example_hook.py"
  printf 'template-content\n'       > "$FIXTURE/templates/PRD_template.md"
  printf '{ "hooks": {} }\n'        > "$FIXTURE/.claude/settings.json"
  # T111: setup/update merge kit hooks into an existing settings.json using
  # lib/merge-settings.py from the fetched clone — the fixture must ship it.
  mkdir -p "$FIXTURE/lib"
  cp "$REPO_ROOT/lib/merge-settings.py" "$FIXTURE/lib/merge-settings.py"
  printf 'GREENFIELD SUPERVISOR RULES\n' > "$FIXTURE/CLAUDE.md"
  printf 'BROWNFIELD SUPERVISOR RULES\n' > "$FIXTURE/CLAUDE_LEGACY.md"
  cat > "$FIXTURE/MANIFEST" <<'EOF'
# fixture MANIFEST
agents
skills
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

# Run update.sh. $2 = /dev/null: no terminal (the safe no-input path).
# $2 = a canned answer file: the answers are typed into a real terminal (T114:
# prompts read /dev/tty, never stdin) after accepting the action menu (Enter =
# Update) and the plan (Enter = Proceed).
run_update() {
  _target="$1"
  _stdin="$2"
  if [ "$_stdin" = /dev/null ]; then
    ( cd "$_target" \
        && SUPERVISOR_REPO="file://$FIXTURE" \
           bash "$UPDATE" <"$_stdin" >"$WORK/update.log" 2>&1 )
  else
    ( cd "$_target" \
        && SUPERVISOR_REPO="file://$FIXTURE" \
           run_in_pty "\n\n$(cat "$_stdin")\n" "bash '$UPDATE'" >"$WORK/update.log" 2>&1 )
  fi
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

# no_bak <target> -> true when no backup path exists anywhere in <target>
no_bak() {
  [ -z "$(find "$1" -name '*.bak*' -not -path '*/.git/*' | head -n 1)" ]
}
# kit_commit <lock> -> the lock's top-level "kit_commit" value ('' if absent)
kit_commit() {
  sed -n 's/^  "kit_commit": "\([^"]*\)",*$/\1/p' "$1" 2>/dev/null
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
  # Simulate an old symlink-model install: replace agents with a symlink.
  rm -rf "$T2/agents"
  ln -s "$FIXTURE/agents" "$T2/agents"
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
  if [ -L "$T2/agents" ]; then
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
  printf 'backend-agent-content-V2\n' > "$FIXTURE/agents/backend.md"
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
  if grep -q 'backend-agent-content-V2' "$T3/agents/backend.md" 2>/dev/null; then
    pass "test3: untouched file silently overwritten with fresh upstream (V2)"
  else
    fail "test3: untouched file was not updated to upstream V2"
  fi
  # Lock re-records the new upstream hash.
  EXP3=$(sha256sum "$FIXTURE/agents/backend.md" | awk '{print $1}')
  GOT3=$(lock_hash "$T3/.claude/harness-lock.json" "agents/backend.md")
  if [ "$EXP3" = "$GOT3" ]; then
    pass "test3: lock re-records the new upstream hash for the overwritten file"
  else
    fail "test3: lock hash not updated (expected $EXP3, got $GOT3)"
  fi
  # Restore fixture to V1 for the remaining tests.
  printf 'backend-agent-content\n' > "$FIXTURE/agents/backend.md"
  git -C "$FIXTURE" commit -q -am "upstream: restore backend.md to V1"
fi

# =============================================================================
# Test 4 — edited file (conflict) + [s]kip: keep edit, keep prior lock hash (AC #4/#5)
# =============================================================================
if fresh_target "target4"; then
  T4="$NEW_TARGET"
  HASH4_BEFORE=$(lock_hash "$T4/.claude/harness-lock.json" "agents/backend.md")
  printf 'MY LOCAL CUSTOMIZATION\n' > "$T4/agents/backend.md"

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
  if grep -q 'MY LOCAL CUSTOMIZATION' "$T4/agents/backend.md" 2>/dev/null \
     && ! grep -q 'backend-agent-content' "$T4/agents/backend.md" 2>/dev/null; then
    pass "test4: [s]kip left the local customization intact"
  else
    fail "test4: [s]kip did not preserve the local edit"
  fi
  HASH4_AFTER=$(lock_hash "$T4/.claude/harness-lock.json" "agents/backend.md")
  if [ "$HASH4_AFTER" = "$HASH4_BEFORE" ]; then
    pass "test4: lock hash for the skipped file unchanged (prior hash kept)"
  else
    fail "test4: lock hash changed for a skipped file (before=$HASH4_BEFORE after=$HASH4_AFTER)"
  fi
  # Prove a non-edited file was still silently overwritten (only the edit prompted).
  if grep -q 'frontend-agent-content' "$T4/agents/frontend.md" 2>/dev/null; then
    pass "test4: untouched sibling file overwritten silently (prompt was per-file)"
  else
    fail "test4: sibling file handling incorrect"
  fi
  # T137 SC6 / AC9: [s]kip keeps the file in place, so there is nothing to back up.
  if no_bak "$T4"; then
    pass "test4 (T137 SC6): [s]kip made no backup"
  else
    fail "test4 (T137 SC6): [s]kip created a backup"; find "$T4" -name '*.bak*' -not -path '*/.git/*' >&2
  fi
fi

# =============================================================================
# Test 5 — edited file (conflict) + [o]verwrite: restore upstream, update lock (AC #4/#5)
# =============================================================================
if fresh_target "target5"; then
  T5="$NEW_TARGET"
  printf 'ANOTHER LOCAL EDIT\n' > "$T5/agents/backend.md"

  RC=0
  run_update "$T5" "$WORK/overwrite.in" || RC=$?
  if [ "$RC" -eq 0 ]; then
    pass "test5: update.sh exited 0 after resolving a conflict with overwrite"
  else
    fail "test5: update.sh returned non-zero ($RC) on an overwrite resolution"
    cat "$WORK/update.log" >&2
  fi
  if grep -q 'backend-agent-content' "$T5/agents/backend.md" 2>/dev/null \
     && ! grep -q 'ANOTHER LOCAL EDIT' "$T5/agents/backend.md" 2>/dev/null; then
    pass "test5: [o]verwrite replaced the local edit with fresh upstream"
  else
    fail "test5: [o]verwrite did not restore the upstream version"
  fi
  EXP5=$(sha256sum "$FIXTURE/agents/backend.md" | awk '{print $1}')
  GOT5=$(lock_hash "$T5/.claude/harness-lock.json" "agents/backend.md")
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
  printf 'UNRESOLVABLE LOCAL EDIT\n' > "$T6/agents/backend.md"

  RC=0
  run_update "$T6" /dev/null || RC=$?
  if [ "$RC" -ne 0 ]; then
    pass "test6: update.sh exits non-zero when a conflict has no interactive input (rc=$RC)"
  else
    fail "test6: update.sh guessed a resolution instead of refusing on no input"
  fi
  if grep -q 'UNRESOLVABLE LOCAL EDIT' "$T6/agents/backend.md" 2>/dev/null; then
    pass "test6: local edit left untouched when no input was available"
  else
    fail "test6: local edit was altered despite no input"
  fi
  if grep -qi 're-run interactively' "$WORK/update.log" 2>/dev/null; then
    pass "test6: instructed the user to re-run interactively"
  else
    fail "test6: no 're-run interactively' guidance emitted"
  fi
  if no_bak "$T6"; then
    pass "test6 (T137 AC9): no input made no backup"
  else
    fail "test6 (T137 AC9): no input created a backup"; find "$T6" -name '*.bak*' -not -path '*/.git/*' >&2
  fi
fi

# =============================================================================
# Test 7 — THE REAL UPGRADE PATH (AC13/AC15). Install at the pre-T096 shape
# (`.claude/skills` a real directory holding stale content), run the REAL
# update.sh, and assert on what Claude Code would actually read: the content at
# `.claude/skills/brainstorming/SKILL.md` must equal the canon at
# `skills/brainstorming/SKILL.md`.
# =============================================================================
if fresh_target "target7"; then
  T7="$NEW_TARGET"
  rm -f "$T7/.claude/skills"
  mkdir -p "$T7/.claude/skills/brainstorming"
  printf 'STALE CONTENT FROM OLD INSTALL\n' > "$T7/.claude/skills/brainstorming/SKILL.md"

  RC=0
  run_update "$T7" /dev/null || RC=$?
  if [ "$RC" -eq 0 ]; then
    pass "test7: update.sh exited 0 on a pre-T096-shape install"
  else
    fail "test7: update.sh returned non-zero ($RC) — see $WORK/update.log"
    cat "$WORK/update.log" >&2
  fi
  if [ -L "$T7/.claude/skills" ] && [ "$(readlink "$T7/.claude/skills")" = "../skills" ]; then
    pass "test7: .claude/skills is the relative symlink after update"
  else
    fail "test7: .claude/skills is not '../skills' after update"
  fi
  # The assertion that matters: read through the path Claude Code uses.
  if [ -f "$T7/.claude/skills/brainstorming/SKILL.md" ] \
     && cmp -s "$T7/.claude/skills/brainstorming/SKILL.md" "$T7/skills/brainstorming/SKILL.md"; then
    pass "test7: .claude/skills/brainstorming/SKILL.md matches the plain-root canon"
  else
    fail "test7: content read via .claude/skills does not match the canon (stale canon regression)"
  fi
  if grep -q 'STALE CONTENT FROM OLD INSTALL' "$T7/.claude/skills.bak/brainstorming/SKILL.md" 2>/dev/null; then
    pass "test7: the stale directory was preserved at .claude/skills.bak, not deleted"
  else
    fail "test7: stale content was not preserved at .claude/skills.bak"
  fi
fi

# =============================================================================
# Test 8 — correct-shape install with the canon link DELETED: update.sh
# restores it when claude is requested this run (AC13, T096). T098 changed
# the plain case: with the links fully absent, `update.sh` no longer
# manufactures them back in — that is the presence-detection fix T098 was
# registered for, so the old "restore unconditionally" expectation here would
# now be wrong. Picking Claude Code on Reinstall still restores them (T098 AC4;
# it was `update.sh --harness claude` until T115 removed every option).
# =============================================================================
if fresh_target "target8"; then
  T8="$NEW_TARGET"
  rm -f "$T8/.claude/skills" "$T8/.claude/agents"

  RC=0
  run_update "$T8" /dev/null || RC=$?
  if [ "$RC" -eq 0 ]; then
    pass "test8: update.sh exited 0 with the canon links missing"
  else
    fail "test8: update.sh returned non-zero ($RC) — see $WORK/update.log"
  fi
  if [ ! -e "$T8/.claude/skills" ] && [ ! -e "$T8/.claude/agents" ]; then
    pass "test8: plain update.sh leaves fully-deleted, unrequested canon links absent (T098)"
  else
    fail "test8: canon symlinks were re-established without being requested or present (T098 regression)"
  fi

  RC=0
  ( cd "$T8" && SUPERVISOR_REPO="file://$FIXTURE" \
      run_in_pty '2\n1\n\n\n\n' "bash '$SETUP'" >"$WORK/update.log" 2>&1 ) || RC=$?
  if [ "$RC" -eq 0 ] \
     && [ "$(readlink "$T8/.claude/skills")" = "../skills" ] \
     && [ "$(readlink "$T8/.claude/agents")" = "../agents" ]; then
    pass "test8: Reinstall + picking Claude Code re-establishes both canon symlinks"
  else
    fail "test8: Reinstall + picking Claude Code did not restore the canon symlinks"
  fi
fi

# =============================================================================
# Test 9 — stale real directory that cannot be migrated (a .bak already exists):
# update.sh must FAIL rather than print "Update complete" over it (AC14).
# =============================================================================
if fresh_target "target9"; then
  T9="$NEW_TARGET"
  rm -f "$T9/.claude/skills"
  mkdir -p "$T9/.claude/skills" "$T9/.claude/skills.bak"
  printf 'STALE CONTENT FROM OLD INSTALL\n' > "$T9/.claude/skills/SKILL.md"

  RC=0
  run_update "$T9" /dev/null || RC=$?
  if [ "$RC" -ne 0 ]; then
    pass "test9: update.sh exits non-zero when a stale canon dir cannot be migrated (rc=$RC)"
  else
    fail "test9: update.sh reported success over a stale, unmigratable .claude/skills"
  fi
  if ! grep -q 'Update complete' "$WORK/update.log" 2>/dev/null; then
    pass "test9: no 'Update complete' printed over a stale canon"
  else
    fail "test9: printed 'Update complete' over a stale canon"
  fi
fi

# =============================================================================
# T137 SC2 / AC1 / AC4 — Update [o]verwrite backs up the edit under the kit
# version it replaces, BEFORE the kit copy lands, and names it in a [warn] line.
# =============================================================================
if fresh_target "t137-sc2"; then
  TO="$NEW_TARGET"
  KIT_A=$(git -C "$FIXTURE" rev-parse --short HEAD)
  LOCK_A=$(kit_commit "$TO/.claude/harness-lock.json")
  printf 'MY EDIT AT A\n' > "$TO/agents/backend.md"
  printf 'backend-agent-content-B\n' > "$FIXTURE/agents/backend.md"
  git -C "$FIXTURE" commit -q -am "upstream: backend.md at B"
  KIT_B=$(git -C "$FIXTURE" rev-parse --short HEAD)

  RC=0
  run_update "$TO" "$WORK/overwrite.in" || RC=$?
  if [ "$RC" -eq 0 ] && [ "$LOCK_A" = "$KIT_A" ] \
     && [ "$(cat "$TO/agents/backend.md.bak-$KIT_A" 2>/dev/null)" = 'MY EDIT AT A' ] \
     && [ "$(cat "$TO/agents/backend.md")" = 'backend-agent-content-B' ]; then
    pass "T137 SC2: [o]verwrite moved the edit to agents/backend.md.bak-$KIT_A, then installed kit $KIT_B"
  else
    fail "T137 SC2: [o]verwrite backup (rc=$RC lock-before=$LOCK_A A=$KIT_A)"
    ls -a "$TO/agents" >&2; cat "$WORK/update.log" >&2
  fi
  if tr -d '\r' < "$WORK/update.log" | grep -F '[warn]' | grep -qF "agents/backend.md.bak-$KIT_A"; then
    pass "T137 AC4: a [warn] line names the backup"
  else
    fail "T137 AC4: no [warn] line names agents/backend.md.bak-$KIT_A"
  fi
  if [ "$(kit_commit "$TO/.claude/harness-lock.json")" = "$KIT_B" ]; then
    pass "T137 AC1: Update re-records kit_commit=$KIT_B"
  else
    fail "T137 AC1: Update lock kit_commit is '$(kit_commit "$TO/.claude/harness-lock.json")', want $KIT_B"
  fi
  printf 'backend-agent-content\n' > "$FIXTURE/agents/backend.md"
  git -C "$FIXTURE" commit -q -am "upstream: restore backend.md to V1"
fi

# =============================================================================
# T137 edge — [o]verwrite when the backup cannot be made (folder not writable):
# the user's file stays as it is, never overwritten without a backup. A plain
# `cp` over the still-writable file WOULD succeed here, so only the guard keeps it.
# =============================================================================
if fresh_target "t137-robak"; then
  TR="$NEW_TARGET"
  printf 'EDIT THAT CANNOT BE BACKED UP\n' > "$TR/agents/backend.md"
  printf 'backend-agent-content-RO\n' > "$FIXTURE/agents/backend.md"
  git -C "$FIXTURE" commit -q -am "upstream: backend.md RO"
  chmod a-w "$TR/agents"
  RC=0
  run_update "$TR" "$WORK/overwrite.in" || RC=$?
  chmod u+w "$TR/agents"
  if [ "$(id -u)" -eq 0 ]; then
    pass "T137 edge: unwritable backup on [o]verwrite — skipped (root ignores directory permissions)"
  elif [ "$RC" -ne 0 ] \
       && [ "$(cat "$TR/agents/backend.md")" = 'EDIT THAT CANNOT BE BACKED UP' ] \
       && grep -q 'Could not back up' "$WORK/update.log"; then
    pass "T137 edge: failed backup on [o]verwrite -> edit kept, error named, non-zero exit (rc=$RC)"
  else
    fail "T137 edge: failed backup on [o]verwrite (rc=$RC)"; cat "$WORK/update.log" >&2
  fi
  printf 'backend-agent-content\n' > "$FIXTURE/agents/backend.md"
  git -C "$FIXTURE" commit -q -am "upstream: restore backend.md to V1"
fi

# =============================================================================
# T137 SC5 / AC6 — the lock's "kit_commit" is hex like a file hash, but it is
# never read as a file entry: nothing is created, removed or prompted about,
# and the rewritten lock holds it once, at the top level only.
# =============================================================================
if fresh_target "t137-sc5"; then
  TK="$NEW_TARGET"
  sed -i.orig 's/^  "kit_commit": "[^"]*"/  "kit_commit": "abc1234"/' "$TK/.claude/harness-lock.json"
  rm -f "$TK/.claude/harness-lock.json.orig"
  RC=0
  run_update "$TK" /dev/null || RC=$?
  _files_block=$(sed -n '/"files"/,$p' "$TK/.claude/harness-lock.json")
  if [ "$RC" -eq 0 ] && [ ! -e "$TK/kit_commit" ] \
     && ! grep -q 'kit_commit' "$WORK/update.log" \
     && ! printf '%s' "$_files_block" | grep -q 'kit_commit' \
     && [ "$(grep -c '"kit_commit"' "$TK/.claude/harness-lock.json")" -eq 1 ]; then
    pass "T137 SC5: kit_commit not treated as a file (no path, no prompt/removal line, not in \"files\")"
  else
    fail "T137 SC5: kit_commit leaked into the file entries (rc=$RC)"
    cat "$TK/.claude/harness-lock.json" >&2; cat "$WORK/update.log" >&2
  fi
fi

printf '\n----- summary: %d passed, %d failed -----\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
