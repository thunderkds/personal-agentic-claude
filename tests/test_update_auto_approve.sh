#!/bin/sh
# tests/test_update_auto_approve.sh — T174: Update settles edited files with one
# choice on the plan screen, and every Update run writes .claude/update-log.md.
#
# Self-contained and offline (file:// kit fixture, no network). Each case builds
# its own fixture kit, installs it with the REAL setup.sh, edits two kit files
# (CLAUDE.md, agents/qa.md), publishes a newer fixture commit (both files bumped,
# agents/new.md added, skills/old dropped), then runs Update:
#   SC1  pty, choice 2 -> both overwritten, both backed up, log "auto-approve (overwrite all)"
#   SC2  pty, choice 3 -> both kept, no backups, exit 0, log "auto-approve (keep all)"
#   SC3  pty, choice 1 then o, s -> per-file flow, log "asked per file"; Enter = 1
#   SC4  pty, choice 4 -> tree unchanged, no log
#   SC5  pty, x then 2 -> re-asks once, then as SC1
#   SC6  no edited files -> Proceed? [Y/n], no list, log "no edited files"
#   SC7  no terminal -> edits kept, exit 2, log "no terminal (kept edits)"
#   SC8  choice 2, one backup forced to fail -> that file kept + logged, other overwritten
#   SC9  update-log.md is a directory / a symlink -> warning, outcome unchanged
#   SC10 two runs -> two entries, newest first, older entry byte-for-byte
#   AC9  an UPDATE_MODE value in the environment selects nothing
#   OLD  lock without kit_commit -> header says "unknown → <new>"
#   M1   mutation: drop the backup call -> SC1's backup assertion must fail
#
# Prompts read /dev/tty (T114), so answers are typed into a real pty
# (tests/lib/pty.sh run_in_pty); the suite itself is detached from the terminal
# so a plain run takes the no-terminal path.
#
# Run: bash tests/test_update_auto_approve.sh
set -u

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)
SETUP="$REPO_ROOT/setup.sh"
UPDATE_LIB="$REPO_ROOT/lib/harness-update.sh"
# shellcheck source=tests/lib/pty.sh
. "$SCRIPT_DIR/lib/pty.sh"
detach_from_terminal "$0" "$@"

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1" >&2; }

