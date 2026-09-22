#!/bin/sh
# tests/test_update_claude_md.sh — POSIX-sh test harness for T110
#
# Self-contained and offline (file:// repo URL, no network). Builds a throwaway
# local git "harness" fixture, runs the REAL setup.sh to produce an installed
# target repo (greenfield or brownfield) + .claude/harness-lock.json, then
# exercises update.sh's CLAUDE.md handling:
#   SC1. greenfield, unedited          -> CLAUDE.md == fresh upstream CLAUDE.md, no prompt
#   SC2. brownfield (pty, answer "2")  -> CLAUDE.md == fresh upstream CLAUDE_LEGACY.md,
#                                          never the greenfield content
#   SC3. user-edited CLAUDE.md         -> conflict prompt; no input -> exit 2, edit kept
#   SC4. install; update; update       -> recorded claude_md_source identical both times
#   SC5. lock predates the source field -> heading inference still applies it
#   SC6. old lock + hand-edited unknown heading -> conflict path, exit 2, file unchanged
#   SC7. brownfield + edited CLAUDE.md line 1, answer "o" -> recorded source
#        (CLAUDE_LEGACY.md) is honoured over heading inference
#   SC8. lock's claude_md_source outside {CLAUDE.md, CLAUDE_LEGACY.md},
#        pointing at a real scratch file -> rejected, never read into CLAUDE.md
#   M1.  mutation: ignore recorded source, always resolve greenfield -> SC2 must fail
#   M2.  mutation: disable the recorded-source branch entirely -> SC7 must fail
#   M3.  mutation: remove the allowlist check on the recorded source -> SC8 must fail
#
# Brownfield installs and conflict answers are driven through a real pty
# (`script -qec`) because setup.sh's prompts read /dev/tty (T114) and are
# unreachable from a pipe (memory/learnings.md). Mutants are built on
# lib/harness-update.sh, where the update logic lives since T114.
#
# Run: bash tests/test_update_claude_md.sh   (or: sh tests/test_update_claude_md.sh)
set -u

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)
SETUP="$REPO_ROOT/setup.sh"
UPDATE="$REPO_ROOT/update.sh"
UPDATE_LIB="$REPO_ROOT/lib/harness-update.sh"
# shellcheck source=tests/lib/pty.sh
. "$SCRIPT_DIR/lib/pty.sh"
detach_from_terminal "$0" "$@"

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

