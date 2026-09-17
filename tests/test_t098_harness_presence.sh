#!/bin/sh
# tests/test_t098_harness_presence.sh — POSIX-sh tests for T098: update.sh
# presence-detects `claude` like every other harness instead of installing
# the canon symlinks unconditionally.
#
#   AC1 setup.sh --harness codex then a no-flag update.sh: symlinks stay absent
#   AC2 claude install then update.sh: symlinks present, are symlinks, relative
#   AC3 repair path: a stale real .claude/skills dir is restored to a symlink
#   AC4 update.sh --harness claude installs symlinks on a project that never
#       had them, regardless of presence
#   AC5 the special case is removed from resolve_projection_harnesses, not
#       shadowed (grep on update.sh's own source)
#   AC6 anti-vacuity: reverting the fix in place makes AC1 go red again
#   AC7 a cap-validation abort under HARNESS_SKILL_BODY_CAP says the install
#       aborted and the tree may be partial
#   AC8 the existing rejection behaviour (non-integer/empty rejected, 0 still
#       disables the check) is unchanged
#
# Self-contained and offline: builds a throwaway local "harness" fixture repo
# and drives the REAL setup.sh/update.sh against scratch git targets via a
# file:// URL — the pattern already proven in tests/test_harness_projection.sh.
#
# Run: bash tests/test_t098_harness_presence.sh
set -u

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)
SETUP="$REPO_ROOT/setup.sh"
UPDATE="$REPO_ROOT/update.sh"

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1" >&2; }