WORK=$(mktemp -d "${TMPDIR:-/tmp}/update-auto-approve-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT INT TERM HUP

USER_MARK="USER-EDIT-MARKER"
UP_MARK="UPSTREAM-V2-MARKER"
LIST_HEAD='How should Update treat your edited files?'

lock_field() {
  sed '/"files"[[:space:]]*:/,$d' "$1" 2>/dev/null | grep -F "\"$2\": \"" | head -n1 \
    | sed -e 's/.*: "//' -e 's/".*//'
}

git_commit() {
  git -C "$1" add -A
  git -C "$1" -c user.email=t@example.com -c user.name=t commit -q -m "$2"
}

# new_case <name> [noedit] -> sets C (case dir), F (fixture kit), P (project),
# C1 (kit_commit at install). Edits CLAUDE.md + agents/qa.md unless "noedit",
# then publishes the newer fixture commit.
new_case() {
  C="$WORK/$1"; F="$C/fixture"; P="$C/project"
  mkdir -p "$F/agents" "$F/skills/brainstorming" "$F/skills/old" "$P"
  printf 'qa v1\n'      > "$F/agents/qa.md"
  printf 'backend v1\n' > "$F/agents/backend.md"
  printf 'skill v1\n'   > "$F/skills/brainstorming/SKILL.md"
  printf 'old skill\n'  > "$F/skills/old/SKILL.md"
  printf 'GREENFIELD RULES\nv1\n' > "$F/CLAUDE.md"
  printf 'BROWNFIELD RULES\nv1\n' > "$F/CLAUDE_LEGACY.md"
  printf 'agents\nskills\n' > "$F/MANIFEST"
  git -C "$F" init -q && git_commit "$F" v1
  git -C "$P" init -q
  if ! ( cd "$P" && SUPERVISOR_REPO="file://$F" bash "$SETUP" </dev/null >"$C/install.log" 2>&1 ); then
    fail "$1: fixture install failed"; cat "$C/install.log" >&2
  fi
  C1=$(lock_field "$P/.claude/harness-lock.json" kit_commit)
  if [ "${2:-}" != noedit ]; then
    printf '%s\n' "$USER_MARK" >> "$P/CLAUDE.md"
    printf '%s\n' "$USER_MARK" >> "$P/agents/qa.md"
    cp "$P/CLAUDE.md" "$C/user-CLAUDE.md"
    cp "$P/agents/qa.md" "$C/user-qa.md"
  fi
  bump_fixture
}

bump_fixture() {
  printf '%s\n' "$UP_MARK" >> "$F/CLAUDE.md"
  printf '%s\n' "$UP_MARK" >> "$F/agents/qa.md"
  printf 'new agent\n' > "$F/agents/new-$(git -C "$F" rev-list --count HEAD).md"
  [ -d "$F/skills/old" ] && git -C "$F" rm -q -r skills/old
  git_commit "$F" "bump"
}

# run_pty <answers> -> RC, OUT (CR and colour stripped), C2 (new kit_commit)
run_pty() {
  ( cd "$P" && SUPERVISOR_REPO="file://$F" run_in_pty "$1" "bash '$SETUP'" ) >"$C/raw.log" 2>&1
  RC=$?
  sed 's/\x1b\[[0-9;]*m//g; s/\r$//; s/\r/\n/g' "$C/raw.log" > "$C/out.log"
  OUT="$C/out.log"
  C2=$(lock_field "$P/.claude/harness-lock.json" kit_commit)
}

run_noterm() {
  ( cd "$P" && SUPERVISOR_REPO="file://$F" bash "$SETUP" </dev/null ) >"$C/out.log" 2>&1
  RC=$?
  OUT="$C/out.log"
  C2=$(lock_field "$P/.claude/harness-lock.json" kit_commit)
}

LOG_OF() { printf '%s' "$P/.claude/update-log.md"; }

# ok <description> <shell test, eval'd>
DUMP=0
ok() {
  if eval "$2"; then pass "$1"; else fail "$1"; DUMP=1; fi
}
dump() { [ "$DUMP" -eq 1 ] && { printf -- '--- %s output ---\n' "$1" >&2; cat "$OUT" >&2; [ -f "$(LOG_OF)" ] && { printf -- '--- update-log ---\n' >&2; cat "$(LOG_OF)" >&2; }; }; DUMP=0; }

header_re() { printf '^## [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2} — Update %s → %s$' "$1" "$2"; }
no_contents() { ! grep -q -e "$USER_MARK" -e "$UP_MARK" -e 'GREENFIELD' "$(LOG_OF)"; }

# assert_overwrite_all <label>: the SC1 outcome, shared by SC1/SC5/SC9.
assert_overwrite_all() {
  ok "$1: exit 0" '[ "$RC" -eq 0 ]'
  ok "$1: CLAUDE.md == upstream" 'cmp -s "$P/CLAUDE.md" "$F/CLAUDE.md"'
  ok "$1: agents/qa.md == upstream" 'cmp -s "$P/agents/qa.md" "$F/agents/qa.md"'
  ok "$1: CLAUDE.md.bak-$C1 holds your edit" 'cmp -s "$P/CLAUDE.md.bak-$C1" "$C/user-CLAUDE.md"'
  ok "$1: agents/qa.md.bak-$C1 holds your edit" 'cmp -s "$P/agents/qa.md.bak-$C1" "$C/user-qa.md"'
  ok "$1: no per-file prompt" '! grep -q "Resolve: \[o\]verwrite" "$OUT"'
}

# =============================================================================
# SC1 — choice 2: overwrite all, each backed up first
# =============================================================================
new_case sc1
run_pty '\n2\n'
for _l in "$LIST_HEAD" '  1) Ask me about each one' '  2) Overwrite all of them (each backed up first)' \
          '  3) Keep all of them' '  4) Cancel'; do
  ok "SC1/AC1: list line '$_l'" 'grep -Fxq "$_l" "$OUT"'
done
ok "SC1/AC1: prompt 'Choice [1]: '" 'grep -Fq "Choice [1]: " "$OUT"'
ok "SC1/AC1: no Proceed? [Y/n] when there are edited files" '! grep -Fq "Proceed? [Y/n]" "$OUT"'
assert_overwrite_all SC1
ok "SC1/AC7: log header is the first line" 'head -n1 "$(LOG_OF)" | grep -Eq "$(header_re "$C1" "$C2")"'
ok "SC1/AC7: Decided by: auto-approve (overwrite all)" 'grep -Fxq "Decided by: auto-approve (overwrite all)" "$(LOG_OF)"'
ok "SC1/AC7: CLAUDE.md line names its backup" 'grep -Fxq "- CLAUDE.md — overwrote (your edits; backup CLAUDE.md.bak-$C1)" "$(LOG_OF)"'
ok "SC1/AC7: agents/qa.md line names its backup" 'grep -Fxq "- agents/qa.md — overwrote (your edits; backup agents/qa.md.bak-$C1)" "$(LOG_OF)"'
ok "SC1/AC7: removal logged" 'grep -Fxq "- skills/old — removed (upstream no longer ships it)" "$(LOG_OF)"'
ok "SC1/AC7: refreshed count" 'grep -Eq "^- [0-9]+ kit files you never edited — refreshed$" "$(LOG_OF)"'
ok "SC1/AC7: added count = 1" 'grep -Fxq "- 1 files added" "$(LOG_OF)"'
ok "SC1/AC8: log holds no file contents" 'no_contents'
dump SC1

# =============================================================================
# SC2 — choice 3: keep all
# =============================================================================
new_case sc2
run_pty '\n3\n'
ok "SC2: exit 0 (the user decided)" '[ "$RC" -eq 0 ]'
ok "SC2: CLAUDE.md is your version" 'cmp -s "$P/CLAUDE.md" "$C/user-CLAUDE.md"'
ok "SC2: agents/qa.md is your version" 'cmp -s "$P/agents/qa.md" "$C/user-qa.md"'
ok "SC2: no backups" '[ -z "$(find "$P" -name "*.bak*" -not -path "*/.git/*")" ]'
ok "SC2: no per-file prompt" '! grep -q "Resolve: \[o\]verwrite" "$OUT"'
ok "SC2: Decided by: auto-approve (keep all)" 'grep -Fxq "Decided by: auto-approve (keep all)" "$(LOG_OF)"'
ok "SC2: both files logged as kept" '[ "$(grep -Ec "^- (CLAUDE.md|agents/qa.md) — kept your version$" "$(LOG_OF)")" -eq 2 ]'
dump SC2

# =============================================================================
# SC3 — choice 1 (and Enter = 1): today's per-file flow
# =============================================================================
for _ans in '1' ''; do
  new_case "sc3-${_ans:-enter}"
  run_pty "\n$_ans\no\ns\n"
  _t="SC3 (answer '${_ans:-Enter}')"
  ok "$_t: exit 0" '[ "$RC" -eq 0 ]'
  ok "$_t: per-file prompt asked twice" '[ "$(grep -o "Resolve: \[o\]verwrite / \[s\]kip / \[v\]iew diff again:" "$OUT" | wc -l)" -eq 2 ]'
  ok "$_t: agents/qa.md overwritten (o)" 'cmp -s "$P/agents/qa.md" "$F/agents/qa.md" && cmp -s "$P/agents/qa.md.bak-$C1" "$C/user-qa.md"'
  ok "$_t: CLAUDE.md kept (s)" 'cmp -s "$P/CLAUDE.md" "$C/user-CLAUDE.md" && [ ! -e "$P/CLAUDE.md.bak-$C1" ]'
  ok "$_t: Decided by: asked per file" 'grep -Fxq "Decided by: asked per file" "$(LOG_OF)"'
  ok "$_t: one overwrote + one kept" 'grep -Fxq "- agents/qa.md — overwrote (your edits; backup agents/qa.md.bak-$C1)" "$(LOG_OF)" && grep -Fxq "- CLAUDE.md — kept your version" "$(LOG_OF)"'
  dump "$_t"
done

# =============================================================================
# SC4 — choice 4: nothing changes, no log
# =============================================================================
snapshot() { ( cd "$P" && find . -path ./.git -prune -o -print | LC_ALL=C sort && find . -path ./.git -prune -o -type f -exec sha256sum {} + | LC_ALL=C sort ); }
new_case sc4
snapshot > "$C/before.snap"
run_pty '\n4\n'
ok "SC4: exit 0, same as cancelling" '[ "$RC" -eq 0 ]'
ok "SC4: tree unchanged" 'snapshot | cmp -s - "$C/before.snap"'
ok "SC4: no .claude/update-log.md" '[ ! -e "$(LOG_OF)" ]'
dump SC4

# EOF at the list cancels too (edge case): no answer after the menu.
new_case eof
snapshot > "$C/before.snap"
run_pty '\n'
ok "EOF at the list: exit 0, tree unchanged, no log" '[ "$RC" -eq 0 ] && snapshot | cmp -s - "$C/before.snap" && [ ! -e "$(LOG_OF)" ]'
dump EOF

# =============================================================================
# SC5 — invalid input re-asks once
# =============================================================================
new_case sc5
run_pty '\nx\n2\n'
ok "SC5: re-asked once" '[ "$(grep -c "Please enter 1, 2, 3 or 4." "$OUT")" -eq 1 ] && [ "$(grep -o "Choice \[1\]: " "$OUT" | wc -l)" -eq 2 ]'
assert_overwrite_all SC5
dump SC5

# =============================================================================
# SC6 — no edited files: Proceed? [Y/n], no list
# =============================================================================
new_case sc6 noedit
run_pty '\n\n'
ok "SC6: exit 0" '[ "$RC" -eq 0 ]'
ok "SC6: Proceed? [Y/n] shown" 'grep -Fq "Proceed? [Y/n]" "$OUT"'
ok "SC6: list not shown" '! grep -Fq "$LIST_HEAD" "$OUT"'
ok "SC6: Decided by: no edited files" 'grep -Fxq "Decided by: no edited files" "$(LOG_OF)"'
ok "SC6: counts present" 'grep -Eq "^- [0-9]+ kit files you never edited — refreshed$" "$(LOG_OF)" && grep -Fxq "- 1 files added" "$(LOG_OF)"'
dump SC6

# =============================================================================
# SC7 — no terminal: today's behaviour, plus a log entry
# =============================================================================
new_case sc7
run_noterm
ok "SC7: exit 2 (unresolved edits)" '[ "$RC" -eq 2 ]'
ok "SC7: both files kept" 'cmp -s "$P/CLAUDE.md" "$C/user-CLAUDE.md" && cmp -s "$P/agents/qa.md" "$C/user-qa.md"'
ok "SC7: Decided by: no terminal (kept edits)" 'grep -Fxq "Decided by: no terminal (kept edits)" "$(LOG_OF)"'
ok "SC7: both logged as kept" '[ "$(grep -Ec "^- (CLAUDE.md|agents/qa.md) — kept your version$" "$(LOG_OF)")" -eq 2 ]'
ok "SC7: log holds no file contents" 'no_contents'
dump SC7

# =============================================================================
# SC8 — choice 2, the backup of agents/qa.md fails (fake mv)
# =============================================================================
new_case sc8
mkdir -p "$C/bin"
REAL_MV=$(command -v mv)
cat > "$C/bin/mv" <<EOF
#!/bin/sh
if [ "\$1" = ./agents/qa.md ]; then
  printf "mv: cannot move '%s': Permission denied\n" "\$1" >&2
  exit 1
fi
exec $REAL_MV "\$@"
EOF
chmod +x "$C/bin/mv"
PATH="$C/bin:$PATH" run_pty '\n2\n'
ok "SC8: agents/qa.md kept (never overwritten without a backup)" 'cmp -s "$P/agents/qa.md" "$C/user-qa.md" && [ -z "$(find "$P/agents" -name "qa.md.bak*")" ]'
ok "SC8: CLAUDE.md overwritten with its backup" 'cmp -s "$P/CLAUDE.md" "$F/CLAUDE.md" && cmp -s "$P/CLAUDE.md.bak-$C1" "$C/user-CLAUDE.md"'
ok "SC8: exit 2 (counted unresolved)" '[ "$RC" -eq 2 ]'
ok "SC8: logged as kept (backup failed: ...)" 'grep -Eq "^- agents/qa.md — kept \(backup failed: .+\)$" "$(LOG_OF)"'
ok "SC8: CLAUDE.md logged as overwrote" 'grep -Fxq "- CLAUDE.md — overwrote (your edits; backup CLAUDE.md.bak-$C1)" "$(LOG_OF)"'
dump SC8

# =============================================================================
# SC9 — the log path is a directory, then a symlink
# =============================================================================
new_case sc9
mkdir -p "$P/.claude/update-log.md"
run_pty '\n2\n'
ok "SC9: warning names the update log" 'grep -q "\[warn\].*update-log.md" "$OUT"'
assert_overwrite_all SC9
ok "SC9: the directory is left alone" '[ -d "$(LOG_OF)" ] && [ -z "$(ls -A "$(LOG_OF)")" ]'
dump SC9

new_case sc9-link
printf 'outside\n' > "$C/outside.md"
ln -s "$C/outside.md" "$P/.claude/update-log.md"
run_pty '\n2\n'
ok "SC9 symlink: warning printed" 'grep -q "\[warn\].*update-log.md" "$OUT"'
ok "SC9 symlink: nothing written through the link" '[ "$(cat "$C/outside.md")" = outside ] && [ -L "$(LOG_OF)" ]'
ok "SC9 symlink: update outcome unchanged" '[ "$RC" -eq 0 ] && cmp -s "$P/CLAUDE.md" "$F/CLAUDE.md"'
dump SC9-link

# =============================================================================
# SC10 — two runs: newest on top, older entry byte-for-byte (user text kept)
# =============================================================================
new_case sc10
run_pty '\n3\n'
_first_c2="$C2"
printf '\nMy own note under the log.\n' >> "$(LOG_OF)"
cp "$(LOG_OF)" "$C/log-after-1"
bump_fixture
run_pty '\n2\n'
ok "SC10: two entries" '[ "$(grep -c "^## " "$(LOG_OF)")" -eq 2 ]'
ok "SC10: newest first" 'head -n1 "$(LOG_OF)" | grep -Eq "$(header_re "$_first_c2" "$C2")"'
_n1=$(wc -c < "$C/log-after-1")
ok "SC10: the older entry (and your note) stay byte-for-byte" 'tail -c "$_n1" "$(LOG_OF)" | cmp -s - "$C/log-after-1"'
dump SC10

# =============================================================================
# AC9 — no env var selects auto-approve; EASYKIT_ACTION stays the only seam
# =============================================================================
new_case ac9
( cd "$P" && UPDATE_MODE=overwrite_all SUPERVISOR_REPO="file://$F" bash "$SETUP" </dev/null ) >"$C/out.log" 2>&1
RC=$?; OUT="$C/out.log"
ok "AC9: UPDATE_MODE in the environment overwrites nothing" '[ "$RC" -eq 2 ] && cmp -s "$P/CLAUDE.md" "$C/user-CLAUDE.md" && cmp -s "$P/agents/qa.md" "$C/user-qa.md"'
dump AC9
_seams=$(grep -ho 'EASYKIT_[A-Z_]*' "$SETUP" "$REPO_ROOT/update.sh" "$UPDATE_LIB" | sort -u | tr '\n' ' ')
ok "AC9: EASYKIT_ACTION is the only EASYKIT_ variable read (got: $_seams)" '[ "$_seams" = "EASYKIT_ACTION " ]'

# =============================================================================
# OLD — a lock written before T137 has no kit_commit
# =============================================================================
new_case old
sed -i.orig '/"kit_commit"/d' "$P/.claude/harness-lock.json"
run_noterm
ok "OLD: header says unknown → <new>" 'head -n1 "$(LOG_OF)" | grep -Eq "$(header_re unknown "$C2")"'
dump OLD

# =============================================================================
# M1 — mutation: drop the backup call; SC1's backup assertion must fail
# =============================================================================
M="$WORK/mutant"
mkdir -p "$M/lib"
cp "$SETUP" "$REPO_ROOT/update.sh" "$M/"
cp "$REPO_ROOT/lib/"* "$M/lib/"
sed 's/if ! harness_backup_path "\$_src" "\$_dst"/if false/' "$UPDATE_LIB" > "$M/lib/harness-update.sh"
if cmp -s "$UPDATE_LIB" "$M/lib/harness-update.sh"; then
  fail "M1: mutation did not apply (pattern not found in lib/harness-update.sh)"
else
  new_case m1
  _real_setup="$SETUP"; SETUP="$M/setup.sh"
  run_pty '\n2\n'
  SETUP="$_real_setup"
  if cmp -s "$P/CLAUDE.md.bak-$C1" "$C/user-CLAUDE.md"; then
    fail "M1: mutant without the backup call still left a backup — SC1 cannot catch it"
  else
    pass "M1: dropping the backup call is caught by SC1's backup assertion"
  fi
fi

printf '\n%s passed, %s failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