WORK=$(mktemp -d "${TMPDIR:-/tmp}/update-claude-md-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT INT TERM HUP

# Read a single top-level string field (hash or claude_md_source) from a lock.
lock_field() {
  grep -F "\"$2\": \"" "$1" 2>/dev/null | head -n1 | sed -e 's/.*: "//' -e 's/".*//'
}

# ── Build a minimal fixture "harness" repo (the fresh upstream update fetches)
# GREENFIELD_MARK/BROWNFIELD_MARK let each test append a distinguishable line
# to the relevant source before committing an "upstream changed" state.
FIXTURE="$WORK/fixture-repo"
build_fixture() {
  mkdir -p "$FIXTURE/agents" "$FIXTURE/skills/brainstorming" "$FIXTURE/templates"
  printf 'agent-content\n'    > "$FIXTURE/agents/backend.md"
  printf 'skill-content\n'    > "$FIXTURE/skills/brainstorming/SKILL.md"
  printf 'template-content\n' > "$FIXTURE/templates/PRD_template.md"
  printf 'GREENFIELD SUPERVISOR RULES\nv1\n' > "$FIXTURE/CLAUDE.md"
  printf 'BROWNFIELD SUPERVISOR RULES\nv1\n' > "$FIXTURE/CLAUDE_LEGACY.md"
  cat > "$FIXTURE/MANIFEST" <<'EOF'
# fixture MANIFEST
agents
skills
templates
EOF
  git -C "$FIXTURE" init -q
  git -C "$FIXTURE" config user.email "test@example.com"
  git -C "$FIXTURE" config user.name "Test"
  git -C "$FIXTURE" add -A
  git -C "$FIXTURE" commit -q -m "fixture harness v1"
}
build_fixture

# Append a line to a fixture source and commit — simulates an upstream change.
bump_fixture_file() {
  printf '%s\n' "$2" >> "$FIXTURE/$1"
  git -C "$FIXTURE" add -A
  git -C "$FIXTURE" commit -q -m "fixture: bump $1"
}

# Greenfield install (mode default, non-interactive).
run_setup_greenfield() {
  _target="$1"
  ( cd "$_target" && SUPERVISOR_REPO="file://$FIXTURE" bash "$SETUP" </dev/null \
      >"$WORK/setup.log" 2>&1 )
}

# Brownfield install driven through a real pty: Enter (1) Install), "2"
# (brownfield), Enter (skip packs), Enter (accept the plan). /dev/tty prompts
# are unreachable from a pipe.
run_setup_brownfield() {
  _target="$1"
  ( cd "$_target" && printf '\n2\n\n\n' | SHELL=/bin/sh script -qec \
      "SUPERVISOR_REPO=file://$FIXTURE bash $SETUP" "$WORK/brownfield.typescript" \
      >"$WORK/setup.log" 2>&1 )
}

# Run update.sh. $2 = /dev/null: no terminal. $2 = a canned answer file: typed
# into a real terminal after accepting the menu (Enter = Update) and the plan
# (Enter = Proceed) — prompts read /dev/tty since T114, never stdin.
run_update() {
  _target="$1"
  _stdin="$2"
  if [ "$_stdin" = /dev/null ]; then
    ( cd "$_target" && SUPERVISOR_REPO="file://$FIXTURE" bash "$UPDATE" <"$_stdin" \
        >"$WORK/update.log" 2>&1 )
  else
    ( cd "$_target" && SUPERVISOR_REPO="file://$FIXTURE" \
        run_in_pty "\n\n$(cat "$_stdin")\n" "bash '$UPDATE'" >"$WORK/update.log" 2>&1 )
  fi
}

# make_mutant <name> <sed-expr> -> prints the path of a kit copy whose
# lib/harness-update.sh has the sed applied; run its update.sh.
make_mutant() {
  _md="$WORK/$1"
  mkdir -p "$_md/lib"
  cp "$SETUP" "$UPDATE" "$_md/"
  cp "$REPO_ROOT/lib/"* "$_md/lib/"
  sed "$2" "$UPDATE_LIB" > "$_md/lib/harness-update.sh"
  printf '%s' "$_md"
}

printf 's\n' > "$WORK/skip.in"
printf 'o\n' > "$WORK/overwrite.in"

# =============================================================================
# SC1 — greenfield, unedited: CLAUDE.md becomes byte-identical to fresh
# upstream CLAUDE.md, no prompt, lock hash + source refreshed.
# =============================================================================
T1="$WORK/t1-greenfield"
mkdir -p "$T1"
git -C "$T1" init -q
if run_setup_greenfield "$T1"; then
  [ "$(lock_field "$T1/.claude/harness-lock.json" claude_md_source)" = "CLAUDE.md" ] \
    && pass "SC1: setup recorded claude_md_source=CLAUDE.md" \
    || fail "SC1: setup did not record claude_md_source=CLAUDE.md"

  bump_fixture_file CLAUDE.md "MARKER-SC1-GREEN"

  if run_update "$T1" /dev/null; then
    pass "SC1: update.sh exited 0"
  else
    fail "SC1: update.sh exited $? (see $WORK/update.log)"; cat "$WORK/update.log" >&2
  fi
  if grep -q "MARKER-SC1-GREEN" "$T1/CLAUDE.md" 2>/dev/null; then
    pass "SC1: CLAUDE.md carries the fresh upstream marker"
  else
    fail "SC1: CLAUDE.md missing the fresh upstream marker"
  fi
  if cmp -s "$T1/CLAUDE.md" "$FIXTURE/CLAUDE.md"; then
    pass "SC1: CLAUDE.md is byte-identical to upstream CLAUDE.md"
  else
    fail "SC1: CLAUDE.md differs from upstream CLAUDE.md"
  fi
  if grep -q "conflict: 'CLAUDE.md'" "$WORK/update.log"; then
    fail "SC1: unexpected conflict prompt for an untouched file"
  else
    pass "SC1: no conflict prompt fired"
  fi
  _new_hash=$(lock_field "$T1/.claude/harness-lock.json" CLAUDE.md)
  _fresh_hash=$(sha256sum "$FIXTURE/CLAUDE.md" | awk '{print $1}')
  [ "$_new_hash" = "$_fresh_hash" ] \
    && pass "SC1: lock hash for CLAUDE.md refreshed to upstream" \
    || fail "SC1: lock hash for CLAUDE.md not refreshed (got '$_new_hash')"
else
  fail "SC1: setup failed for greenfield fixture — see $WORK/setup.log"; cat "$WORK/setup.log" >&2
fi

# =============================================================================
# SC2 — brownfield (pty), unedited: CLAUDE.md becomes the fresh upstream
# CLAUDE_LEGACY.md, never the greenfield content.
# =============================================================================
T2="$WORK/t2-brownfield"
mkdir -p "$T2"
git -C "$T2" init -q
if run_setup_brownfield "$T2"; then
  [ "$(lock_field "$T2/.claude/harness-lock.json" claude_md_source)" = "CLAUDE_LEGACY.md" ] \
    && pass "SC2: setup recorded claude_md_source=CLAUDE_LEGACY.md" \
    || fail "SC2: setup did not record claude_md_source=CLAUDE_LEGACY.md"

  bump_fixture_file CLAUDE_LEGACY.md "MARKER-SC2-LEGACY"

  if run_update "$T2" /dev/null; then
    pass "SC2: update.sh exited 0"
  else
    fail "SC2: update.sh exited $? (see $WORK/update.log)"; cat "$WORK/update.log" >&2
  fi
  if grep -q "MARKER-SC2-LEGACY" "$T2/CLAUDE.md" 2>/dev/null; then
    pass "SC2: CLAUDE.md carries the fresh upstream CLAUDE_LEGACY marker"
  else
    fail "SC2: CLAUDE.md missing the fresh upstream CLAUDE_LEGACY marker"
  fi
  if grep -q "GREENFIELD SUPERVISOR RULES" "$T2/CLAUDE.md" 2>/dev/null; then
    fail "SC2: CLAUDE.md picked up greenfield content instead of legacy"
  else
    pass "SC2: greenfield content never appeared in the brownfield project"
  fi
else
  fail "SC2: setup failed for brownfield fixture — see $WORK/setup.log"; cat "$WORK/setup.log" >&2
fi

# =============================================================================
# SC3 — user-edited CLAUDE.md + upstream change: conflict prompt fires; no
# input leaves the edit intact and exits 2.
# =============================================================================
T3="$WORK/t3-edited"
mkdir -p "$T3"
git -C "$T3" init -q
if run_setup_greenfield "$T3"; then
  printf '\nUSER CUSTOM LINE\n' >> "$T3/CLAUDE.md"
  bump_fixture_file CLAUDE.md "MARKER-SC3-GREEN"

  run_update "$T3" /dev/null
  _rc=$?
  [ "$_rc" -eq 2 ] && pass "SC3: update.sh exits 2 on an unresolved CLAUDE.md conflict" \
    || fail "SC3: expected exit 2, got $_rc"
  if grep -q "USER CUSTOM LINE" "$T3/CLAUDE.md" 2>/dev/null; then
    pass "SC3: user's edited line is still present"
  else
    fail "SC3: user's edited line was lost"
  fi
  if grep -q "MARKER-SC3-GREEN" "$T3/CLAUDE.md" 2>/dev/null; then
    fail "SC3: upstream change silently applied over the user's edit"
  else
    pass "SC3: upstream change was NOT silently applied"
  fi
  if grep -q "conflict" "$WORK/update.log" && grep -q "CLAUDE.md" "$WORK/update.log"; then
    pass "SC3: stderr names 'conflict' and 'CLAUDE.md'"
  else
    fail "SC3: stderr did not name the conflict"; cat "$WORK/update.log" >&2
  fi
else
  fail "SC3: setup failed — see $WORK/setup.log"; cat "$WORK/setup.log" >&2
fi

# =============================================================================
# SC4 — install; update; update: recorded claude_md_source identical after
# each run (survives write_new_lock rebuilding the lock twice).
# =============================================================================
T4="$WORK/t4-idempotent"
mkdir -p "$T4"
git -C "$T4" init -q
if run_setup_greenfield "$T4"; then
  _src0=$(lock_field "$T4/.claude/harness-lock.json" claude_md_source)
  run_update "$T4" /dev/null
  _src1=$(lock_field "$T4/.claude/harness-lock.json" claude_md_source)
  run_update "$T4" /dev/null
  _src2=$(lock_field "$T4/.claude/harness-lock.json" claude_md_source)
  if [ "$_src0" = "CLAUDE.md" ] && [ "$_src1" = "CLAUDE.md" ] && [ "$_src2" = "CLAUDE.md" ]; then
    pass "SC4: claude_md_source stable across install + 2 updates"
  else
    fail "SC4: claude_md_source drifted ('$_src0' -> '$_src1' -> '$_src2')"
  fi
  # Second update with nothing changed must be a true no-op (idempotent).
  git -C "$T4" diff --quiet -- CLAUDE.md \
    2>/dev/null && true # CLAUDE.md is untracked project content, not asserted here
else
  fail "SC4: setup failed — see $WORK/setup.log"; cat "$WORK/setup.log" >&2
fi

# =============================================================================
# SC5 — lock predates the source field (stripped, simulating a pre-T110 lock):
# heading inference still identifies the greenfield source and updates it.
# =============================================================================
T5="$WORK/t5-old-lock"
mkdir -p "$T5"
git -C "$T5" init -q
if run_setup_greenfield "$T5"; then
  # Strip the claude_md_source line to simulate a lock written before T110.
  sed -i.orig '/"claude_md_source"/d' "$T5/.claude/harness-lock.json"
  rm -f "$T5/.claude/harness-lock.json.orig"
  [ -z "$(lock_field "$T5/.claude/harness-lock.json" claude_md_source)" ] \
    || fail "SC5: precondition broken — claude_md_source still present after stripping"

  bump_fixture_file CLAUDE.md "MARKER-SC5-GREEN"

  if run_update "$T5" /dev/null; then
    pass "SC5: update.sh exited 0 against an old (fieldless) lock"
  else
    fail "SC5: update.sh exited $? (see $WORK/update.log)"; cat "$WORK/update.log" >&2
  fi
  if grep -q "MARKER-SC5-GREEN" "$T5/CLAUDE.md" 2>/dev/null; then
    pass "SC5: CLAUDE.md updated via heading inference"
  else
    fail "SC5: CLAUDE.md was not updated — inference did not identify the source"
  fi
  [ "$(lock_field "$T5/.claude/harness-lock.json" claude_md_source)" = "CLAUDE.md" ] \
    && pass "SC5: the rewritten lock now records the inferred source" \
    || fail "SC5: the rewritten lock still lacks claude_md_source"
else
  fail "SC5: setup failed — see $WORK/setup.log"; cat "$WORK/setup.log" >&2
fi

# =============================================================================
# SC6 — old lock (fieldless) + CLAUDE.md's first line hand-edited to an
# unknown heading: neither candidate matches -> conflict path, exit 2, file
# left unchanged (never silently overwritten).
# =============================================================================
T6="$WORK/t6-unknown-heading"
mkdir -p "$T6"
git -C "$T6" init -q
if run_setup_greenfield "$T6"; then
  sed -i.orig '/"claude_md_source"/d' "$T6/.claude/harness-lock.json"
  rm -f "$T6/.claude/harness-lock.json.orig"
  # Rewrite the first line to something neither upstream CLAUDE.md nor
  # CLAUDE_LEGACY.md starts with.
  { printf '# TOTALLY UNRECOGNIZED HEADING\n'; tail -n +2 "$T6/CLAUDE.md"; } \
    > "$T6/CLAUDE.md.new" && mv "$T6/CLAUDE.md.new" "$T6/CLAUDE.md"
  _before_hash=$(sha256sum "$T6/CLAUDE.md" | awk '{print $1}')

  bump_fixture_file CLAUDE.md "MARKER-SC6-GREEN"

  run_update "$T6" /dev/null
  _rc=$?
  [ "$_rc" -eq 2 ] && pass "SC6: update.sh exits 2 on an unrecognized heading" \
    || fail "SC6: expected exit 2, got $_rc"
  _after_hash=$(sha256sum "$T6/CLAUDE.md" | awk '{print $1}')
  [ "$_before_hash" = "$_after_hash" ] \
    && pass "SC6: CLAUDE.md left byte-unchanged (never silently overwritten)" \
    || fail "SC6: CLAUDE.md content changed despite unresolved conflict"
  if grep -q "conflict" "$WORK/update.log" && grep -q "CLAUDE.md" "$WORK/update.log"; then
    pass "SC6: stderr names the conflict against CLAUDE.md"
  else
    fail "SC6: stderr did not describe the conflict"; cat "$WORK/update.log" >&2
  fi
else
  fail "SC6: setup failed — see $WORK/setup.log"; cat "$WORK/setup.log" >&2
fi

# =============================================================================
# SC7 — brownfield, user edited CLAUDE.md's first line, upstream
# CLAUDE_LEGACY.md changed: the RECORDED source must still be honoured (not
# heading inference, which would see an unrecognized first line and treat it
# as a conflict against greenfield CLAUDE.md instead). Answering "o" through
# the standard hash-conflict prompt must land the fresh CLAUDE_LEGACY.md
# content, never the greenfield CLAUDE.md's own first line.
# =============================================================================
T7SRC="$WORK/t7-source-honoured"
mkdir -p "$T7SRC"
git -C "$T7SRC" init -q
if run_setup_brownfield "$T7SRC"; then
  [ "$(lock_field "$T7SRC/.claude/harness-lock.json" claude_md_source)" = "CLAUDE_LEGACY.md" ] \
    || fail "SC7: precondition broken — install did not record CLAUDE_LEGACY.md"

  # Edit CLAUDE.md's first line — this changes its hash (triggers the normal
  # conflict prompt) without changing its recorded install source.
  { printf '# USER EDITED FIRST LINE\n'; tail -n +2 "$T7SRC/CLAUDE.md"; } \
    > "$T7SRC/CLAUDE.md.new" && mv "$T7SRC/CLAUDE.md.new" "$T7SRC/CLAUDE.md"

  bump_fixture_file CLAUDE_LEGACY.md "MARKER-SC7-LEGACY"

  if run_update "$T7SRC" "$WORK/overwrite.in"; then
    pass "SC7: update.sh exited 0 answering [o] to the conflict"
  else
    fail "SC7: update.sh exited $? (see $WORK/update.log)"; cat "$WORK/update.log" >&2
  fi
  if grep -q "MARKER-SC7-LEGACY" "$T7SRC/CLAUDE.md" 2>/dev/null; then
    pass "SC7: CLAUDE.md carries the fresh CLAUDE_LEGACY.md marker"
  else
    fail "SC7: CLAUDE.md missing the fresh CLAUDE_LEGACY.md marker"
  fi
  if grep -q "GREENFIELD SUPERVISOR RULES" "$T7SRC/CLAUDE.md" 2>/dev/null; then
    fail "SC7: CLAUDE.md picked up greenfield content — recorded source was not honoured"
  else
    pass "SC7: greenfield content never appeared"
  fi
  [ "$(lock_field "$T7SRC/.claude/harness-lock.json" claude_md_source)" = "CLAUDE_LEGACY.md" ] \
    && pass "SC7: lock still records CLAUDE_LEGACY.md" \
    || fail "SC7: lock's claude_md_source drifted away from CLAUDE_LEGACY.md"
else
  fail "SC7: setup failed for brownfield fixture — see $WORK/setup.log"; cat "$WORK/setup.log" >&2
fi

# =============================================================================
# SC8 — lock's claude_md_source set to a value outside the allowlist
# {CLAUDE.md, CLAUDE_LEGACY.md}, pointing (via relative traversal out of
# HARNESS_TEMP_DIR) at a real file holding a unique marker. That marker must
# never land in CLAUDE.md; update must still exit per the existing rules
# (unedited CLAUDE.md -> fast overwrite via heading-inferred CLAUDE.md); and
# the rewritten lock must record an allowlisted value (or omit the field).
# =============================================================================
T8="$WORK/t8-untrusted-source"
mkdir -p "$T8"
git -C "$T8" init -q
if run_setup_greenfield "$T8"; then
  EVILFILE="$WORK/sc8-evil.md"
  printf 'MARKER-SC8-EVIL-CONTENT\n' > "$EVILFILE"
  # $WORK and update.sh's own $HARNESS_TEMP_DIR are both direct children of
  # the same $TMPDIR (mktemp "${TMPDIR:-/tmp}/<prefix>.XXXXXX"), so one level
  # up plus $WORK's own basename reaches $EVILFILE regardless of the random
  # suffix on either directory.
  REL_EVIL="../$(basename "$WORK")/sc8-evil.md"
  python3 - "$T8/.claude/harness-lock.json" "$REL_EVIL" <<'PYEOF'
import sys
path, rel = sys.argv[1], sys.argv[2]
data = open(path).read()
old = '"claude_md_source": "CLAUDE.md"'
new = f'"claude_md_source": "{rel}"'
assert old in data, "SC8 fixture assumption broken: claude_md_source line not found"
open(path, "w").write(data.replace(old, new, 1))
PYEOF

  if run_update "$T8" /dev/null; then
    pass "SC8: update.sh exited 0"
  else
    fail "SC8: update.sh exited $? (see $WORK/update.log)"; cat "$WORK/update.log" >&2
  fi
  if grep -q "MARKER-SC8-EVIL-CONTENT" "$T8/CLAUDE.md" 2>/dev/null; then
    fail "SC8: the untrusted lock value's file content landed in CLAUDE.md"
  else
    pass "SC8: the untrusted lock value's file content never landed in CLAUDE.md"
  fi
  if grep -q "not an allowed value" "$WORK/update.log"; then
    pass "SC8: stderr warns about the rejected claude_md_source value"
  else
    fail "SC8: stderr did not warn about the rejected value"; cat "$WORK/update.log" >&2
  fi
  _sc8_src=$(lock_field "$T8/.claude/harness-lock.json" claude_md_source)
  case "$_sc8_src" in
    CLAUDE.md|CLAUDE_LEGACY.md|"")
      pass "SC8: rewritten lock records an allowlisted source ('$_sc8_src')" ;;
    *)
      fail "SC8: rewritten lock still carries an untrusted source ('$_sc8_src')" ;;
  esac
