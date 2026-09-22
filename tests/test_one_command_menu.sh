#!/bin/sh
# tests/test_one_command_menu.sh — the one Easy Kit command (T114, ADR-0002).
#
# setup.sh detects an existing install, offers a numbered action menu with a
# safe default, shows a plan, and acts only after the user accepts. Every prompt
# reads /dev/tty, so each interactive case runs inside a real pty (`script -qec`,
# tests/lib/pty.sh); the no-terminal cases run under `setsid` (skipped, by name,
# where setsid is absent). Covers SC1–SC9 of tasks/TASK_GUIDE_T114.md plus the
# AC3 plan contents, AC5 invalid input and the MANIFEST-exclusion Reinstall case.
#
# Offline: the kit under test is a committed copy of this checkout's working
# tree, fetched via file:// — so uncommitted changes are what gets tested.
#
# EASYKIT_TRANSCRIPTS=<dir> copies the SC1/SC3/SC6 terminal transcripts there
# (for the HITL wording review).
#
# Run: bash tests/test_one_command_menu.sh
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

WORK=$(mktemp -d "${TMPDIR:-/tmp}/one-command-test.XXXXXX")
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

HAVE_SETSID=0
command -v setsid >/dev/null 2>&1 && HAVE_SETSID=1

# new_repo <name> -> fresh git repo with one commit
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
pty_setup() {
  # shellcheck disable=SC2016  # $SETUP does expand: the quotes are inside "..."
  ( cd "$1" && SUPERVISOR_REPO="file://$FIXTURE" \
      run_in_pty "$2" "${3:-sh '$SETUP'}" >"$1.log" 2>&1 )
}

# notty_setup <repo> -> exit code; output in <repo>.log (no controlling terminal)
notty_setup() {
  ( cd "$1" && SUPERVISOR_REPO="file://$FIXTURE" \
      setsid -w sh "$SETUP" </dev/null >"$1.log" 2>&1 )
}

# installed_repo <name> -> repo with Easy Kit installed and committed (clean)
installed_repo() {
  _ir=$(new_repo "$1")
  pty_setup "$_ir" '\n\n\n\n' >/dev/null 2>&1
  git -C "$_ir" add -A >/dev/null 2>&1
  git -C "$_ir" commit -q -m "install easy kit" >/dev/null 2>&1
  printf '%s' "$_ir"
}

# clean <repo> -> true when git sees no change at all
clean() { [ -z "$(git -C "$1" status --porcelain)" ]; }

# line_of <file> <fixed string> -> first line number containing it (0 if none)
line_of() { _l=$(grep -nF -- "$2" "$1" | head -n1 | cut -d: -f1); printf '%s' "${_l:-0}"; }

keep_transcript() {
  [ -n "${EASYKIT_TRANSCRIPTS:-}" ] || return 0
  mkdir -p "$EASYKIT_TRANSCRIPTS" && cp "$1" "$EASYKIT_TRANSCRIPTS/$2"
}

EDITED=skills/tdd/SKILL.md

# ── SC1 / AC1 — no lock: 1) Install 2) Cancel, Enter accepts ────────────────
T=$(new_repo sc1)
pty_setup "$T" '\n\n\n\n'; RC=$?
keep_transcript "$T.log" SC1.txt
if [ "$RC" -eq 0 ] && [ -f "$T/.claude/harness-lock.json" ] \
   && grep -q '1) Install' "$T.log" && grep -q '2) Cancel' "$T.log" \
   && grep -q 'Choose \[1\]' "$T.log" && grep -q 'Proceed? \[Y/n\]' "$T.log" \
   && grep -q 'Plan: Install Easy Kit' "$T.log"; then
  pass "SC1: Enter, Enter installs; menu showed Install/Cancel; plan confirmed"
else
  fail "SC1: default install via the menu (rc=$RC)"; cat "$T.log" >&2
fi

# ── SC2 / AC2 / AC4 — lock present: menu offers Update/Reinstall/Cancel ─────
T=$(installed_repo sc2)
pty_setup "$T" '3\n'; RC=$?
if [ "$RC" -eq 0 ] && clean "$T" \
   && grep -q '1) Update (keeps your edits)' "$T.log" \
   && grep -q '2) Reinstall (backs up your edits)' "$T.log" \
   && grep -q '3) Cancel' "$T.log" && grep -q 'nothing was changed' "$T.log"; then
  pass "SC2: 3) Cancel exits 0 with git status empty"