WORK=$(mktemp -d "${TMPDIR:-/tmp}/t098-presence-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT INT TERM HUP
NO_CLONE="$WORK/should-not-exist-supervisor"

# ── Fixture harness repo ─────────────────────────────────────────────────────
FIXTURE="$WORK/fixture-repo"
mkdir -p "$FIXTURE/agents" \
         "$FIXTURE/skills/small-one" \
         "$FIXTURE/.claude/hooks" \
         "$FIXTURE/templates" \
         "$FIXTURE/lib"
cp "$REPO_ROOT/lib/merge-settings.py" "$FIXTURE/lib/merge-settings.py"
printf 'backend-agent-content\n' > "$FIXTURE/agents/backend.md"
printf 'hook-content\n'          > "$FIXTURE/.claude/hooks/example_hook.py"
printf 'template-content\n'      > "$FIXTURE/templates/PRD_template.md"
printf '{ "hooks": {} }\n'       > "$FIXTURE/.claude/settings.json"
printf 'GREENFIELD SUPERVISOR RULES\n' > "$FIXTURE/CLAUDE.md"
printf 'BROWNFIELD SUPERVISOR RULES\n' > "$FIXTURE/CLAUDE_LEGACY.md"
{
  printf -- '---\nname: small-one\ndescription: fixture skill\n---\n\nfixture body\n'
} > "$FIXTURE/skills/small-one/SKILL.md"

cat > "$FIXTURE/MANIFEST" <<'EOF'
# fixture MANIFEST (T097 destination-column form)
agents
skills          codex=.codex/skills
.claude/hooks
templates
EOF

git -C "$FIXTURE" init -q
git -C "$FIXTURE" config user.email "test@example.com"
git -C "$FIXTURE" config user.name "Test"
git -C "$FIXTURE" add -A
git -C "$FIXTURE" commit -q -m "fixture harness"

new_target() {
  _t="$WORK/$1"
  mkdir -p "$_t"
  git -C "$_t" init -q
  git -C "$_t" config user.email "test@example.com"
  git -C "$_t" config user.name "Test"
  printf '%s' "$_t"
}

run_setup() {
  _target="$1"; shift
  ( cd "$_target" \
      && SUPERVISOR_REPO="file://$FIXTURE" SUPERVISOR_PATH="$NO_CLONE" \
         bash "$SETUP" "$@" </dev/null >"$WORK/last.log" 2>&1 )
}
run_update() {
  _target="$1"; shift
  ( cd "$_target" \
      && SUPERVISOR_REPO="file://$FIXTURE" \
         bash "$UPDATE" "$@" </dev/null >"$WORK/last.log" 2>&1 )
}

# =============================================================================
# Test 1 (AC1) — codex-only project: symlinks stay absent across a no-flag update
# =============================================================================
T1=$(new_target target-codex-only)
if run_setup "$T1" --harness codex; then
  if [ ! -e "$T1/.claude/skills" ] && [ ! -e "$T1/.claude/agents" ]; then
    pass "AC1: symlinks absent immediately after setup.sh --harness codex"
  else
    fail "AC1: symlinks unexpectedly present right after setup"
  fi
  if run_update "$T1"; then
    if [ ! -e "$T1/.claude/skills" ] && [ ! -e "$T1/.claude/agents" ]; then
      pass "AC1: symlinks still absent after a no-flag update.sh (the reported defect)"
    else
      fail "AC1: symlinks reappeared after a no-flag update.sh — defect still present"
    fi
  else
    fail "AC1: update.sh failed — see $WORK/last.log"; cat "$WORK/last.log" >&2
  fi
else
  fail "AC1: setup.sh --harness codex failed"; cat "$WORK/last.log" >&2
fi

# =============================================================================
# Test 2 (AC2) — claude install: symlinks present, ARE symlinks, relative targets
# =============================================================================
T2=$(new_target target-claude)
if run_setup "$T2" --harness claude && run_update "$T2"; then
  if [ -L "$T2/.claude/skills" ] && [ -L "$T2/.claude/agents" ]; then
    pass "AC2: .claude/skills and .claude/agents are symlinks after update"
  else
    fail "AC2: .claude/skills or .claude/agents is not a symlink after update"
  fi
  SKILLS_TARGET=$(readlink "$T2/.claude/skills")
  AGENTS_TARGET=$(readlink "$T2/.claude/agents")
  if [ "$SKILLS_TARGET" = "../skills" ] && [ "$AGENTS_TARGET" = "../agents" ]; then
    pass "AC2: symlink targets are relative (../skills, ../agents)"
  else
    fail "AC2: symlink targets not relative (got '$SKILLS_TARGET', '$AGENTS_TARGET')"
  fi
else
  fail "AC2: setup+update for a claude install failed"; cat "$WORK/last.log" >&2
fi

# =============================================================================
# Test 3 (AC3) — repair path: a stale real dir is restored to a correct symlink
# =============================================================================
T3=$(new_target target-repair)
if run_setup "$T3" --harness claude; then
  rm "$T3/.claude/skills"
  mkdir -p "$T3/.claude/skills"
  printf 'stale\n' > "$T3/.claude/skills/stale.txt"
  if run_update "$T3"; then
    if [ -L "$T3/.claude/skills" ] && [ "$(readlink "$T3/.claude/skills")" = "../skills" ]; then
      pass "AC3: stale real .claude/skills dir was repaired to a relative symlink"
    else
      fail "AC3: stale real .claude/skills dir was not repaired"
    fi
  else
    fail "AC3: update.sh failed on the repair case"; cat "$WORK/last.log" >&2
  fi
else
  fail "AC3: setup.sh --harness claude failed"; cat "$WORK/last.log" >&2
fi

# =============================================================================
# Test 3b (AC3) — repair path: a broken (dangling) symlink is also detected as
# present and repaired, not just a real directory. -e alone misses a dangling
# link since it follows the target — this asserts the -L fallback is in place.
# =============================================================================
T3B=$(new_target target-repair-broken-link)
if run_setup "$T3B" --harness claude; then
  rm "$T3B/.claude/agents"
  ln -s "../nonexistent-target" "$T3B/.claude/agents"
  if run_update "$T3B"; then
    if [ -L "$T3B/.claude/agents" ] && [ "$(readlink "$T3B/.claude/agents")" = "../agents" ]; then
      pass "AC3: a broken/dangling symlink was detected as present and repaired"
    else
      fail "AC3: a broken/dangling symlink was not repaired"
    fi
  else
    fail "AC3: update.sh failed on the broken-symlink repair case"; cat "$WORK/last.log" >&2
  fi
else
  fail "AC3: setup.sh --harness claude failed (broken-link case)"; cat "$WORK/last.log" >&2
fi

# =============================================================================
# Test 4 (AC4) — explicit --harness claude installs symlinks regardless of
# prior presence, on a project that never had claude
# =============================================================================
T4=$(new_target target-explicit-claude)
if run_setup "$T4" --harness codex; then
  if run_update "$T4" --harness claude; then
    if [ -L "$T4/.claude/skills" ] && [ -L "$T4/.claude/agents" ]; then
      pass "AC4: 'update.sh --harness claude' installs symlinks on a codex-only project"
    else
      fail "AC4: symlinks not installed despite explicit --harness claude"
    fi
  else
    fail "AC4: 'update.sh --harness claude' failed"; cat "$WORK/last.log" >&2
  fi
else
  fail "AC4: setup.sh --harness codex failed"; cat "$WORK/last.log" >&2
fi

# =============================================================================
# Test 5 (AC5) — the special case is removed from resolve_projection_harnesses,
# not shadowed by a parallel rule
# =============================================================================
RESOLVE_BODY=$(awk '/^resolve_projection_harnesses\(\) \{/,/^\}/' "$UPDATE")
if printf '%s' "$RESOLVE_BODY" | grep -q '\[ "\$_h" = "claude" \] && continue'; then
  fail "AC5: 'claude' special-case continue still present in resolve_projection_harnesses"
else
  pass "AC5: no claude special-case 'continue' inside resolve_projection_harnesses"
fi

# =============================================================================
# Test 6 (AC6) — anti-vacuity: revert the fix in place, AC1 goes red again
# =============================================================================
# Reconstructs the pre-T098 update.sh by re-inserting the exact special case
# this task removes and un-gating the symlink install call, via a literal
# string substitution on the CURRENT fixed source (self-contained: does not
# depend on git history staying in any particular shape).
# update.sh sources lib/harness-fetch.sh relative to its OWN location
# ($SCRIPT_DIR/lib/harness-fetch.sh), so the probe script must live in a
# directory with a sibling lib/ — a symlink onto the real one is enough.
REVERT_DIR="$WORK/revert-probe"
mkdir -p "$REVERT_DIR"
ln -s "$REPO_ROOT/lib" "$REVERT_DIR/lib"
REVERTED_UPDATE="$REVERT_DIR/update.sh"
python3 - "$UPDATE" "$REVERTED_UPDATE" <<'PYEOF'
import sys
src, dst = sys.argv[1], sys.argv[2]
text = open(src).read()

needle_a = '  for _h in $VALID_HARNESSES; do\n    _want=0\n'
replacement_a = '  for _h in $VALID_HARNESSES; do\n    [ "$_h" = "claude" ] && continue\n    _want=0\n'
assert text.count(needle_a) == 1, "resolve_projection_harnesses anchor not found exactly once"
text = text.replace(needle_a, replacement_a, 1)

needle_b = '  case " $PROJECTION_HARNESSES " in\n    *" claude "*) harness_install_canon_symlinks . ; claude_linked=1 ;;\n  esac\n'
replacement_b = '  harness_install_canon_symlinks .\n  claude_linked=1\n'
assert text.count(needle_b) == 1, "symlink-install gate anchor not found exactly once"
text = text.replace(needle_b, replacement_b, 1)

open(dst, 'w').write(text)
PYEOF
if [ ! -s "$REVERTED_UPDATE" ]; then
  fail "AC6: revert probe generation failed — see script output above"
fi
chmod +x "$REVERTED_UPDATE"
if diff -q "$UPDATE" "$REVERTED_UPDATE" >/dev/null 2>&1; then
  fail "AC6: revert probe is byte-identical to the fixed update.sh — probe is not testing anything"
elif ! grep -q '\[ "\$_h" = "claude" \] && continue' "$REVERTED_UPDATE"; then
  fail "AC6: revert probe does not contain the special case being tested against"
fi

T6=$(new_target target-anti-vacuity)
if run_setup "$T6" --harness codex; then
  ( cd "$T6" && SUPERVISOR_REPO="file://$FIXTURE" bash "$REVERTED_UPDATE" </dev/null >"$WORK/last.log" 2>&1 )
  if [ -e "$T6/.claude/skills" ] || [ -e "$T6/.claude/agents" ]; then
    pass "AC6: reverting the fix in place makes AC1 go red again (symlinks reappear)"
  else
    fail "AC6: anti-vacuity probe did not reproduce the original defect — probe is not testing the real branch"
  fi
else
  fail "AC6: setup.sh --harness codex failed for the anti-vacuity probe"; cat "$WORK/last.log" >&2
fi

# =============================================================================
# Test 7 (AC7) — a mid-install cap-validation abort says it aborted
# =============================================================================
T7=$(new_target target-abort)
RC=0
( cd "$T7" && HARNESS_SKILL_BODY_CAP=abc SUPERVISOR_REPO="file://$FIXTURE" SUPERVISOR_PATH="$NO_CLONE" \
    bash "$SETUP" --harness codex </dev/null >"$WORK/last.log" 2>&1 ) || RC=$?
if [ "$RC" -ne 0 ]; then
  pass "AC7: setup.sh exits non-zero (rc=$RC) on a bad HARNESS_SKILL_BODY_CAP"
else
  fail "AC7: setup.sh exited 0 despite a bad HARNESS_SKILL_BODY_CAP"
fi
if grep -qi 'abort' "$WORK/last.log" 2>/dev/null; then
  pass "AC7: the failure message states the install/update aborted"
else
  fail "AC7: no 'aborted' message emitted on the mid-install cap failure"
fi

# =============================================================================
# Test 8 (AC8) — existing rejection behaviour unchanged
# =============================================================================
T8A=$(new_target target-negative-cap)
RC=0
( cd "$T8A" && HARNESS_SKILL_BODY_CAP="-1" SUPERVISOR_REPO="file://$FIXTURE" SUPERVISOR_PATH="$NO_CLONE" \
    bash "$SETUP" --harness codex </dev/null >"$WORK/last.log" 2>&1 ) || RC=$?
if [ "$RC" -ne 0 ]; then
  pass "AC8: a non-integer HARNESS_SKILL_BODY_CAP ('-1') is still rejected by name (rc=$RC)"
else
  fail "AC8: HARNESS_SKILL_BODY_CAP=-1 was NOT rejected"
fi
if grep -q "HARNESS_SKILL_BODY_CAP must be a non-negative integer" "$WORK/last.log" 2>/dev/null; then
  pass "AC8: rejection names HARNESS_SKILL_BODY_CAP explicitly"
else
  fail "AC8: rejection message does not name HARNESS_SKILL_BODY_CAP"
fi

T8B=$(new_target target-cap-zero)
if ( cd "$T8B" && HARNESS_SKILL_BODY_CAP=0 SUPERVISOR_REPO="file://$FIXTURE" SUPERVISOR_PATH="$NO_CLONE" \
       bash "$SETUP" --harness codex </dev/null >"$WORK/last.log" 2>&1 ); then
  pass "AC8: HARNESS_SKILL_BODY_CAP=0 still disables the check (setup succeeds)"
else
  fail "AC8: HARNESS_SKILL_BODY_CAP=0 unexpectedly failed"; cat "$WORK/last.log" >&2
fi

# =============================================================================
# Test 9 (AC9) — the closing summary must not claim a projection that did not
# happen. `claude` is resolved into PROJECTION_HARNESSES but deliberately
# skipped by the projection loop, so naming it under "Re-projected harness(es)"
# is a false statement about work performed (found at the CLI during /verify).
# =============================================================================
T9=$(new_target target-summary-claude)
if run_setup "$T9"; then
  if run_update "$T9"; then
    if grep -q "Re-projected harness(es):.*claude" "$WORK/last.log"; then
      fail "AC9: summary claims 'Re-projected harness(es): claude' but claude is never projected"
    else
      pass "AC9: claude is not listed as re-projected"
    fi
    if grep -q "re-pointed .claude/{skills,agents}" "$WORK/last.log"; then
      pass "AC9: the claude symlink step is reported on its own terms"
    else
      fail "AC9: no line reports what was actually done for claude"
    fi
  else
    fail "AC9: update.sh failed — see $WORK/last.log"; cat "$WORK/last.log" >&2
  fi
fi

# A codex+claude project must still name codex (and only codex) as projected.
T9B=$(new_target target-summary-both)
if run_setup "$T9B" --harness claude --harness codex && run_update "$T9B"; then
  if grep -q "Re-projected harness(es): codex$" "$WORK/last.log"; then
    pass "AC9: a claude+codex project reports exactly the projected set (codex)"
  else
    fail "AC9: projected-set summary wrong for claude+codex"
    grep "Re-projected" "$WORK/last.log" >&2 || true
  fi
fi

# =============================================================================
# Test 10 (AC10) — both canon links deleted on a claude project: the links
# correctly stay absent (fully-absent is indistinguishable from "never had
# claude"), but the run must say so and name the way back, instead of printing
# a bare "Update complete" with no hint that --harness claude would restore it.
# =============================================================================
T10=$(new_target target-empty-set)
if run_setup "$T10"; then
  rm -f "$T10/.claude/skills" "$T10/.claude/agents"
  if run_update "$T10"; then
    if grep -q "No harness detected in this project" "$WORK/last.log"; then
      pass "AC10: an empty resolved set is reported, not silent"
    else
      fail "AC10: nothing reported when no harness was requested or present"
      cat "$WORK/last.log" >&2
    fi
    if grep -q -- "--harness <name>" "$WORK/last.log" \
       && grep -q "Valid harnesses: claude codex" "$WORK/last.log"; then
      pass "AC10: the message names the remedy and the valid harnesses"
    else
      fail "AC10: the message does not name --harness or the valid values"
    fi
    if [ ! -e "$T10/.claude/skills" ] && [ ! -e "$T10/.claude/agents" ]; then
      pass "AC10: the links still stay absent (behaviour unchanged, only reporting added)"
    else
      fail "AC10: links were re-created — the reporting fix changed behaviour"
    fi
  else
    fail "AC10: update.sh failed — see $WORK/last.log"; cat "$WORK/last.log" >&2
  fi
fi

# ── Summary ───────────────────────────────────────────────────────────────────
printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