else
  fail "SC8: setup failed — see $WORK/setup.log"; cat "$WORK/setup.log" >&2
fi

# =============================================================================
# M1 — mutation control: patch the update logic so resolve_claude_md_source always
# resolves "CLAUDE.md" regardless of the recorded/inferred source. SC2 (the
# brownfield-propagation assertion) must then fail, proving SC2 actually
# exercises the source-selection logic rather than passing vacuously.
# =============================================================================
M1_DIR=$(make_mutant mutant1 's/CLAUDE_MD_SOURCE="\$_recorded"/CLAUDE_MD_SOURCE="CLAUDE.md"/')
MUTANT="$M1_DIR/update.sh"
if cmp -s "$UPDATE_LIB" "$M1_DIR/lib/harness-update.sh"; then
  fail "M1: mutation did not change the update logic — sed pattern did not match"
else
  pass "M1: mutation landed (mutant differs from lib/harness-update.sh)"
fi

T7="$WORK/t7-mutation"
mkdir -p "$T7"
git -C "$T7" init -q
if run_setup_brownfield "$T7"; then
  bump_fixture_file CLAUDE_LEGACY.md "MARKER-M1-LEGACY"
  ( cd "$T7" && SUPERVISOR_REPO="file://$FIXTURE" bash "$MUTANT" </dev/null \
      >"$WORK/mutant-update.log" 2>&1 )
  if grep -q "GREENFIELD SUPERVISOR RULES" "$T7/CLAUDE.md" 2>/dev/null; then
    pass "M1: mutant wrongly overwrote the brownfield project with greenfield content (SC2 would fail)"
  else
    fail "M1: mutant did not reproduce the expected SC2 failure — mutation may be inert"
  fi
