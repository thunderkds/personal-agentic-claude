#!/bin/sh
# tests/test_cli_and_project_menus.sh — choose CLIs and project type from a list (T115).
#
# setup.sh takes no options. On Install / Reinstall the user picks the CLIs
# (1) Claude Code  2) Codex) and the project type (1) New  2) Existing / legacy)
# from numbered menus; Update shows neither and keeps what is present. Covers
# SC1–SC8 of tasks/TASK_GUIDE_T115.md plus AC2 input forms, the Reinstall
# deselect rule, and the "both links deleted" restore path.
#
# PATH: tests/lib/pty.sh hides any real claude/codex; each case that needs a
# CLI "installed" puts a fake executable on PATH (with_clis).
#
# EASYKIT_TRANSCRIPTS=<dir> copies the SC1 transcript there (HITL review).
#
# Run: bash tests/test_cli_and_project_menus.sh
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
skip() { printf 'SKIP: %s\n' "$1"; }

WORK=$(mktemp -d "${TMPDIR:-/tmp}/cli-menus-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT INT TERM HUP

# ── Fixture kit: this checkout's working tree, committed ─────────────────────
FIXTURE="$WORK/kit"
mkdir -p "$FIXTURE"
( cd "$REPO_ROOT" && git ls-files -co --exclude-standard -z | tar --null -T - -cf - ) \
  | tar -xf - -C "$FIXTURE"
git -C "$FIXTURE" init -q
git -C "$FIXTURE" config user.email "test@example.com"
git -C "$FIXTURE" config user.name "Test"
git -C "$FIXTURE" add -A
git -C "$FIXTURE" commit -q -m "kit under test"
SETUP="$FIXTURE/setup.sh"
UPDATE="$FIXTURE/update.sh"
BASE_PATH=$PATH

HAVE_SETSID=0
command -v setsid >/dev/null 2>&1 && HAVE_SETSID=1

# with_clis <names...> -> PATH with a fake executable for each name (none = no CLI)
with_clis() {
  _wc="$WORK/bin-$(printf '%s' "$*" | tr ' ' '-')"
  mkdir -p "$_wc"
  for _n in "$@"; do
    printf '#!/bin/sh\nexit 0\n' > "$_wc/$_n"
    chmod +x "$_wc/$_n"
  done
  PATH="$_wc:$BASE_PATH"
  export PATH
}

new_repo() {
  _r="$WORK/$1"
  mkdir -p "$_r"
  git -C "$_r" init -q
  git -C "$_r" config user.email "test@example.com"
  git -C "$_r" config user.name "Test"
  git -C "$_r" commit -q --allow-empty -m init
  printf '%s' "$_r"
}

# pty_setup <repo> <answers> [command] -> exit code; transcript in <repo>.log
# Answers on Install / Reinstall: action, CLIs, project type, packs, Proceed.
pty_setup() {
  # shellcheck disable=SC2016  # $SETUP does expand: the quotes are inside "..."
  ( cd "$1" && SUPERVISOR_REPO="file://$FIXTURE" \
      run_in_pty "$2" "${3:-sh '$SETUP'}" >"$1.log" 2>&1 )
}

notty_setup() {
  ( cd "$1" && SUPERVISOR_REPO="file://$FIXTURE" \
      setsid -w sh "$SETUP" </dev/null >"$1.log" 2>&1 )
}

commit_all() { git -C "$1" add -A >/dev/null 2>&1; git -C "$1" commit -q -m "$2" >/dev/null 2>&1; }
clean() { [ -z "$(git -C "$1" status --porcelain)" ]; }
line_of() { _l=$(grep -nF -- "$2" "$1" | head -n1 | cut -d: -f1); printf '%s' "${_l:-0}"; }
has_claude_links() { [ -L "$1/.claude/skills" ] && [ -L "$1/.claude/agents" ]; }
no_claude_links() { [ ! -e "$1/.claude/skills" ] && [ ! -L "$1/.claude/skills" ] \
                    && [ ! -e "$1/.claude/agents" ] && [ ! -L "$1/.claude/agents" ]; }
has_codex() { [ -d "$1/.codex/skills" ]; }

keep_transcript() {
  [ -n "${EASYKIT_TRANSCRIPTS:-}" ] || return 0
  mkdir -p "$EASYKIT_TRANSCRIPTS" && cp "$1" "$EASYKIT_TRANSCRIPTS/$2"
}

# ── SC1 / AC1 — codex on PATH only: Codex pre-selected, Enter accepts ───────
with_clis codex
T=$(new_repo sc1)
pty_setup "$T" '\n\n\n\n\n'; RC=$?
keep_transcript "$T.log" SC1.txt
if [ "$RC" -eq 0 ] && has_codex "$T" && no_claude_links "$T" \
   && grep -q 'Which CLIs should Easy Kit set up?' "$T.log" \
   && grep -q '1) Claude Code  2) Codex' "$T.log" \
   && grep -q 'Choose one or more \[2\]' "$T.log"; then
  pass "SC1: codex on PATH -> Codex pre-selected; Enter installs Codex only"
else
  fail "SC1: PATH pre-selection (rc=$RC)"; cat "$T.log" >&2
fi

# ── AC1 — neither CLI on PATH: Claude Code pre-selected ─────────────────────
with_clis
T=$(new_repo ac1-none)
pty_setup "$T" '\n\n\n\n\n'; RC=$?
if [ "$RC" -eq 0 ] && has_claude_links "$T" && ! has_codex "$T" \
   && grep -q 'Choose one or more \[1\]' "$T.log"; then
  pass "AC1: no CLI on PATH -> Claude Code pre-selected"
else
  fail "AC1: fallback pre-selection (rc=$RC)"; cat "$T.log" >&2
fi

# ── AC1 — both on PATH: both pre-selected ───────────────────────────────────
with_clis claude codex
T=$(new_repo ac1-both)
pty_setup "$T" '\n\n\n\n\n'; RC=$?
if [ "$RC" -eq 0 ] && has_claude_links "$T" && has_codex "$T" \
   && grep -q 'Choose one or more \[1 2\]' "$T.log"; then
  pass "AC1: both on PATH -> both pre-selected"
else
  fail "AC1: both pre-selected (rc=$RC)"; cat "$T.log" >&2
fi

# ── SC2 / AC2 — '1,2', '1 2' and '2' select exactly those CLIs ──────────────
with_clis
for _case in '1,2:both' '1 2:both' '2:codex' '1:claude'; do
  _in=${_case%%:*}; _want=${_case#*:}
  T=$(new_repo "ac2-$(printf '%s' "$_in" | tr ' ,' '_c')")
  pty_setup "$T" "\\n$_in\\n\\n\\n\\n"; RC=$?
  case "$_want" in
    both)   has_claude_links "$T" && has_codex "$T"; OK=$? ;;
    codex)  no_claude_links "$T" && has_codex "$T"; OK=$? ;;
    claude) has_claude_links "$T" && ! has_codex "$T"; OK=$? ;;
  esac
  if [ "$RC" -eq 0 ] && [ "$OK" -eq 0 ]; then
    pass "SC2/AC2: input '$_in' selects $_want"
  else
    fail "SC2/AC2: input '$_in' (rc=$RC, wanted $_want)"; cat "$T.log" >&2
  fi
