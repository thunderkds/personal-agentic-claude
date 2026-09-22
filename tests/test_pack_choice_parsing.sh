#!/bin/sh
# tests/test_pack_choice_parsing.sh — POSIX-sh tests for setup.sh pack-choice
# parsing (T108).
#
# A comma between pack numbers must not cost the user a pack: "1, 5, 3",
# "1,5,3" and "1 5 3" must all select the same three packs, and a genuinely
# invalid entry must still warn.
#
# setup.sh's prompt_packs early-returns unless stdin is a tty, so it cannot be
# driven from a test without a pty. The parsing lives in the pure function
# resolve_pack_choices (raw line in -> space-separated pack names on stdout,
# one log_warn per bad token on stderr). This test sources setup.sh with the
# define-only guard set (SETUP_SH_DEFINE_ONLY=1) so `main` does NOT run, and
# SETUP_SH_DIR pointed at the checkout so the piped-install bootstrap is not
# misfired, then asserts one case per Success Criteria row on that function.
#
# Run: bash tests/test_pack_choice_parsing.sh   (or: sh ...)
set -u

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)
# No terminal for the installer's /dev/tty prompts, even from a dev shell (T114).
# shellcheck source=tests/lib/pty.sh
. "$SCRIPT_DIR/lib/pty.sh"
detach_from_terminal "$0" "$@"
SETUP="$REPO_ROOT/setup.sh"

if [ ! -f "$SETUP" ]; then
  printf 'FATAL: setup.sh not found at %s\n' "$SETUP" >&2
  exit 2
fi

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1" >&2; }

WORK=$(mktemp -d "${TMPDIR:-/tmp}/pack-choice-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT INT TERM HUP

ERR="$WORK/stderr"

export SETUP SETUP_SH_DIR="$REPO_ROOT"

# Resolve a raw choice line via a define-only source of setup.sh, run from a
# scratch cwd so we can also prove `main` never scaffolds anything.
# stdout -> resolved pack list; stderr -> "$ERR".
resolve() {
  ( cd "$WORK" \
      && RAW="$1" SETUP_SH_DEFINE_ONLY=1 sh -c \
           'set --; . "$SETUP"; resolve_pack_choices "$RAW"' ) 2>"$ERR"
}

warn_count() {
  _c=$(grep -c 'Unknown pack choice' "$ERR" 2>/dev/null) || _c=0
  printf '%s' "$_c"
}

check() {
  _label="$1"; _input="$2"; _want_out="$3"; _want_warns="$4"; _want_name="$5"
  _got_out=$(resolve "$_input")
  _got_warns=$(warn_count)
  if [ "$_got_out" = "$_want_out" ] && [ "$_got_warns" -eq "$_want_warns" ]; then
    if [ -z "$_want_name" ] || grep -q "'$_want_name'" "$ERR"; then
      pass "$_label"
      return
    fi
  fi
  fail "$_label — got out='$_got_out' warns=$_got_warns (want out='$_want_out' warns=$_want_warns)"
  [ -s "$ERR" ] && sed 's/^/    stderr: /' "$ERR" >&2
}

# ── Success Criteria rows 1–6 ───────────────────────────────────────────────
check "row1: '1, 5, 3' -> mobile api devops, no warning" \
      "1, 5, 3" "mobile api devops" 0 ""
check "row2: '1,5,3' -> mobile api devops, no warning" \
      "1,5,3" "mobile api devops" 0 ""
check "row3: '1 5 3' -> mobile api devops, no warning (no regression)" \
      "1 5 3" "mobile api devops" 0 ""
check "row4: '' (empty) -> nothing, no warning" \
      "" "" 0 ""
check "row5: '1 9 3' -> mobile devops, exactly one warning naming 9" \
      "1 9 3" "mobile devops" 1 "9"
check "row6: '1,,3' -> mobile devops, no warning (separator is never a choice)" \
      "1,,3" "mobile devops" 0 ""

# ── Edge cases from the guide's checklist ───────────────────────────────────
check "edge: trailing comma '1,3,' -> mobile devops, no empty-string warning" \
      "1,3," "mobile devops" 0 ""
check "edge: surrounding whitespace '  1 , 3  ' is harmless" \
      "  1 , 3  " "mobile devops" 0 ""
check "edge: tab separators still work" \
      "$(printf '1\t3')" "mobile devops" 0 ""
check "edge: ',' alone -> nothing, no warning" \
      "," "" 0 ""
check "edge: duplicate choice '1 1' -> one token per input (install_pack is idempotent)" \
      "1 1" "mobile mobile" 0 ""

# ── Regression: empty selection must not abort setup.sh under `set -e` ──────
# prompt_packs runs `if [ -n "$resolved" ]; then PACKS=...; fi` — NOT
# `[ -n ... ] && PACKS=...`, whose non-zero status on an empty selection would
# be prompt_packs' exit code and, called bare inside main under `set -e`, would
# abort the installer before any work. Guard the composition, not just the
# function's stdout.
SE_RC=0
( cd "$WORK" && SETUP_SH_DEFINE_ONLY=1 sh -c '
    set -e
    . "$SETUP"
    demo_prompt_packs() {
      _resolved=$(resolve_pack_choices "")   # user pressed Enter to skip
      if [ -n "$_resolved" ]; then PACKS="$PACKS $_resolved"; fi
    }
    run() { demo_prompt_packs; }
    run
    echo REACHED' ) >"$WORK/se.out" 2>&1 || SE_RC=$?
if [ "$SE_RC" -eq 0 ] && grep -q REACHED "$WORK/se.out"; then
  pass "regression: empty pack selection does not abort under 'set -e'"
else
  fail "regression: empty pack selection aborted under 'set -e' (rc=$SE_RC)"
  sed 's/^/    /' "$WORK/se.out" >&2
fi

# ── Success Criteria row 7 — the define-only seam asserts on itself ─────────
# After a define-only source: resolve_pack_choices must be DEFINED, and `main`
# must NOT have run — nothing scaffolded into the scratch cwd.
SEAM_OUT=$( cd "$WORK" \
  && SETUP_SH_DEFINE_ONLY=1 sh -c \
       'set --; . "$SETUP" >/dev/null 2>&1
        command -v resolve_pack_choices >/dev/null 2>&1 && printf DEFINED' )
if [ "$SEAM_OUT" = "DEFINED" ]; then
  pass "row7a: resolve_pack_choices is defined after a define-only source"
else
  fail "row7a: resolve_pack_choices not defined after a define-only source"
fi
if [ ! -e "$WORK/.claude" ] && [ ! -e "$WORK/memory" ] && [ ! -e "$WORK/CLAUDE.md" ] \
   && [ ! -e "$WORK/templates" ]; then
  pass "row7b: define-only source did NOT run main (no install artifacts in cwd)"
else
  fail "row7b: define-only source ran main — install artifacts appeared in cwd"
fi

# Control: with the guard UNSET, the same source reaches main. Proven without a
# network fetch by pointing at a non-git cwd, where main's early
# check_target_is_git_repo aborts non-zero before any clone.
CTRL="$WORK/ctrl-not-git"
mkdir -p "$CTRL"
CTRL_RC=0
( cd "$CTRL" && sh -c 'set --; . "$SETUP"' >/dev/null 2>&1 ) || CTRL_RC=$?
if [ "$CTRL_RC" -ne 0 ]; then
  pass "row7c: without the guard, sourcing runs main (guard is the off switch)"
else
  fail "row7c: without the guard, sourcing did not run main — guard semantics unclear"
fi

printf '\n----- summary: %d passed, %d failed -----\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
