#!/bin/sh
# tests/test_harness_projection.sh — POSIX-sh tests for T097's per-harness
# install projection, the `--harness` flag, and the AGENTS.md correction.
#
# Hard-Stop Gate 5 coverage — at least one automated test per defect plus the
# criteria the guide singles out:
#   Defect A (AGENTS.md stated a falsehood about Codex)      -> Test 1
#   Defect B (no projection mechanism existed)               -> Test 3  (AC2)
#   AC1  no --harness flag => today's install, unchanged     -> Test 2
#   AC4  oversize skill fails LOUDLY and by name             -> Test 4
#   AC5  anti-vacuity: cap disabled => installs silently     -> Test 5
#   AC6  unknown harness name exits non-zero, names valid    -> Test 6
#   AC7  a second identical run is idempotent                -> Test 7
#   AC8  projections are gitignored downstream               -> Test 8
#   AC9  update.sh leaves exactly one live set of skills     -> Test 9
#   AC10 harness-lock keys are unaffected by the new column  -> Test 10
#
# Self-contained and offline: builds a throwaway local "harness" fixture repo
# (including a deliberately oversize skill) and runs the REAL setup.sh/update.sh
# against scratch git targets via a file:// URL — the pattern already proven in
# tests/test_setup.sh and tests/test_update.sh.
#
# Run: bash tests/test_harness_projection.sh
set -u

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)
SETUP="$REPO_ROOT/setup.sh"
UPDATE="$REPO_ROOT/update.sh"

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1" >&2; }