done

# ── AC2 — cleared selection re-prompts "pick at least one"; bad number too ──
T=$(new_repo ac2-empty)
pty_setup "$T" '\n,\n3\nabc\n2\n\n\n\n'; RC=$?
if [ "$RC" -eq 0 ] && has_codex "$T" && no_claude_links "$T" \
   && [ "$(grep -c 'Pick at least one CLI' "$T.log")" -eq 1 ] \
   && [ "$(grep -c 'Please enter 1, 2 or both' "$T.log")" -eq 2 ]; then
  pass "AC2: ',' -> pick at least one; '3' and 'abc' re-prompt; then '2' takes"
else
  fail "AC2: cleared/invalid CLI input (rc=$RC)"; cat "$T.log" >&2
fi

# EOF at the CLI menu cancels (same rule as T114's menus): nothing written.
T=$(new_repo ac2-eof)
pty_setup "$T" '\n\004'; RC=$?
if [ "$RC" -eq 0 ] && clean "$T" && grep -q 'nothing was changed' "$T.log"; then
  pass "AC2: EOF at the CLI menu cancels; nothing written"
else
  fail "AC2: EOF at the CLI menu (rc=$RC)"; git -C "$T" status --porcelain >&2; cat "$T.log" >&2
fi

# Stage 4: the answer word-splits, so it also globs. In a project holding
# files named 1 and 2, `*` expanded to them and was accepted as a selection
# instead of re-prompting. Only `*` is typed here; the re-prompt then gets a
# real answer, so a regression selects both CLIs while the fix installs Codex.
T=$(new_repo ac2-glob)
: >"$T/1"; : >"$T/2"
commit_all "$T" "files named 1 and 2"
pty_setup "$T" '\n*\n2\n\n\n\n'; RC=$?
if [ "$RC" -eq 0 ] && has_codex "$T" && no_claude_links "$T" \
   && grep -q 'Please enter 1, 2 or both' "$T.log"; then
  pass "AC2: '*' re-prompts; it never globs to the files named 1 and 2"