else
  fail "SC2: cancel from the menu (rc=$RC)"; git -C "$T" status --porcelain >&2; cat "$T.log" >&2
fi

# ── SC4 / AC3 / AC4 — plan 'n' returns to the menu; then Cancel ─────────────
# A committed deletion makes Update's work non-empty, so a plan that acted
# without asking (mutation M1) would show up in git status.
T=$(installed_repo sc4)
git -C "$T" rm -q "$EDITED" && git -C "$T" commit -q -m "delete one kit file"
pty_setup "$T" '1\nn\n3\n'; RC=$?
if [ "$RC" -eq 0 ] && clean "$T" \
   && [ "$(grep -c '1) Update (keeps your edits)' "$T.log")" -eq 2 ] \
   && grep -q 'Files to add or restore: 1' "$T.log" \
   && grep -q 'nothing was changed' "$T.log"; then
  pass "SC4: 'n' at the plan went back to the menu; Cancel left no change"
else
  fail "SC4: plan rejection then cancel (rc=$RC)"; git -C "$T" status --porcelain >&2; cat "$T.log" >&2
fi

# ── AC5 — invalid input re-prompts, takes no action ─────────────────────────
T=$(installed_repo ac5)
pty_setup "$T" '9\nabc\n3\n'; RC=$?
if [ "$RC" -eq 0 ] && clean "$T" \
   && [ "$(grep -c 'Please enter 1, 2 or 3' "$T.log")" -eq 2 ]; then
  pass "AC5: '9' and 'abc' each re-prompt; nothing changes"
else
  fail "AC5: invalid menu input (rc=$RC)"; cat "$T.log" >&2
fi
T=$(new_repo ac5-fresh)
pty_setup "$T" '7\n2\n'; RC=$?
if [ "$RC" -eq 0 ] && clean "$T" && grep -q 'Please enter 1 or 2' "$T.log"; then
  pass "AC5: invalid input on the install menu re-prompts; 2) Cancel writes nothing"
else
  fail "AC5: invalid input on the install menu (rc=$RC)"; cat "$T.log" >&2
fi

# ── SC3 / AC3 / AC6 — Reinstall backs up the edited file, named on the plan ──
T=$(installed_repo sc3)
printf '\nMY LOCAL EDIT\n' >> "$T/$EDITED"
pty_setup "$T" '2\n\n\n\n'; RC=$?
keep_transcript "$T.log" SC3.txt
PLAN_AT=$(line_of "$T.log" "      $EDITED")
ASK_AT=$(line_of "$T.log" 'Proceed? [Y/n]')
if [ "$RC" -eq 0 ] && grep -q 'MY LOCAL EDIT' "$T/$EDITED.bak" \
   && cmp -s "$FIXTURE/$EDITED" "$T/$EDITED" \
   && [ "$PLAN_AT" -gt 0 ] && [ "$PLAN_AT" -lt "$ASK_AT" ]; then
  pass "SC3: edit saved as $EDITED.bak, kit version installed, plan named it before Proceed"
else
  fail "SC3: reinstall backup (rc=$RC plan-line=$PLAN_AT ask-line=$ASK_AT)"; cat "$T.log" >&2
fi
# Only the edited file was backed up, and the lock now matches the kit copy.
if [ "$(find "$T" -name '*.bak*' -not -path '*/.git/*' | wc -l | tr -d ' ')" -eq 1 ] \
   && grep -q "\"$EDITED\": \"$(sha256sum "$FIXTURE/$EDITED" | awk '{print $1}')\"" "$T/.claude/harness-lock.json"; then
  pass "SC3: exactly one backup made; lock rewritten with the kit's hash"
else
  fail "SC3: extra backups or stale lock"; find "$T" -name '*.bak*' -not -path '*/.git/*' >&2
fi

