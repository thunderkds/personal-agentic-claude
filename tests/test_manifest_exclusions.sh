#!/bin/sh
# tests/test_manifest_exclusions.sh — MANIFEST `!` exclusions reach every reader (T122)
#
# T113 added `!<path>` exclusion lines to MANIFEST. scripts/validate.sh kept
# reading them as paths and failed CI on `!.claude/hooks/tests`. This suite pins:
#   SC1  the real repo validates (exit 0)
#   SC2  no MANIFEST line starting `!` is reported; every real entry is still [ok]
#   SC3  a genuinely missing entry still [FAIL]s and exits non-zero
#   SC4  an exclusion naming a path that does not exist is not an error
#   SC5  harness_manifest_dest maps nothing for a `!` line (lib/harness-update.sh
#        feeds it raw MANIFEST lines)
#
# validate.sh cd's to its own repo root, so each case runs a copy of THIS working
# tree (uncommitted edits included) with the MANIFEST under test.
#
# Run: bash tests/test_manifest_exclusions.sh   (or: sh tests/test_manifest_exclusions.sh)
set -u

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1" >&2; }

WORK=$(mktemp -d "${TMPDIR:-/tmp}/manifest-exclusions-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT INT TERM HUP

# One copy of the working tree; -P keeps .claude/{skills,agents} as symlinks.
COPY="$WORK/repo"
mkdir -p "$COPY"
cp -PR "$REPO_ROOT/." "$COPY/"
rm -rf "$COPY/.git"
cp "$REPO_ROOT/MANIFEST" "$WORK/MANIFEST.real"

# run_validate <manifest-file>: sets OUT (the MANIFEST section only) and RC.
run_validate() {
  cp "$1" "$COPY/MANIFEST"
  _all=$(sh "$COPY/scripts/validate.sh" 2>&1)
  RC=$?
  OUT=$(printf '%s\n' "$_all" | awk '/^== MANIFEST/ { on = 1; next } /^== / { on = 0 } on')
}

# Paths the real MANIFEST lists (field 1 of non-comment, non-exclusion lines).
REAL_PATHS=$(tr -d '\r' < "$WORK/MANIFEST.real" | awk '$0 !~ /^[[:space:]]*(#|$|!)/ { print $1 }')

# ── SC1 + SC2: the real MANIFEST ─────────────────────────────────────────────
run_validate "$WORK/MANIFEST.real"
if [ "$RC" -eq 0 ]; then
  pass "sc1: validate.sh exits 0 on this tree"
else
  fail "sc1: validate.sh exited $RC on this tree"
  printf '%s\n' "$OUT" >&2
fi

if grep -q '^!' "$WORK/MANIFEST.real"; then
  pass "sc2: precondition — the real MANIFEST carries a '!' exclusion"
else
  fail "sc2: precondition — the real MANIFEST has no '!' line, so sc2 tests nothing"
fi
if printf '%s\n' "$OUT" | grep -q '!'; then
  fail "sc2: a '!' exclusion was reported as an entry: $(printf '%s\n' "$OUT" | grep '!')"
else
  pass "sc2: no MANIFEST line starting '!' is reported as an entry"
fi
SC2_OK=1
for _p in $REAL_PATHS; do
  printf '%s\n' "$OUT" | grep -qxF "  [ok]   $_p" || { SC2_OK=0; fail "sc2: '$_p' not reported [ok]"; }
done
[ -n "$REAL_PATHS" ] && [ "$SC2_OK" -eq 1 ] && pass "sc2: every non-excluded entry still reported [ok] ($(printf '%s\n' "$REAL_PATHS" | wc -l | tr -d ' ') paths)"

# ── SC3: a missing entry still gates ─────────────────────────────────────────
{ cat "$WORK/MANIFEST.real"; printf 'no-such-path-xyz\n'; } > "$WORK/MANIFEST.missing"
run_validate "$WORK/MANIFEST.missing"
if [ "$RC" -ne 0 ] && printf '%s\n' "$OUT" | grep -qF '[FAIL] MANIFEST entry not found: no-such-path-xyz'; then
  pass "sc3: a missing MANIFEST entry [FAIL]s and exits non-zero (rc=$RC)"
else
  fail "sc3: missing entry not gated (rc=$RC)"
  printf '%s\n' "$OUT" >&2
fi

# ── SC4: an exclusion of a non-existent path is not an error ─────────────────
{ cat "$WORK/MANIFEST.real"; printf '!no-such-path-xyz\n'; } > "$WORK/MANIFEST.excl"
run_validate "$WORK/MANIFEST.excl"
if [ "$RC" -eq 0 ] && ! printf '%s\n' "$OUT" | grep -q 'no-such-path-xyz'; then
  pass "sc4: '!no-such-path-xyz' is skipped, exit 0"
else
  fail "sc4: '!no-such-path-xyz' was treated as an entry (rc=$RC)"
  printf '%s\n' "$OUT" >&2
fi

# ── SC5: harness_manifest_dest skips `!` lines ───────────────────────────────
# shellcheck source=../lib/harness-fetch.sh
. "$REPO_ROOT/lib/harness-fetch.sh"
_d=$(harness_manifest_dest 'skills          codex=.codex/skills' codex)
if [ "$_d" = ".codex/skills" ]; then
  pass "sc5: control — a path line still maps its codex destination"
else
  fail "sc5: control — expected '.codex/skills', got '$_d'"
fi
_d=$(harness_manifest_dest '!skills codex=.codex/skills' codex)
if [ -z "$_d" ]; then
  pass "sc5: a '!' line maps no destination"
else
  fail "sc5: a '!' line mapped destination '$_d'"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
printf '\n----- summary: %d passed, %d failed -----\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