else
  fail "M1: setup failed for mutation-control fixture — see $WORK/setup.log"; cat "$WORK/setup.log" >&2
fi

# =============================================================================
# M2 — mutation control: disable the recorded-source branch entirely (force
# heading inference always, even when a valid recorded source exists). SC7
# must then fail: an edited CLAUDE.md first line no longer matches any
# upstream heading, so the diff/overwrite falls back to greenfield CLAUDE.md
# instead of the recorded CLAUDE_LEGACY.md.
# =============================================================================
M2_DIR=$(make_mutant mutant2 's/if \[ -n "\$_recorded" \]; then/if false; then/')
MUTANT2="$M2_DIR/update.sh"
if cmp -s "$UPDATE_LIB" "$M2_DIR/lib/harness-update.sh"; then
  fail "M2: mutation did not change the update logic — sed pattern did not match"
else
  pass "M2: mutation landed (mutant differs from lib/harness-update.sh)"
fi

T9="$WORK/t9-m2-mutation"
mkdir -p "$T9"
git -C "$T9" init -q
if run_setup_brownfield "$T9"; then
  { printf '# USER EDITED FIRST LINE\n'; tail -n +2 "$T9/CLAUDE.md"; } \
    > "$T9/CLAUDE.md.new" && mv "$T9/CLAUDE.md.new" "$T9/CLAUDE.md"
  bump_fixture_file CLAUDE_LEGACY.md "MARKER-M2-LEGACY"
  ( cd "$T9" && SUPERVISOR_REPO="file://$FIXTURE" \
      run_in_pty "\n\n$(cat "$WORK/overwrite.in")\n" "bash '$MUTANT2'" \
      >"$WORK/mutant2-update.log" 2>&1 )
  if grep -q "GREENFIELD SUPERVISOR RULES" "$T9/CLAUDE.md" 2>/dev/null \
     && ! grep -q "MARKER-M2-LEGACY" "$T9/CLAUDE.md" 2>/dev/null; then
    pass "M2: mutant wrongly diffed/overwrote against greenfield CLAUDE.md (SC7 would fail)"
  else
    fail "M2: mutant did not reproduce the expected SC7 failure — mutation may be inert"
  fi