# ── Reinstall honours MANIFEST `!` exclusions (T113) ─────────────────────────
T=$(installed_repo excl)
mkdir -p "$T/.claude/hooks/tests"
printf 'my own test\n' > "$T/.claude/hooks/tests/test_mine.py"
git -C "$T" add -A && git -C "$T" commit -q -m "project's own hook tests"
pty_setup "$T" '2\n\n\n\n'; RC=$?
if [ "$RC" -eq 0 ] && [ "$(cat "$T/.claude/hooks/tests/test_mine.py")" = 'my own test' ] \
   && [ ! -e "$T/.claude/hooks/tests.bak" ] \
   && ! grep -q '.claude/hooks/tests' "$T/.claude/harness-lock.json" \
   && [ -z "$(git -C "$T" status --porcelain -- .claude/hooks/tests)" ]; then
  pass "Reinstall leaves the project's own .claude/hooks/tests untouched; no tests.bak"
else
  fail "Reinstall touched an excluded path (rc=$RC)"; ls -a "$T/.claude/hooks" >&2; cat "$T.log" >&2
fi

# ── AC3 — Update's plan lists removals, kept edits and the files it will ask ──
T=$(installed_repo plan-update)
printf '\nMY EDIT\n' >> "$T/$EDITED"
git -C "$FIXTURE" rm -q -r skills/optimize && git -C "$FIXTURE" commit -q -m "stop shipping optimize"
pty_setup "$T" '1\nn\n3\n'; RC=$?
ASK_AT=$(line_of "$T.log" 'Proceed? [Y/n]')
RM_AT=$(line_of "$T.log" '      skills/optimize')
EDIT_AT=$(line_of "$T.log" "      $EDITED")
if [ "$RC" -eq 0 ] && [ "$RM_AT" -gt 0 ] && [ "$RM_AT" -lt "$ASK_AT" ] \
   && [ "$EDIT_AT" -gt 0 ] && [ "$EDIT_AT" -lt "$ASK_AT" ] \
   && grep -q 'they will be removed' "$T.log" && [ -d "$T/skills/optimize" ]; then
  pass "AC3: Update plan names the removal (skills/optimize) and the edited file before Proceed"
else
  fail "AC3: Update plan contents (rc=$RC rm=$RM_AT edit=$EDIT_AT ask=$ASK_AT)"; cat "$T.log" >&2
fi
git -C "$FIXTURE" revert --no-edit HEAD >/dev/null

# ── Stage 4 P1 — Reinstall keeps T113's removal contract (same as Update) ────
# Upstream stops shipping skills/optimize (unedited) and, in the second repo,
# the project has edited it. Reinstall removes the unedited one, keeps the edited
# one in the lock, and names both on the plan before Proceed.
lock_has() { grep -qF "\"$2\"" "$1"; }
T=$(installed_repo rein-rm)
T2=$(installed_repo rein-keep)
printf '\nMY SKILL EDIT\n' >> "$T2/skills/optimize/SKILL.md"
T3=$(installed_repo rein-incomplete)
git -C "$FIXTURE" rm -q -r skills/optimize && git -C "$FIXTURE" commit -q -m "stop shipping optimize"
pty_setup "$T" '2\n\n\n\n'; RC=$?
RM_AT=$(line_of "$T.log" '      skills/optimize')
ASK_AT=$(line_of "$T.log" 'Proceed? [Y/n]')
if [ "$RC" -eq 0 ] && [ ! -e "$T/skills/optimize" ] \
   && ! lock_has "$T/.claude/harness-lock.json" "skills/optimize/SKILL.md" \
   && grep -q 'they will be removed' "$T.log" && [ "$RM_AT" -gt 0 ] && [ "$RM_AT" -lt "$ASK_AT" ]; then
  pass "Reinstall: unedited file upstream dropped is removed, named on the plan, out of the lock"
else
  fail "Reinstall: unedited dropped file (rc=$RC rm=$RM_AT ask=$ASK_AT)"; cat "$T.log" >&2
fi
pty_setup "$T2" '2\n\n\n\n'; RC=$?
KEEP_AT=$(line_of "$T2.log" '      skills/optimize/SKILL.md')
ASK_AT=$(line_of "$T2.log" 'Proceed? [Y/n]')
if [ "$RC" -eq 0 ] && grep -q 'MY SKILL EDIT' "$T2/skills/optimize/SKILL.md" \
   && lock_has "$T2/.claude/harness-lock.json" "skills/optimize/SKILL.md" \
   && grep -q 'you edited them; they will be kept' "$T2.log" \
   && [ "$KEEP_AT" -gt 0 ] && [ "$KEEP_AT" -lt "$ASK_AT" ]; then
  pass "Reinstall: edited file upstream dropped is kept, stays in the lock, named on the plan"