else
  fail "AC2: glob in CLI answer (rc=$RC)"; cat "$T.log" >&2
fi

# ── SC3 / AC3 / AC4 — project type 2 = CLAUDE_LEGACY.md; plan shows both ────
T=$(new_repo sc3)
pty_setup "$T" '\n1 2\n2\n\n\n'; RC=$?
ASK_AT=$(line_of "$T.log" 'Proceed? [Y/n]')
CLI_AT=$(line_of "$T.log" '  - CLIs: Claude Code, Codex')
TYPE_AT=$(line_of "$T.log" '  - Project type: Existing / legacy project (CLAUDE_LEGACY.md)')
if [ "$RC" -eq 0 ] \
   && [ "$(head -n1 "$T/CLAUDE.md")" = "$(head -n1 "$FIXTURE/CLAUDE_LEGACY.md")" ] \
   && grep -q '1) New project' "$T.log" && grep -q '2) Existing / legacy project' "$T.log" \
   && ! grep -qi 'greenfield\|brownfield' "$T.log" \
   && [ "$CLI_AT" -gt 0 ] && [ "$CLI_AT" -lt "$ASK_AT" ] \
   && [ "$TYPE_AT" -gt 0 ] && [ "$TYPE_AT" -lt "$ASK_AT" ]; then
  pass "SC3/AC3/AC4: '2' installs CLAUDE_LEGACY.md; plan names CLIs + project type before Proceed"
else
  fail "SC3/AC3/AC4: project type (rc=$RC cli=$CLI_AT type=$TYPE_AT ask=$ASK_AT)"; cat "$T.log" >&2
fi

# AC3 — default 1 = New project; an invalid answer re-prompts.
T=$(new_repo ac3-default)
pty_setup "$T" '\n\n9\n\n\n\n'; RC=$?
if [ "$RC" -eq 0 ] && cmp -s "$FIXTURE/CLAUDE.md" "$T/CLAUDE.md" \
   && grep -q 'Please enter 1 or 2' "$T.log" \
   && grep -q '  - Project type: New project (CLAUDE.md)' "$T.log"; then
  pass "AC3: Enter = New project (CLAUDE.md); '9' re-prompts"
else
  fail "AC3: project-type default (rc=$RC)"; cat "$T.log" >&2
fi

# ── SC4 / AC6 — any argument: exit 1, names it, nothing written ─────────────
for _args in '--harness codex' '--harness=codex' '--copy' '--pack=mobile' 'install'; do
  T=$(new_repo "sc4-$(printf '%s' "$_args" | tr -c '[:lower:]' '_')")
  # shellcheck disable=SC2086  # word-split the argument list on purpose
  ( cd "$T" && SUPERVISOR_REPO="file://$FIXTURE" sh "$SETUP" $_args </dev/null >"$T.log" 2>&1 ); RC=$?
  _first=${_args%% *}
  if [ "$RC" -eq 1 ] && clean "$T" && grep -qF -- "$_first" "$T.log" \
     && grep -q 'Easy Kit takes no options' "$T.log" \
     && grep -q 'choose from the menus' "$T.log"; then
    pass "SC4/AC6: 'setup.sh $_args' -> exit 1, names '$_first', nothing written"
  else
    fail "SC4/AC6: 'setup.sh $_args' (rc=$RC)"; git -C "$T" status --porcelain >&2; cat "$T.log" >&2
  fi
done

# update.sh forwards its arguments: an installed repo stays byte-identical.
T=$(new_repo sc4-update)
pty_setup "$T" '\n\n\n\n\n' >/dev/null 2>&1
commit_all "$T" "install easy kit"
( cd "$T" && SUPERVISOR_REPO="file://$FIXTURE" sh "$UPDATE" --harness claude </dev/null >"$T.log" 2>&1 ); RC=$?
if [ "$RC" -eq 1 ] && clean "$T" && grep -qF -- '--harness' "$T.log" \
   && grep -q 'Easy Kit takes no options' "$T.log"; then
  pass "SC4/AC6: 'update.sh --harness claude' -> exit 1, names the flag, nothing written"
else
  fail "SC4/AC6: update.sh --harness claude (rc=$RC)"; git -C "$T" status --porcelain >&2; cat "$T.log" >&2
fi