else
  fail "M2: setup failed for mutation-control fixture — see $WORK/setup.log"; cat "$WORK/setup.log" >&2
fi

# =============================================================================
# M3 — mutation control: remove the allowlist check (accept any recorded
# claude_md_source value, as round 1 did). SC8 must then fail: the untrusted
# lock value's file content lands directly in CLAUDE.md.
# =============================================================================
M3_DIR=$(make_mutant mutant3 's/CLAUDE\.md|CLAUDE_LEGACY\.md)/*)/')
MUTANT3="$M3_DIR/update.sh"
if cmp -s "$UPDATE_LIB" "$M3_DIR/lib/harness-update.sh"; then
  fail "M3: mutation did not change the update logic — sed pattern did not match"
else
  pass "M3: mutation landed (mutant differs from lib/harness-update.sh)"
fi

T10="$WORK/t10-m3-mutation"
mkdir -p "$T10"
git -C "$T10" init -q
if run_setup_greenfield "$T10"; then
  EVILFILE3="$WORK/m3-evil.md"
  printf 'MARKER-M3-EVIL-CONTENT\n' > "$EVILFILE3"
  REL_EVIL3="../$(basename "$WORK")/m3-evil.md"
  python3 - "$T10/.claude/harness-lock.json" "$REL_EVIL3" <<'PYEOF'
import sys
path, rel = sys.argv[1], sys.argv[2]
data = open(path).read()
old = '"claude_md_source": "CLAUDE.md"'
new = f'"claude_md_source": "{rel}"'
assert old in data, "M3 fixture assumption broken: claude_md_source line not found"
open(path, "w").write(data.replace(old, new, 1))
PYEOF
  ( cd "$T10" && SUPERVISOR_REPO="file://$FIXTURE" bash "$MUTANT3" </dev/null \
      >"$WORK/mutant3-update.log" 2>&1 )
  if grep -q "MARKER-M3-EVIL-CONTENT" "$T10/CLAUDE.md" 2>/dev/null; then
    pass "M3: mutant wrongly copied the untrusted source's content into CLAUDE.md (SC8 would fail)"
  else
    fail "M3: mutant did not reproduce the expected SC8 failure — mutation may be inert"
  fi
else
  fail "M3: setup failed for mutation-control fixture — see $WORK/setup.log"; cat "$WORK/setup.log" >&2
fi

printf '\n----- summary: %s passed, %s failed -----\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