else
  fail "Reinstall: edited dropped file (rc=$RC keep=$KEEP_AT ask=$ASK_AT)"; cat "$T2.log" >&2
fi
# /verify: the empty-backup line must stay true when an edited file is kept.
if grep -q 'Upstream no longer ships these, but you edited them' "$T2.log" \
   && ! grep -q 'no kit file has been edited' "$T2.log"; then
  pass "Reinstall plan: empty-backup wording does not deny the edited file it lists"
else
  fail "Reinstall plan: says 'no kit file has been edited' beside an edited file"; grep -n 'edited' "$T2.log" >&2
fi
# Incomplete upstream (a whole MANIFEST path gone): nothing removed, said so, exit 2.
git -C "$FIXTURE" rm -q -r .cursor/rules && git -C "$FIXTURE" commit -q -m "incomplete upstream"
pty_setup "$T3" '2\n\n\n\n'; RC=$?
if [ "$RC" -eq 2 ] && [ -f "$T3/skills/optimize/SKILL.md" ] \
   && lock_has "$T3/.claude/harness-lock.json" "skills/optimize/SKILL.md" \
   && grep -q 'Removals skipped' "$T3.log" && grep -q 'nothing was removed' "$T3.log"; then
  pass "Reinstall: incomplete upstream removes nothing, says so, exits 2 (as Update)"
else
  fail "Reinstall: incomplete upstream (rc=$RC)"; cat "$T3.log" >&2
fi
git -C "$FIXTURE" reset -q --hard HEAD~2

# ── SC5 / AC7 — `cat setup.sh | sh`: prompts still reach the terminal ───────
# Answers: Enter (Install), 2 (existing/legacy project), Enter (plan). The pack
# prompt is stdin-gated (T115's) and is skipped because stdin is the script.
T=$(new_repo sc5)
pty_setup "$T" '\n2\n\n' "cat '$SETUP' | sh"; RC=$?
if [ "$RC" -eq 0 ] && grep -q 'bootstrapping a full checkout' "$T.log" \
   && grep -q '"claude_md_source": "CLAUDE_LEGACY.md"' "$T/.claude/harness-lock.json" 2>/dev/null \
   && cmp -s "$FIXTURE/CLAUDE_LEGACY.md" "$T/CLAUDE.md"; then
  pass "SC5: piped install read its answers from the terminal (brownfield took effect)"
else
  fail "SC5: piped install answers (rc=$RC)"; cat "$T.log" >&2
fi

# ── SC6 / AC8 — no terminal + lock: Update, edits kept, exit 2, no Reinstall ─
if [ "$HAVE_SETSID" -eq 1 ]; then
  T=$(installed_repo sc6)
  printf '\nMY LOCAL EDIT\n' >> "$T/$EDITED"
  notty_setup "$T"; RC=$?
  keep_transcript "$T.log" SC6.txt
  if [ "$RC" -eq 2 ] && grep -qi 'no terminal — updating, keeping your edits' "$T.log" \
     && grep -q 'MY LOCAL EDIT' "$T/$EDITED" \
     && [ -z "$(find "$T" -name '*.bak*' -not -path '*/.git/*')" ] \
     && ! grep -q 'Reinstall complete' "$T.log" && ! grep -q 'Choose \[1\]' "$T.log"; then
    pass "SC6: no terminal -> Update, edit kept, exit 2, no menu, nothing reinstalled"
  else
    fail "SC6: no-terminal update (rc=$RC)"; cat "$T.log" >&2
  fi
  # /verify: with no terminal there is nobody to ask — no prompt line, only the warning.
  if ! grep -qF 'Resolve: [o]verwrite' "$T.log" \
     && grep -q "no input for '$EDITED'" "$T.log" && grep -qF -- '-MY LOCAL EDIT' "$T.log"; then
    pass "SC6: no conflict prompt printed without a terminal; warning and diff kept"
  else
    fail "SC6: no-terminal output prints the Resolve prompt"; grep -n "Resolve\|no input" "$T.log" >&2
  fi
