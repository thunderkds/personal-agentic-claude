#!/bin/sh
# tests/test_install_backups.sh — first install never destroys a project's own
# files (T112 / ADR-0002 "No silent loss").
#
# Self-contained, offline: builds a local fixture "kit" repo and runs the real
# setup.sh against scratch git repos under mktemp -d via a file:// URL.
# Covers SC1–SC7 of tasks/TASK_GUIDE_T112.md plus mutation control M1.
#
# Run: bash tests/test_install_backups.sh   (or: sh tests/test_install_backups.sh)
set -u

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)
SETUP="$REPO_ROOT/setup.sh"

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1" >&2; }

WORK=$(mktemp -d "${TMPDIR:-/tmp}/backup-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT INT TERM HUP

# ── Fixture kit repo ─────────────────────────────────────────────────────────
FIXTURE="$WORK/fixture-repo"
mkdir -p "$FIXTURE/agents" "$FIXTURE/skills/brainstorming" \
         "$FIXTURE/.claude/hooks" "$FIXTURE/templates" "$FIXTURE/lib"
printf 'backend-agent-content\n' > "$FIXTURE/agents/backend.md"
printf 'skill-content\n'         > "$FIXTURE/skills/brainstorming/SKILL.md"
printf 'hook-content\n'          > "$FIXTURE/.claude/hooks/example_hook.py"
printf 'kit-template\n'          > "$FIXTURE/templates/TASK_GUIDE_template.md"
printf '# AGENTS.md\n'           > "$FIXTURE/AGENTS.md"
printf '{ "hooks": {} }\n'       > "$FIXTURE/.claude/settings.json"
cp "$REPO_ROOT/lib/merge-settings.py" "$FIXTURE/lib/merge-settings.py"
printf '# Claude Project Supervisor Guidelines\n' > "$FIXTURE/CLAUDE.md"
printf 'BROWNFIELD\n'            > "$FIXTURE/CLAUDE_LEGACY.md"
cat > "$FIXTURE/MANIFEST" <<'EOF'
agents
skills
.claude/hooks
templates
AGENTS.md
EOF
git -C "$FIXTURE" init -q
git -C "$FIXTURE" config user.email "test@example.com"
git -C "$FIXTURE" config user.name "Test"
git -C "$FIXTURE" add -A
git -C "$FIXTURE" commit -q -m "fixture kit"

# new_repo <name> -> path of a fresh git-initialized target
new_repo() {
  mkdir -p "$WORK/$1"
  git -C "$WORK/$1" init -q
  printf '%s\n' "$WORK/$1"
}

# run_setup <target> [setup.sh path] -> exit code; log in <target>.log
run_setup() {
  _t="$1"
  _s="${2:-$SETUP}"
  ( cd "$_t" && SUPERVISOR_REPO="file://$FIXTURE" bash "$_s" </dev/null >"$_t.log" 2>&1 )
}

# no_bak <target> -> true when no backup path exists anywhere in <target>
no_bak() {
  [ -z "$(find "$1" -name '*.bak*' -not -path '*/.git/*' | head -n 1)" ]
}

# ── SC1 — pre-existing CLAUDE.md is backed up and named ─────────────────────
T=$(new_repo sc1)
printf '# my project rules\n' > "$T/CLAUDE.md"
run_setup "$T"; RC=$?
if [ "$RC" -eq 0 ] \
   && [ "$(cat "$T/CLAUDE.md.bak")" = '# my project rules' ] \
   && grep -q 'Supervisor Guidelines' "$T/CLAUDE.md" \
   && [ "$(grep -c 'CLAUDE.md.bak' "$T.log")" -eq 1 ]; then
  pass "SC1: CLAUDE.md moved to CLAUDE.md.bak, kit installed, backup named once"
else
  fail "SC1: CLAUDE.md backup (rc=$RC)"; cat "$T.log" >&2
fi

# ── SC2 — pre-existing AGENTS.md (a MANIFEST file) is backed up and named ───
T=$(new_repo sc2)
printf '# my agents\n' > "$T/AGENTS.md"
run_setup "$T"; RC=$?
if [ "$RC" -eq 0 ] \
   && [ "$(cat "$T/AGENTS.md.bak")" = '# my agents' ] \
   && [ "$(cat "$T/AGENTS.md")" = '# AGENTS.md' ] \
   && grep -q 'AGENTS.md.bak' "$T.log"; then
  pass "SC2: AGENTS.md moved to AGENTS.md.bak, kit installed, backup named"
else
  fail "SC2: AGENTS.md backup (rc=$RC)"; cat "$T.log" >&2
fi

# ── SC3 — pre-existing directory is moved whole, kit dir installed ──────────
T=$(new_repo sc3)
mkdir -p "$T/templates"
printf 'my own template\n' > "$T/templates/mine.md"
run_setup "$T"; RC=$?
if [ "$RC" -eq 0 ] \
   && [ "$(cat "$T/templates.bak/mine.md" 2>/dev/null)" = 'my own template' ] \
   && [ -f "$T/templates/TASK_GUIDE_template.md" ] \
   && [ ! -e "$T/templates/mine.md" ] \
   && grep -q 'templates.bak' "$T.log"; then
  pass "SC3: templates/ moved to templates.bak/ with mine.md intact; kit templates/ installed"
else
  fail "SC3: directory backup (rc=$RC)"; cat "$T.log" >&2
fi

# ── SC4 — identical content: no backup, no backup line ──────────────────────
T=$(new_repo sc4)
printf '# AGENTS.md\n' > "$T/AGENTS.md"
mkdir -p "$T/templates"
printf 'kit-template\n' > "$T/templates/TASK_GUIDE_template.md"
run_setup "$T"; RC=$?
if [ "$RC" -eq 0 ] && no_bak "$T" && ! grep -q '\.bak' "$T.log"; then
  pass "SC4: identical AGENTS.md and templates/ left alone — no backup, no line"
else
  fail "SC4: identical content produced a backup (rc=$RC)"; cat "$T.log" >&2
fi

# ── SC5 — existing .bak is never overwritten; next free .bak.N is used ──────
T=$(new_repo sc5)
printf 'current\n'  > "$T/CLAUDE.md"
printf 'older\n'    > "$T/CLAUDE.md.bak"
run_setup "$T"; RC1=$?
printf 'current2\n' > "$T/CLAUDE.md"
run_setup "$T"; RC2=$?
if [ "$RC1" -eq 0 ] && [ "$RC2" -eq 0 ] \
   && [ "$(cat "$T/CLAUDE.md.bak")" = 'older' ] \
   && [ "$(cat "$T/CLAUDE.md.bak.1")" = 'current' ] \
   && [ "$(cat "$T/CLAUDE.md.bak.2")" = 'current2' ] \
   && grep -q 'CLAUDE.md.bak.2' "$T.log"; then
  pass "SC5: CLAUDE.md.bak untouched; backups went to .bak.1 then .bak.2"
else
  fail "SC5: backup numbering (rc=$RC1/$RC2)"; cat "$T.log" >&2
fi

# ── SC6 — non-git directory: rejected before any write or backup ───────────
T="$WORK/sc6"
mkdir -p "$T"
printf '# my project rules\n' > "$T/CLAUDE.md"
run_setup "$T"; RC=$?
if [ "$RC" -eq 1 ] \
   && [ "$(cat "$T/CLAUDE.md")" = '# my project rules' ] \
   && no_bak "$T"; then
  pass "SC6: non-git dir rejected (exit 1), CLAUDE.md unchanged, no backup"
else
  fail "SC6: non-git rejection (rc=$RC)"; cat "$T.log" >&2
fi

# ── SC7 — backups are not recorded in the lock ──────────────────────────────
# Reuses SC1–SC3 targets, which all hold backups next to kit files.
LOCK_BAD=0
for _n in sc1 sc2 sc3 sc5; do
  if grep -Eq '\.bak(\.[0-9]+)?"|\.bak(\.[0-9]+)?/' "$WORK/$_n/.claude/harness-lock.json"; then
    LOCK_BAD=1
  fi
done
if [ "$LOCK_BAD" -eq 0 ]; then
  pass "SC7: no .bak path appears in any harness-lock.json"
else
  fail "SC7: a backup path was recorded in harness-lock.json"
fi

# ── AC7 — empty repo: no backups, no backup line ────────────────────────────
T=$(new_repo empty)
run_setup "$T"; RC=$?
if [ "$RC" -eq 0 ] && no_bak "$T" && ! grep -q '\.bak' "$T.log"; then
  pass "AC7: empty repo installs with zero backups"
else
  fail "AC7: empty repo (rc=$RC)"; cat "$T.log" >&2
fi

# ── Edge — symlink at a MANIFEST path: the link moves, the target is untouched
T=$(new_repo symlink)
mkdir -p "$T/elsewhere"
printf 'target file\n' > "$T/elsewhere/keep.md"
ln -s elsewhere "$T/templates"
run_setup "$T"; RC=$?
if [ "$RC" -eq 0 ] && [ -L "$T/templates.bak" ] && [ ! -L "$T/templates" ] \
   && [ -f "$T/templates/TASK_GUIDE_template.md" ] \
   && [ "$(cat "$T/elsewhere/keep.md")" = 'target file' ] \
   && [ ! -e "$T/elsewhere/TASK_GUIDE_template.md" ]; then
  pass "edge: symlinked templates -> link moved to templates.bak, target untouched"
else
  fail "edge: symlink handling (rc=$RC)"; cat "$T.log" >&2
fi

# ── Edge — user's own .claude/hooks: backed up, warned by name ──────────────
T=$(new_repo hooks)
mkdir -p "$T/.claude/hooks"
printf 'mine\n' > "$T/.claude/hooks/my hook.py"
run_setup "$T"; RC=$?
if [ "$RC" -eq 0 ] && [ -f "$T/.claude/hooks.bak/my hook.py" ] \
   && grep -q "Your own hooks now live in '\./\.claude/hooks\.bak'" "$T.log"; then
  pass "edge: own .claude/hooks (spaced filename) backed up, settings.json warning printed"
else
  fail "edge: .claude/hooks backup (rc=$RC)"; cat "$T.log" >&2
fi

# ── Edge — a regular file where the kit has a directory ─────────────────────
T=$(new_repo typeswap)
printf 'not a dir\n' > "$T/templates"
run_setup "$T"; RC=$?
if [ "$RC" -eq 0 ] && [ "$(cat "$T/templates.bak")" = 'not a dir' ] \
   && [ -f "$T/templates/TASK_GUIDE_template.md" ]; then
  pass "edge: file at a directory path -> backed up, kit directory installed"
else
  fail "edge: type mismatch (rc=$RC)"; cat "$T.log" >&2
fi

# ── Edge — backup cannot be written: stop, keep the data, claim no backup ────
# Called in a condition, set -e does not fire inside the helper, so the helper
# must report the failed mv itself or the caller's rm -rf destroys the original.
T="$WORK/ro"
mkdir -p "$T/p/templates" "$T/kit/templates"
printf 'mine\n' > "$T/p/templates/mine.md"
printf 'kit\n'  > "$T/kit/templates/k.md"
chmod a-w "$T/p"
RO_OUT=$(sh -c '. "$1/lib/harness-fetch.sh"; set -e
  if harness_backup_path "$2/kit/templates" "$2/p/templates"; then echo HELPER_OK; fi' \
  _ "$REPO_ROOT" "$T" 2>&1)
chmod u+w "$T/p"
if [ "$(id -u)" -eq 0 ]; then
  pass "edge: unwritable backup — skipped (root ignores directory permissions)"
elif ! printf '%s' "$RO_OUT" | grep -q -e HELPER_OK -e 'Backed up' \
   && [ -f "$T/p/templates/mine.md" ]; then
  pass "edge: unwritable backup -> helper fails, no 'Backed up' claim, original intact"
else
  fail "edge: unwritable backup reported success: $RO_OUT"
fi

# ── M1 — mutation: restore the plain rm -rf → the SC3 check must fail ───────
MUT="$WORK/mutant"
mkdir -p "$MUT/lib"
cp "$SETUP" "$MUT/setup.sh"
cp "$REPO_ROOT/lib/"* "$MUT/lib/"
# shellcheck disable=SC2016  # the $_dst text is sed input, meant literally
sed -i.orig 's/^\([[:space:]]*\)harness_backup_path "\$_src" "\$_dst" || return 1$/\1[ -e "$_dst" ] \&\& rm -rf "$_dst"/' \
  "$MUT/lib/harness-fetch.sh"
if cmp -s "$MUT/lib/harness-fetch.sh" "$MUT/lib/harness-fetch.sh.orig"; then
  fail "M1: mutation did not land (sed matched nothing)"
else
  T=$(new_repo m1)
  mkdir -p "$T/templates"
  printf 'my own template\n' > "$T/templates/mine.md"
  run_setup "$T" "$MUT/setup.sh"
  if [ ! -e "$T/templates.bak/mine.md" ] && [ ! -e "$T/templates/mine.md" ]; then
    pass "M1: with the rm -rf restored, mine.md is destroyed — SC3 would fail"
  else
    fail "M1: mutant still preserved mine.md — SC3 is not load-bearing"
  fi
fi

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
