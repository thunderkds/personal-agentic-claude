#!/bin/sh
# tests/test_pack_catalog.sh — every pack ships as a dormant catalog (T116, ADR-0002).
#
# The kit's packs/ reaches every project through MANIFEST as plain files that no
# CLI loads; update keeps it current under the hash-lock rule; the installer no
# longer asks about, or claims to install, packs. Covers SC1–SC5 and AC7 of
# tasks/TASK_GUIDE_T116.md, plus mutation controls M1 (a `codex=` pair on the
# packs line → the SC2 check fails) and M2 (no packs line → the SC1 check fails),
# run against mutant kits so the checks are observed failing on every run.
#
# Run: bash tests/test_pack_catalog.sh
set -u

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)
# shellcheck source=tests/lib/pty.sh
. "$SCRIPT_DIR/lib/pty.sh"
detach_from_terminal "$0" "$@"

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1" >&2; }
# verdict <pass-msg> <fail-msg> <command...> -> pass or fail on the command's status
verdict() {
  _vp=$1; _vf=$2; shift 2
  if "$@"; then pass "$_vp"; else fail "$_vf"; fi
}

WORK=$(mktemp -d "${TMPDIR:-/tmp}/pack-catalog-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT INT TERM HUP

# ── Kits: this checkout's working tree, committed; mutants edit MANIFEST ─────
# make_kit <name> [sed-expression applied to MANIFEST]
make_kit() {
  _k="$WORK/$1"
  mkdir -p "$_k"
  ( cd "$REPO_ROOT" && git ls-files -co --exclude-standard -z | tar --null -T - -cf - ) \
    | tar -xf - -C "$_k"
  [ -n "${2:-}" ] && sed -i "$2" "$_k/MANIFEST"
  git -C "$_k" init -q
  git -C "$_k" config user.email "test@example.com"
  git -C "$_k" config user.name "Test"
  git -C "$_k" add -A
  git -C "$_k" commit -q -m "kit under test"
}
make_kit kit
make_kit kit-m1 's/^packs$/packs  codex=.codex\/packs/'
make_kit kit-m2 '/^packs$/d'
KIT="$WORK/kit"

new_repo() {
  _r="$WORK/$1"
  mkdir -p "$_r"
  git -C "$_r" init -q
  git -C "$_r" config user.email "test@example.com"
  git -C "$_r" config user.name "Test"
  git -C "$_r" commit -q --allow-empty -m init
  printf '%s' "$_r"
}

# install_both <repo> <kit> -> Install with Claude Code + Codex, New project, Proceed.
install_both() {
  ( cd "$1" && SUPERVISOR_REPO="file://$2" \
      run_in_pty '1\n1 2\n1\n\n' "sh '$2/setup.sh'" >"$1.log" 2>&1 )
}

# update_notty <repo> <kit> -> the no-terminal Update (setup.sh's update alias).
update_notty() {
  ( cd "$1" && SUPERVISOR_REPO="file://$2" sh "$2/update.sh" </dev/null >"$1.update.log" 2>&1 )
}

# ── Checks, each returning non-zero with a reason on stderr ──────────────────
# SC1: every kit pack is in the project, byte-identical, and hash-locked.
check_catalog_present() {
  _t="$1"
  for _p in "$KIT"/packs/*/; do
    _n=$(basename "$_p")
    [ -f "$_t/packs/$_n/PACK.md" ] || { echo "packs/$_n/PACK.md missing" >&2; return 1; }
  done
  diff -r "$KIT/packs" "$_t/packs" >/dev/null 2>&1 || { echo "packs/ differs from the kit" >&2; return 1; }
  ( cd "$KIT" && find packs -type f ) | while read -r _f; do
    _h=$(sha256sum "$_t/$_f" | awk '{print $1}')
    grep -q "\"$_f\": \"$_h\"" "$_t/.claude/harness-lock.json" \
      || { echo "lock has no matching hash for $_f" >&2; exit 1; }
  done
}

# SC2: no CLI directory holds anything pack-derived. Names are read from the kit
# at test time; -L follows .claude/{skills,agents} onto the canon they link to.
check_no_cli_loads_packs() {
  _t="$1"
  _names=$(for _a in "$KIT"/packs/*/agents/*.md; do basename "$_a"; done
           for _s in "$KIT"/packs/*/skills/*/; do basename "$_s"; done)
  [ -n "$_names" ] || { echo "read no pack names from the kit" >&2; return 1; }
  for _d in .claude .codex; do
    [ -e "$_t/$_d" ] || continue
    if [ -n "$(find -L "$_t/$_d" -name packs 2>/dev/null)" ]; then
      echo "$_d contains a packs path" >&2; return 1
    fi
    for _n in $_names; do
      if [ -n "$(find -L "$_t/$_d" -name "$_n" 2>/dev/null)" ]; then
        echo "$_d contains pack item $_n" >&2; return 1
      fi
    done
  done
}

# SC4: the installer neither asks about nor claims packs; it names the catalog.
check_install_output() {
  _log=$(tr -d '\r' < "$1")
  for _bad in "Pack '" "Packs requested" "Optional packs" "no packs installed"; do
    case "$_log" in *"$_bad"*) echo "output contains '$_bad'" >&2; return 1 ;; esac
  done
  case "$_log" in
    *"Pack catalog: every pack is in packs/, inactive. Your Supervisor recommends packs for this project."*) ;;
    *) echo "output lacks the catalog line" >&2; return 1 ;;
  esac
}

# ── SC1 / SC2 / SC4 — fresh install, Claude Code + Codex, via a pty ──────────
T=$(new_repo fresh)
install_both "$T" "$KIT"; RC=$?
if [ "$RC" -eq 0 ]; then pass "install exits 0"; else fail "install rc=$RC"; cat "$T.log" >&2; fi
if [ -d "$T/.codex/skills" ] && [ -L "$T/.claude/skills" ]; then
  pass "both CLIs were set up (the SC2 check has directories to search)"
else
  fail "Claude Code + Codex were not both set up"
fi
verdict "SC1: all packs present, byte-identical, hash-locked" "SC1" check_catalog_present "$T"
verdict "SC2: no CLI directory holds a pack item after install" "SC2 (install)" check_no_cli_loads_packs "$T"
verdict "SC4: no pack prompt or claim; catalog line present" "SC4 (terminal)" check_install_output "$T.log"

# SC4, no-terminal path: the old "no packs installed" line is gone too.
T_NT=$(new_repo notty)
( cd "$T_NT" && SUPERVISOR_REPO="file://$KIT" sh "$KIT/setup.sh" </dev/null >"$T_NT.log" 2>&1 )
verdict "SC4: no-terminal install output is the same" "SC4 (no terminal)" check_install_output "$T_NT.log"
verdict "SC1: no-terminal install ships the catalog too" "SC1 (no terminal)" check_catalog_present "$T_NT"

# ── SC3 — update keeps the catalog current through the hash-lock rule ────────
printf '\nupstream T116 edit\n' >> "$KIT/packs/api/PACK.md"
git -C "$KIT" commit -q -am "upstream: edit packs/api/PACK.md"
update_notty "$T" "$KIT"; RC=$?
if [ "$RC" -eq 0 ] && cmp -s "$KIT/packs/api/PACK.md" "$T/packs/api/PACK.md"; then
  pass "SC3: unedited catalog file refreshed silently on update"
else
  fail "SC3: unedited packs/api/PACK.md not refreshed (rc=$RC)"; cat "$T.update.log" >&2
fi
verdict "SC2: no CLI directory holds a pack item after update" "SC2 (update)" check_no_cli_loads_packs "$T"

# A project installed before the catalog existed (kit-m2 = MANIFEST without the
# packs line) receives it on its next Update — the path every existing user takes.
T_UP=$(new_repo pre-catalog)
( cd "$T_UP" && SUPERVISOR_REPO="file://$WORK/kit-m2" sh "$WORK/kit-m2/setup.sh" </dev/null >"$T_UP.log" 2>&1 )
if [ ! -e "$T_UP/packs" ]; then
  update_notty "$T_UP" "$KIT"; RC=$?
  if [ "$RC" -eq 0 ] && check_catalog_present "$T_UP"; then
    pass "SC3: a pre-catalog project receives the whole catalog, hash-locked, on update"
  else
    fail "SC3: update did not deliver the catalog to a pre-catalog project (rc=$RC)"; cat "$T_UP.update.log" >&2
  fi
else
  fail "SC3: the pre-catalog fixture already has packs/ — the upgrade case is not exercised"
fi

printf '\nmy local note\n' >> "$T/packs/api/PACK.md"
printf '\nsecond upstream edit\n' >> "$KIT/packs/api/PACK.md"
git -C "$KIT" commit -q -am "upstream: edit packs/api/PACK.md again"
update_notty "$T" "$KIT"; RC=$?
if [ "$RC" -ne 0 ] && grep -q 'my local note' "$T/packs/api/PACK.md" \
   && grep -qi 'conflict' "$T.update.log"; then
  pass "SC3: edited catalog file is a conflict, left untouched without input"
else
  fail "SC3: edited packs/api/PACK.md not treated as a conflict (rc=$RC)"; cat "$T.update.log" >&2
fi

# ── Edge: a project's own packs/ is backed up, not overwritten (T112) ────────
T_OWN=$(new_repo own-packs)
mkdir -p "$T_OWN/packs/mine"
printf 'my pack\n' > "$T_OWN/packs/mine/NOTES.md"
( cd "$T_OWN" && SUPERVISOR_REPO="file://$KIT" sh "$KIT/setup.sh" </dev/null >"$T_OWN.log" 2>&1 )
if grep -q 'my pack' "$T_OWN/packs.bak/mine/NOTES.md" 2>/dev/null && [ ! -e "$T_OWN/packs/mine" ]; then
  pass "edge: a pre-existing packs/ is moved to packs.bak before the catalog lands"
else
  fail "edge: a pre-existing packs/ was not backed up"
fi

# ── SC5 — the pack installer's names are gone from the installer ─────────────
_hits=$( cd "$REPO_ROOT" && command grep -nwE \
  'install_pack|install_abs|resolve_pack_choices|prompt_packs|SUPERVISOR_PATH|USE_COPY|PACKS' \
  setup.sh update.sh lib/*.sh )
verdict "SC5: no pack-installer name left in setup.sh/update.sh/lib" "SC5: still present: $_hits" \
  [ -z "$_hits" ]

# ── AC7 — the MANIFEST packs line carries no destination pair ────────────────
_line=$(command grep -E '^packs([[:space:]]|$)' "$REPO_ROOT/MANIFEST")
verdict "AC7: MANIFEST 'packs' line has no <harness>=<dest> pair" "AC7: MANIFEST packs line is '$_line'" \
  [ "$_line" = "packs" ]

# ── Mutation controls: the checks above must fail on a mutant kit ────────────
T_M1=$(new_repo m1)
install_both "$T_M1" "$WORK/kit-m1"
if ! check_no_cli_loads_packs "$T_M1"; then
  pass "M1: with 'codex=.codex/packs' on the packs line, the SC2 check fails"
else
  fail "M1: the SC2 check passed on a kit that projects packs into Codex"
fi

T_M2=$(new_repo m2)
install_both "$T_M2" "$WORK/kit-m2"
if ! check_catalog_present "$T_M2"; then
  pass "M2: with the packs line deleted, the SC1 check fails"
else
  fail "M2: the SC1 check passed on a kit with no packs line"
fi

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