else
  skip "SC6: setsid (util-linux) not found — cannot remove the controlling terminal"
fi

# ── SC7 / AC8 — no terminal, no lock: installs with printed defaults ────────
if [ "$HAVE_SETSID" -eq 1 ]; then
  T=$(new_repo sc7)
  notty_setup "$T"; RC=$?
  if [ "$RC" -eq 0 ] && [ -f "$T/.claude/harness-lock.json" ] \
     && grep -q 'No terminal — installing with the defaults: CLI Claude Code, new project (CLAUDE.md)' "$T.log" \
     && ! grep -q 'Choose \[1\]' "$T.log"; then
    pass "SC7: no terminal -> installs with the printed defaults, exit 0"
  else
    fail "SC7: no-terminal install (rc=$RC)"; cat "$T.log" >&2
  fi
else
  skip "SC7: setsid (util-linux) not found — cannot remove the controlling terminal"
fi

# ── SC8 / AC9 — update.sh from a checkout: same menus, Update action ────────
T=$(installed_repo sc8)
git -C "$FIXTURE" rm -q "$EDITED" && git -C "$FIXTURE" commit -q -m "drop one file upstream"
pty_setup "$T" '\n\n' "sh '$FIXTURE/update.sh'"; RC=$?
if [ "$RC" -eq 0 ] && grep -q '1) Update (keeps your edits)' "$T.log" \
   && grep -q 'Update complete' "$T.log" && [ ! -e "$T/$EDITED" ]; then
  pass "SC8: update.sh shows the same menu and runs Update (Enter, Enter)"
else
  fail "SC8: update.sh alias (rc=$RC)"; cat "$T.log" >&2
fi
git -C "$FIXTURE" revert -q --no-edit HEAD

# update.sh where nothing is installed: refuses (it is the Update action only).
T=$(new_repo sc8-nolock)
( cd "$T" && SUPERVISOR_REPO="file://$FIXTURE" sh "$FIXTURE/update.sh" </dev/null >"$T.log" 2>&1 ); RC=$?
if [ "$RC" -eq 1 ] && clean "$T" && grep -q 'not installed here' "$T.log"; then
  pass "AC9: update.sh with no install exits 1 and writes nothing"
else
  fail "AC9: update.sh with no lock (rc=$RC)"; cat "$T.log" >&2
fi

# ── SC9 / AC9 — update.sh alone: prints the install command, exits 1 ────────
mkdir -p "$WORK/alone"
cp "$REPO_ROOT/update.sh" "$WORK/alone/update.sh"
OUT=$(sh "$WORK/alone/update.sh" 2>&1); RC=$?
if [ "$RC" -eq 1 ] && printf '%s' "$OUT" | grep -q 'curl -fsSL .*/setup.sh | sh'; then
  pass "SC9: update.sh with no adjacent setup.sh prints the install command, exit 1"
else
  fail "SC9: lone update.sh (rc=$RC): $OUT"
fi

# AC9: a thin alias — at most 15 lines of code (comments and blank lines aside).
CODE_LINES=$(grep -cvE '^[[:space:]]*(#|$)' "$REPO_ROOT/update.sh")
if [ "$CODE_LINES" -le 15 ]; then
  pass "AC9: update.sh is $CODE_LINES lines of code (<= 15)"
else
  fail "AC9: update.sh has $CODE_LINES lines of code (> 15)"
fi

# The alias seam is not a user option: an unknown value is an error.
T=$(new_repo seam)
( cd "$T" && EASYKIT_ACTION=reinstall SUPERVISOR_REPO="file://$FIXTURE" sh "$SETUP" </dev/null >"$T.log" 2>&1 ); RC=$?
if [ "$RC" -eq 1 ] && clean "$T" && grep -q "Unknown EASYKIT_ACTION" "$T.log"; then
  pass "seam: an unknown EASYKIT_ACTION is rejected before anything runs"
else
  fail "seam: EASYKIT_ACTION=reinstall (rc=$RC)"; cat "$T.log" >&2
fi

printf '\n----- summary: %s passed, %s failed -----\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