WORK=$(mktemp -d "${TMPDIR:-/tmp}/harness-projection-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT INT TERM HUP
NO_CLONE="$WORK/should-not-exist-supervisor"

# ── Fixture harness repo ─────────────────────────────────────────────────────
# Three skills: two comfortably under Codex's 8192-byte cap, one deliberately
# ~9 KB so the cap has something real to catch. The oversize body is generated,
# not hand-written, so the fixture cannot silently drift under the cap.
FIXTURE="$WORK/fixture-repo"
mkdir -p "$FIXTURE/agents" \
         "$FIXTURE/skills/small-one" \
         "$FIXTURE/skills/small-two" \
         "$FIXTURE/skills/oversize-skill" \
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

mk_skill() {
  _dir="$1"; _name="$2"; _filler_lines="$3"
  {
    printf -- '---\nname: %s\ndescription: fixture skill %s\n---\n\n' "$_name" "$_name"
    _i=0
    while [ "$_i" -lt "$_filler_lines" ]; do
      printf 'filler line %03d: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n' "$_i"
      _i=$((_i + 1))
    done
  } > "$_dir/SKILL.md"
}
mk_skill "$FIXTURE/skills/small-one"      small-one       5
mk_skill "$FIXTURE/skills/small-two"      small-two       5
mk_skill "$FIXTURE/skills/oversize-skill" oversize-skill  130

OVERSIZE_BYTES=$(wc -c < "$FIXTURE/skills/oversize-skill/SKILL.md" | tr -d ' ')
if [ "$OVERSIZE_BYTES" -le 8192 ]; then
  printf 'FATAL: oversize fixture is only %s bytes, not over the 8192 cap\n' "$OVERSIZE_BYTES" >&2
  exit 2
fi

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

# Run setup.sh non-interactively in $1, extra args after; log to $WORK/last.log.
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
# Test 1 (Defect A) — AGENTS.md tells the truth about Codex skills
# =============================================================================
AGENTS_MD="$REPO_ROOT/AGENTS.md"
if grep -qF "Codex has no equivalent of Claude Code's hooks, skills, or" "$AGENTS_MD"; then
  fail "Defect A: AGENTS.md still claims Codex has no skills"
else
  pass "Defect A: the false 'Codex has no ... skills' sentence is gone"
fi
if grep -qF ".codex/skills" "$AGENTS_MD"; then
  pass "Defect A: AGENTS.md names .codex/skills/"
else
  fail "Defect A: AGENTS.md does not name .codex/skills/"
fi
if grep -qE '8 ?KB' "$AGENTS_MD"; then
  pass "Defect A: AGENTS.md states the 8 KB skill-body cap"
else
  fail "Defect A: AGENTS.md does not state the 8 KB cap"
fi
# The TRUE half of the original sentence must survive verbatim.
_missing_true=""
for _term in "code-review" "security-review" "verify" "ship" "migration-safety" "git-guardrails"; do
  grep -qF "$_term" "$AGENTS_MD" || _missing_true="$_missing_true $_term"
done
if [ -z "$_missing_true" ]; then
  pass "Defect A: the true limits sentence survives (hooks + all 5 gates + git-guardrails)"
else
  fail "Defect A: limits section lost:$_missing_true"
fi

# =============================================================================
# Test 2 (AC1) — no --harness flag => today's install, no vendor dirs
# =============================================================================
T2=$(new_target target-default)
if run_setup "$T2"; then
  _ok=1
  [ -d "$T2/skills" ]  || { _ok=0; }
  [ -d "$T2/agents" ]  || { _ok=0; }
  [ -L "$T2/.claude/skills" ] || { _ok=0; }
  [ -L "$T2/.claude/agents" ] || { _ok=0; }
  [ -e "$T2/.codex" ]  && _ok=0   # must NOT appear without the flag
  if [ "$_ok" -eq 1 ]; then
    pass "AC1: default install unchanged — canon + .claude symlinks, and no .codex/"
  else
    fail "AC1: default install differs from the pre-T097 shape"
  fi
else
  fail "AC1: default setup.sh run failed"
fi
# The destination column must never leak into an installed path.
if [ -e "$T2/skills" ] && [ ! -e "$T2/skills          codex=.codex" ]; then
  pass "AC1: the destination column is not treated as part of the path"
else
  fail "AC1: MANIFEST's second column leaked into the installed path"
fi

# =============================================================================
# Test 3 (Defect B / AC2) — --harness codex projects real copies
# =============================================================================
T3=$(new_target target-codex)
if run_setup "$T3" --harness codex; then
  if [ -d "$T3/.codex/skills/small-one" ] && [ -d "$T3/.codex/skills/small-two" ]; then
    pass "AC2: .codex/skills/ contains every under-cap skill"
  else
    fail "AC2: .codex/skills/ is missing under-cap skills"
  fi
  if [ -f "$T3/.codex/skills/small-one/SKILL.md" ] && [ -z "$(find "$T3/.codex" -type l)" ]; then
    pass "AC2: projected entries are real file copies, not symlinks"
  else
    fail "AC2: projection produced symlinks or no regular files"
  fi
  # 'claude' was not requested, so its symlinks must not be created.
  if [ ! -L "$T3/.claude/skills" ]; then
    pass "AC2: an unrequested harness receives no directories (.claude/skills absent)"
  else
    fail "AC2: .claude/skills was created for a harness that was not selected"
  fi
else
  fail "AC2: setup.sh --harness codex failed"
fi

# =============================================================================
# Test 4 (AC4) — an oversize skill fails LOUDLY, by name and size, never truncated
# =============================================================================
if [ -e "$T3/.codex/skills/oversize-skill" ]; then
  fail "AC4: the oversize skill was installed anyway"
else
  pass "AC4: the oversize skill is absent (skipped, not installed)"
fi
if grep -q "oversize-skill" "$WORK/last.log" 2>/dev/null; then
  pass "AC4: the warning names the offending skill"
else
  fail "AC4: no warning naming 'oversize-skill'"
fi
if grep -q "$OVERSIZE_BYTES" "$WORK/last.log" 2>/dev/null; then
  pass "AC4: the warning states the skill's byte size ($OVERSIZE_BYTES)"
else
  fail "AC4: the warning does not state the skill's size"
fi
if grep -qi "8192" "$WORK/last.log" 2>/dev/null; then
  pass "AC4: the warning states the cap it exceeded"
else
  fail "AC4: the warning does not state the cap"
fi
# Never truncated: nothing under the cap is left behind pretending to be it.
if [ ! -f "$T3/.codex/skills/oversize-skill/SKILL.md" ]; then
  pass "AC4: no truncated copy of the oversize skill exists"
else
  fail "AC4: a (possibly truncated) oversize-skill body was written"
fi

# =============================================================================
# Test 5 (AC5, anti-vacuity) — with the cap disabled the SAME fixture installs
# silently. If this test fails, Test 4 was passing for some reason other than
# the size check, and the check is not load-bearing.
# =============================================================================
T5=$(new_target target-nocap)
if ( cd "$T5" \
      && SUPERVISOR_REPO="file://$FIXTURE" SUPERVISOR_PATH="$NO_CLONE" \
         HARNESS_SKILL_BODY_CAP=0 \
         bash "$SETUP" --harness codex </dev/null >"$WORK/nocap.log" 2>&1 ); then
  if [ -f "$T5/.codex/skills/oversize-skill/SKILL.md" ]; then
    pass "AC5: with the cap disabled the oversize skill installs — the check is load-bearing"
  else
    fail "AC5: oversize skill still absent with the cap disabled (Test 4 may be vacuous)"
  fi
  if grep -q "oversize-skill" "$WORK/nocap.log" 2>/dev/null; then
    fail "AC5: a warning was still emitted with the cap disabled"
  else
    pass "AC5: it installs SILENTLY with the cap disabled — no warning at all"
  fi
  # And the installed body must be the whole file, byte for byte.
  _installed=$(wc -c < "$T5/.codex/skills/oversize-skill/SKILL.md" | tr -d ' ')
  if [ "$_installed" = "$OVERSIZE_BYTES" ]; then
    pass "AC5: the body is copied whole ($_installed bytes) — never truncated"
  else
    fail "AC5: installed body is $_installed bytes, expected $OVERSIZE_BYTES"
  fi
else
  fail "AC5: setup.sh with HARNESS_SKILL_BODY_CAP=0 failed"
fi

# =============================================================================
# Test 6 (AC6) — an unknown harness name exits non-zero and names the valid set
# =============================================================================
T6=$(new_target target-unknown)
if run_setup "$T6" --harness banana; then
  fail "AC6: --harness banana exited 0"
else
  pass "AC6: --harness banana exits non-zero"
fi
if grep -q "banana" "$WORK/last.log" && grep -q "claude codex" "$WORK/last.log"; then
  pass "AC6: the error names the bad value and the valid harnesses"
else
  fail "AC6: the error does not name the bad value and/or the valid harnesses"
fi
# It must fail BEFORE writing anything — not produce a silently empty install.
if [ ! -e "$T6/.codex" ] && [ ! -e "$T6/skills" ] && [ ! -e "$T6/CLAUDE.md" ]; then
  pass "AC6: nothing was written — no silently empty install"
else
  fail "AC6: files were written despite the unknown harness"
fi
# A --harness with no value must be rejected too, not swallow the next flag.
T6B=$(new_target target-novalue)
if run_setup "$T6B" --harness; then
  fail "AC6: bare --harness with no value exited 0"
else
  pass "AC6: bare --harness with no value exits non-zero"
fi
# An EMPTY value is the dangerous shape, found by Stage 5 /verify: it cannot be
# caught by the validation loop, because `for h in $HARNESSES` word-splits an
# empty entry away (validating zero names) while the string stays non-empty and
# so suppresses the default-to-claude fallback. Before the fix this exited 0 and
# produced an install with NO harness directories at all — no .claude/skills, no
# .claude/agents, no .codex — which is exactly the silently-empty install AC6
# exists to forbid, and the user's original "skill is not available" symptom.
for _empty_form in '--harness ""' '--harness='; do
  T6C=$(new_target "target-empty-$(printf '%s' "$_empty_form" | tr -cd 'a-z=')")
  if [ "$_empty_form" = '--harness=' ]; then
    if run_setup "$T6C" --harness=; then
      fail "AC6: $_empty_form exited 0 (silently empty install)"
    else
      pass "AC6: $_empty_form exits non-zero"
    fi
  else
    if run_setup "$T6C" --harness ""; then
      fail "AC6: $_empty_form exited 0 (silently empty install)"
    else
      pass "AC6: $_empty_form exits non-zero"
    fi
  fi
  if [ ! -L "$T6C/.claude/skills" ] && [ ! -e "$T6C/.codex" ] && [ ! -e "$T6C/CLAUDE.md" ]; then
    pass "AC6: $_empty_form wrote nothing — no harness-less install"
  else
    fail "AC6: $_empty_form produced an install with no usable harness directory"
  fi
done
# update.sh must reject the same shape rather than silently doing nothing.
T6D=$(new_target target-empty-update)
run_setup "$T6D" --harness codex
if run_update "$T6D" --harness ""; then
  fail "AC6: update.sh --harness \"\" exited 0"
else
  pass "AC6: update.sh rejects an empty --harness value too"
fi

# =============================================================================
# Test 7 (AC7) — a second identical run changes nothing
# =============================================================================
SNAP1="$WORK/snap1"; SNAP2="$WORK/snap2"
( cd "$T3" && find .codex -type f -exec sha256sum {} \; | LC_ALL=C sort ) > "$SNAP1"
if run_setup "$T3" --harness codex; then
  ( cd "$T3" && find .codex -type f -exec sha256sum {} \; | LC_ALL=C sort ) > "$SNAP2"
  if diff -q "$SNAP1" "$SNAP2" >/dev/null 2>&1; then
    pass "AC7: a second --harness codex run is byte-for-byte idempotent"
  else
    fail "AC7: the second run changed .codex/ contents"
    diff -u "$SNAP1" "$SNAP2" >&2
  fi
  # No orphan: a file that vanishes upstream must not survive a re-projection.
  printf 'stale\n' > "$T3/.codex/skills/orphan-marker"
  run_setup "$T3" --harness codex
  if [ ! -e "$T3/.codex/skills/orphan-marker" ]; then
    pass "AC7: re-projection removes orphaned files rather than accumulating them"
  else
    fail "AC7: an orphaned file survived re-projection"
  fi
else
  fail "AC7: the second setup.sh --harness codex run failed"
fi

# =============================================================================
# Test 8 (AC8) — projections are gitignored, and the entry is not duplicated
# =============================================================================
if [ -f "$T3/.gitignore" ] && grep -qF ".codex/skills/" "$T3/.gitignore"; then
  pass "AC8: .codex/skills/ is gitignored downstream"
else
  fail "AC8: .codex/skills/ is not gitignored"
fi
_n=$(grep -cFx ".codex/skills/" "$T3/.gitignore" 2>/dev/null || printf '0')
if [ "$_n" = "1" ]; then
  pass "AC8: repeated runs do not duplicate the .gitignore entry (found $_n)"
else
  fail "AC8: .gitignore entry appears $_n times, expected exactly 1"
fi
# Canon stays committable; only the projection is ignored.
if ! grep -qE '^skills/?$' "$T3/.gitignore" 2>/dev/null; then
  pass "AC8: the canonical skills/ is NOT gitignored — canon stays committed"
else
  fail "AC8: the canonical skills/ was gitignored"
fi

# =============================================================================
# Test 9 (AC9) — update.sh leaves exactly one live set of skills
# =============================================================================
# Upstream renames a skill; update.sh must not leave the old name behind.
git -C "$FIXTURE" mv skills/small-two skills/renamed-two
git -C "$FIXTURE" commit -q -m "rename small-two -> renamed-two"
if run_update "$T3"; then
  if [ -d "$T3/.codex/skills/renamed-two" ] && [ ! -e "$T3/.codex/skills/small-two" ]; then
    pass "AC9: update.sh re-projects an already-present harness with no --harness flag"
  else
    fail "AC9: update.sh left the old skill name live alongside the new one"
  fi
  # Exactly one live set: after re-projection the vendor directory holds exactly
  # the fresh upstream's under-cap skills — no stale entry surviving beside them.
  # Compared against UPSTREAM: the PROJECTION is replaced wholesale and can never
  # hold two live sets.
  _upstream=$( cd "$FIXTURE/skills" && find . -mindepth 1 -maxdepth 1 -printf '%f\n' | LC_ALL=C sort | grep -v '^oversize-skill$' )
  _proj=$( cd "$T3/.codex/skills" && find . -mindepth 1 -maxdepth 1 -printf '%f\n' | LC_ALL=C sort )
  if [ "$_upstream" = "$_proj" ]; then
    pass "AC9: the projection equals fresh upstream's under-cap set — one live set"
  else
    fail "AC9: projection diverges from upstream (upstream=[$_upstream] projection=[$_proj])"
  fi
  # T113 / ADR-0002 reverses ADR-0001's "never deletes": a skill the kit dropped
  # and the user never edited is removed from the canon too, so the canon and
  # the projection agree.
  if [ ! -e "$T3/skills/small-two" ]; then
    pass "AC9: canon drops the unedited upstream-removed skill (T113) — canon and projection agree"
  else
    fail "AC9: update.sh left an unedited, upstream-removed skill in the canon"
  fi
else
  fail "AC9: update.sh failed on a projected install"
fi
# A project that never asked for codex must not gain it from update.sh.
if run_update "$T2"; then
  if [ ! -e "$T2/.codex" ]; then
    pass "AC9: update.sh does not add a harness the project never selected"
  else
    fail "AC9: update.sh created .codex/ in a Claude-only project"
  fi
else
  fail "AC9: update.sh failed on the default install"
fi

# =============================================================================
# Test 10 (AC10) — the lock is unaffected by the new column and by projections
# =============================================================================
LOCK2="$T2/.claude/harness-lock.json"
LOCK3="$T3/.claude/harness-lock.json"
if grep -q '"skills/small-one/SKILL.md"' "$LOCK2" 2>/dev/null; then
  pass "AC10: lock keys use MANIFEST field 1 — the destination column is not in the key"
else
  fail "AC10: lock does not contain the expected canonical key"
fi
if grep -q 'codex=' "$LOCK2" 2>/dev/null; then
  fail "AC10: the destination column leaked into harness-lock.json"
else
  pass "AC10: no destination-column text leaked into harness-lock.json"
fi
if grep -q '\.codex/skills' "$LOCK3" 2>/dev/null; then
  fail "AC10: generated projections were recorded in the lock (they are gitignored)"
else
  pass "AC10: projections are not lock-tracked — only the canon they derive from is"
fi
# A stale lock is still DETECTED, not silently mismatched on every file: edit one
# tracked file and confirm update.sh reports a conflict for that file only.
printf 'locally customised\n' >> "$T2/agents/backend.md"
run_update "$T2"
if grep -q "conflict: 'agents/backend.md'" "$WORK/last.log"; then
  _conflicts=$(grep -c "^.*conflict: " "$WORK/last.log")
  if [ "$_conflicts" = "1" ]; then
    pass "AC10: hash comparison still works — exactly 1 conflict for the 1 edited file"
  else
    fail "AC10: $_conflicts conflicts reported, expected exactly 1"
  fi
else
  fail "AC10: an edited tracked file was not detected as a conflict"
fi

# =============================================================================
# Stage 4 review hardening (P2). Both of these were empirically reproduced during
# review before being fixed, so each test guards a real, demonstrated failure.
# =============================================================================
S4="$WORK/stage4"; rm -rf "$S4"; mkdir -p "$S4/src/skills/big" "$S4/out" "$S4/esc/sub"
head -c 20000 /dev/zero | tr '\0' 'x' > "$S4/src/skills/big/SKILL.md"
printf 'skills\tcodex=.codex/skills\n' > "$S4/mani"

# A malformed cap must fail loudly instead of falling through to "no cap" and
# installing the oversize skill it was supposed to stop.
if ( . "$REPO_ROOT/lib/harness-fetch.sh"
     HARNESS_SKILL_BODY_CAP=abc harness_project_manifest "$S4/src" "$S4/out" "$S4/mani" codex
   ) >"$S4/log" 2>&1; then
  fail "P2: a non-numeric HARNESS_SKILL_BODY_CAP was accepted"
elif grep -q 'must be a non-negative integer' "$S4/log" && [ ! -e "$S4/out/.codex/skills/big" ]; then
  pass "P2: a malformed cap fails loudly by name and installs nothing"
else
  fail "P2: malformed cap did not produce a named error, or installed the oversize skill anyway"
fi

# A destination that escapes the target tree must be refused before `rm -rf`.
printf 'skills\tcodex=../ESCAPED\n' > "$S4/mani_esc"
( . "$REPO_ROOT/lib/harness-fetch.sh"
  cd "$S4/esc/sub" && harness_project_manifest "$S4/src" . "$S4/mani_esc" codex
) >"$S4/log2" 2>&1
if [ -e "$S4/esc/ESCAPED" ]; then
  fail "P2: a '..' destination escaped the target tree"
elif grep -q 'must be a relative path inside the project' "$S4/log2"; then
  pass "P2: a '..' destination is refused by name and nothing is written outside the target"
else
  fail "P2: traversal was not written, but no named error explained why"
fi

printf '\n----------------------------------------\n'

printf 'test_harness_projection.sh: %d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ] || exit 1