# ── SC5 / AC5 — Update shows no CLI / project menu; Codex-only stays so ─────
with_clis codex
T=$(new_repo sc5)
pty_setup "$T" '\n\n\n\n\n' >/dev/null 2>&1
commit_all "$T" "install codex only"
rm -rf "$T/.codex/skills/tdd"
with_clis claude codex   # claude on PATH must NOT pull Claude into an Update
pty_setup "$T" '\n\n'; RC=$?
if [ "$RC" -eq 0 ] && grep -q 'Update complete' "$T.log" \
   && ! grep -q 'Which CLIs' "$T.log" && ! grep -q 'New project' "$T.log" \
   && [ -f "$T/.codex/skills/tdd/SKILL.md" ] && no_claude_links "$T"; then
  pass "SC5/AC5: Update shows no menus 2-3; Codex re-projected; no Claude links"
else
  fail "SC5/AC5: Update on a Codex-only repo (rc=$RC)"; cat "$T.log" >&2
fi

# ── Reinstall — pre-selects what is present, not what is on PATH ────────────
pty_setup "$T" '2\n\n\n\n\n'; RC=$?
if [ "$RC" -eq 0 ] && grep -q 'Choose one or more \[2\]' "$T.log" \
   && has_codex "$T" && no_claude_links "$T"; then
  pass "Reinstall: Codex-only project pre-selects [2]; Enter keeps it Codex-only"
else
  fail "Reinstall: pre-selection from presence (rc=$RC)"; cat "$T.log" >&2
fi

# ── Reinstall deselect: a CLI already set up but not picked is KEPT, and said ─
with_clis claude codex
T=$(new_repo deselect)
pty_setup "$T" '\n\n\n\n\n' >/dev/null 2>&1
commit_all "$T" "install both"
rm -rf "$T/.codex/skills/tdd"
pty_setup "$T" '2\n1\n\n\n\n'; RC=$?
NOTE_AT=$(line_of "$T.log" 'Already set up here, not picked, kept and refreshed: Codex')
ASK_AT=$(line_of "$T.log" 'Proceed? [Y/n]')
if [ "$RC" -eq 0 ] && has_claude_links "$T" && [ -f "$T/.codex/skills/tdd/SKILL.md" ] \
   && [ "$NOTE_AT" -gt 0 ] && [ "$NOTE_AT" -lt "$ASK_AT" ]; then
  pass "Reinstall deselect: Codex not picked is kept and refreshed, stated on the plan"
else
  fail "Reinstall deselect (rc=$RC note=$NOTE_AT ask=$ASK_AT)"; cat "$T.log" >&2
fi

# ── D3 — both Claude links deleted: Update leaves them; Reinstall + 1 restores
if [ "$HAVE_SETSID" -eq 1 ]; then
  with_clis
  T=$(new_repo relink)
  pty_setup "$T" '\n\n\n\n\n' >/dev/null 2>&1
  commit_all "$T" "install claude"
  rm "$T/.claude/skills" "$T/.claude/agents"
  notty_setup "$T"; RC_U=$?
  UPDATE_LEFT=1; no_claude_links "$T" || UPDATE_LEFT=0
  pty_setup "$T" '2\n1\n\n\n\n'; RC=$?
  if [ "$RC_U" -eq 0 ] && [ "$UPDATE_LEFT" -eq 1 ] && [ "$RC" -eq 0 ] && has_claude_links "$T"; then
    pass "D3: both links deleted -> Update leaves them absent; Reinstall + Claude Code restores"
  else
    fail "D3: restore path (update rc=$RC_U left=$UPDATE_LEFT reinstall rc=$RC)"; cat "$T.log" >&2
  fi
else
  skip "D3: setsid not found — cannot run the no-terminal Update step"
fi

# ── SC6 / AC7 — no terminal: defaults printed and taken ─────────────────────
if [ "$HAVE_SETSID" -eq 1 ]; then
  with_clis
  T=$(new_repo sc6)
  notty_setup "$T"; RC=$?
  if [ "$RC" -eq 0 ] && has_claude_links "$T" \
     && grep -q 'No terminal — installing with the defaults: Claude Code, New project (CLAUDE.md)' "$T.log" \
     && ! grep -q 'Which CLIs' "$T.log"; then
    pass "SC6/AC7: no terminal -> prints 'Claude Code' + 'New project' defaults and installs"
  else
    fail "SC6/AC7: no-terminal defaults (rc=$RC)"; cat "$T.log" >&2
  fi
else
  skip "SC6: setsid not found — cannot remove the controlling terminal"
fi

# ── SC8 / AC8 — no user-facing installer string says "harness" ──────────────
# (the grep itself lives in tests/test_docs_match_installer.py; SC7 is pytest)
if python3 -m pytest -q "$REPO_ROOT/tests/test_docs_match_installer.py" >"$WORK/sc8.log" 2>&1; then
  pass "SC8/D9: installer strings and live docs are flag-free and say CLI, not harness"
else
  fail "SC8/D9: tests/test_docs_match_installer.py"; cat "$WORK/sc8.log" >&2
fi

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
