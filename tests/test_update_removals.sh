#!/bin/sh
# tests/test_update_removals.sh — POSIX-sh tests for T113.
#
# Offline (file:// upstream). Proves: update removes what upstream stopped shipping
# unless the user edited it; a `!<path>` MANIFEST line keeps the kit's own test suite
# out of installs; a corrupt/partial upstream never becomes a mass delete.
#
# Run: bash tests/test_update_removals.sh
set -u

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)
SETUP="$REPO_ROOT/setup.sh"
UPDATE="$REPO_ROOT/update.sh"

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1" >&2; }

WORK=$(mktemp -d "${TMPDIR:-/tmp}/update-removals.XXXXXX")
trap 'rm -rf "$WORK"' EXIT INT TERM HUP
NO_CLONE="$WORK/should-not-exist"

lock_has() { grep -qF "\"$2\": \"" "$1"; }

MANIFEST_OLD='agents
skills
.claude/hooks
templates'
MANIFEST_NEW="$MANIFEST_OLD
!.claude/hooks/tests"

# build_upstream <dir> <old|new>  — a fixture kit; `new` carries the `!` line.
build_upstream() {
  _u="$1"
  mkdir -p "$_u/agents" "$_u/skills/optimize" "$_u/skills/keep" "$_u/.claude/hooks/tests" \
           "$_u/templates" "$_u/lib"
  printf 'agent\n'    > "$_u/agents/backend.md"
  printf 'optimize\n' > "$_u/skills/optimize/SKILL.md"
  printf 'keep\n'     > "$_u/skills/keep/SKILL.md"
  printf 'hook\n'     > "$_u/.claude/hooks/example_hook.py"
  printf 'helper\n'   > "$_u/.claude/hooks/tests_helper.py"
  printf 'a test\n'   > "$_u/.claude/hooks/tests/test_a.py"
  printf 'tmpl\n'     > "$_u/templates/t.md"
  printf '{ "hooks": {} }\n' > "$_u/.claude/settings.json"
  cp "$REPO_ROOT/lib/merge-settings.py" "$_u/lib/merge-settings.py"
  printf 'GREENFIELD\n' > "$_u/CLAUDE.md"
  printf 'BROWNFIELD\n' > "$_u/CLAUDE_LEGACY.md"
  if [ "$2" = "new" ]; then printf '%s\n' "$MANIFEST_NEW" > "$_u/MANIFEST"
  else printf '%s\n' "$MANIFEST_OLD" > "$_u/MANIFEST"; fi
  git -C "$_u" init -q
  git -C "$_u" config user.email t@example.com
  git -C "$_u" config user.name T
  git -C "$_u" add -A
  git -C "$_u" commit -q -m fixture
}

# run_setup <target> <upstream>;  run_update <target> <upstream> [stdin]
run_setup() {
  ( cd "$1" && SUPERVISOR_REPO="file://$2" SUPERVISOR_PATH="$NO_CLONE" \
      bash "$SETUP" </dev/null >"$WORK/setup.log" 2>&1 )
}
run_update() {
  ( cd "$1" && SUPERVISOR_REPO="file://$2" bash "$UPDATE" <"${3:-/dev/null}" >"$WORK/update.log" 2>&1 )
}
new_project() {
  mkdir -p "$1"
  git -C "$1" init -q
}

# Upstream drops skills/optimize (a new commit on a fresh clone of the fixture).
drop_optimize() {
  git -C "$1" rm -rq skills/optimize
  git -C "$1" commit -q -m drop-optimize
}

# ── SC1: unedited skill dropped upstream is removed ──────────────────────────
U1="$WORK/up1"; build_upstream "$U1" new
P1="$WORK/p1"; new_project "$P1"; run_setup "$P1" "$U1" || { fail "sc1: setup failed"; cat "$WORK/setup.log" >&2; }
drop_optimize "$U1"
RC=0; run_update "$P1" "$U1" || RC=$?
[ "$RC" -eq 0 ] && pass "sc1: update exits 0" || { fail "sc1: update rc=$RC"; cat "$WORK/update.log" >&2; }
[ ! -e "$P1/skills/optimize" ] && pass "sc1: skills/optimize removed, incl. its now-empty directory" \
  || fail "sc1: skills/optimize still present"
[ -f "$P1/skills/keep/SKILL.md" ] && [ -d "$P1/skills" ] && pass "sc1: sibling skill and skills/ root kept" \
  || fail "sc1: sibling skill or skills/ root was removed"
lock_has "$P1/.claude/harness-lock.json" "skills/optimize/SKILL.md" \
  && fail "sc1: lock still holds skills/optimize/ entry" || pass "sc1: lock entry dropped"
[ "$(grep -c 'removed.*skills/optimize' "$WORK/update.log")" -eq 1 ] \
  && pass "sc1: exactly one 'removed' line for the skill" \
  || { fail "sc1: expected one 'removed' line naming skills/optimize"; cat "$WORK/update.log" >&2; }

# ── SC2: edited skill is kept, named, lock entry kept ────────────────────────
U2="$WORK/up2"; build_upstream "$U2" new
P2="$WORK/p2"; new_project "$P2"; run_setup "$P2" "$U2"
printf 'my edit\n' >> "$P2/skills/optimize/SKILL.md"
drop_optimize "$U2"
RC=0; run_update "$P2" "$U2" || RC=$?
[ "$RC" -eq 0 ] && pass "sc2: update exits 0" || fail "sc2: update rc=$RC"
grep -q 'my edit' "$P2/skills/optimize/SKILL.md" 2>/dev/null && pass "sc2: edited file kept" || fail "sc2: edited file lost"
grep -q "skills/optimize/SKILL.md" "$WORK/update.log" && pass "sc2: output names the kept path" || fail "sc2: kept path not named"
lock_has "$P2/.claude/harness-lock.json" "skills/optimize/SKILL.md" && pass "sc2: lock entry kept" || fail "sc2: lock entry dropped"

# ── SC3: a user-added file inside a removed skill survives ───────────────────
U3="$WORK/up3"; build_upstream "$U3" new
P3="$WORK/p3"; new_project "$P3"; run_setup "$P3" "$U3"
printf 'mine\n' > "$P3/skills/optimize/NOTES.md"
drop_optimize "$U3"
run_update "$P3" "$U3" || true
[ -f "$P3/skills/optimize/NOTES.md" ] && [ ! -e "$P3/skills/optimize/SKILL.md" ] \
  && pass "sc3: NOTES.md kept, kit file removed, directory not removed" \
  || fail "sc3: user file lost or kit file kept"

# ── SC4: fresh install of a `!` MANIFEST lands no kit tests, locks none ──────
U4="$WORK/up4"; build_upstream "$U4" new
P4="$WORK/p4"; new_project "$P4"; run_setup "$P4" "$U4"
[ ! -e "$P4/.claude/hooks/tests" ] && pass "sc4: .claude/hooks/tests not installed" || fail "sc4: tests dir installed"
[ -f "$P4/.claude/hooks/tests_helper.py" ] && pass "sc4: segment match — tests_helper.py still installed" \
  || fail "sc4: tests_helper.py wrongly excluded"
[ -f "$P4/.claude/hooks/example_hook.py" ] && pass "sc4: rest of .claude/hooks installed" || fail "sc4: hooks not installed"
grep -q '"\.claude/hooks/tests/' "$P4/.claude/harness-lock.json" \
  && fail "sc4: lock holds a .claude/hooks/tests/ key" || pass "sc4: no lock key under .claude/hooks/tests/"
[ ! -e "$P4/!.claude/hooks/tests" ] && pass "sc4: no literal '!' path created" || fail "sc4: literal '!' path created"
# update must not report the excluded files as new.
run_update "$P4" "$U4" || true
grep -q 'tests/test_a.py' "$WORK/update.log" && fail "sc4: update mentions excluded tests" || pass "sc4: update ignores excluded tests"

# ── SC5: existing install with tests gets them removed on the next update ────
U5="$WORK/up5"; build_upstream "$U5" old
P5="$WORK/p5"; new_project "$P5"; run_setup "$P5" "$U5"
[ -f "$P5/.claude/hooks/tests/test_a.py" ] || fail "sc5: precondition — old install lacks tests"
printf '%s\n' "$MANIFEST_NEW" > "$U5/MANIFEST"
git -C "$U5" commit -qam "ship no tests"
RC=0; run_update "$P5" "$U5" || RC=$?
[ "$RC" -eq 0 ] && [ ! -e "$P5/.claude/hooks/tests" ] && pass "sc5: unedited tests removed by update" \
  || fail "sc5: tests remain (rc=$RC)"
[ -f "$P5/.claude/hooks/tests_helper.py" ] && pass "sc5: tests_helper.py untouched" || fail "sc5: tests_helper.py removed"
# An EDITED kit test is kept.
P5b="$WORK/p5b"; new_project "$P5b"
git -C "$U5" checkout -q HEAD~1 -- MANIFEST
git -C "$U5" commit -qam "old manifest again"
run_setup "$P5b" "$U5"
printf 'user edit\n' >> "$P5b/.claude/hooks/tests/test_a.py"
printf '%s\n' "$MANIFEST_NEW" > "$U5/MANIFEST"; git -C "$U5" commit -qam "new manifest again"
run_update "$P5b" "$U5" || true
grep -q 'user edit' "$P5b/.claude/hooks/tests/test_a.py" 2>/dev/null \
  && pass "sc5: edited kit test kept" || fail "sc5: edited kit test lost"

# ── SC7: install over a project's own .claude/hooks/tests — untouched, no .bak ─
U7="$WORK/up7"; build_upstream "$U7" new
P7="$WORK/p7"; new_project "$P7"
mkdir -p "$P7/.claude/hooks/tests"
printf 'my own test\n' > "$P7/.claude/hooks/tests/mine.py"
run_setup "$P7" "$U7" || { fail "sc7: setup failed"; cat "$WORK/setup.log" >&2; }
[ "$(cat "$P7/.claude/hooks/tests/mine.py" 2>/dev/null)" = "my own test" ] \
  && [ "$(ls "$P7/.claude/hooks/tests" | wc -l | tr -d ' ')" = "1" ] \
  && pass "sc7: project's own tests dir untouched" || fail "sc7: project's tests dir was changed"
[ ! -e "$P7/.claude/hooks/tests.bak" ] && [ ! -e "$P7/.claude/hooks.bak/tests" ] \
  && pass "sc7: no tests.bak, tests not swept into a hooks backup" || fail "sc7: tests was backed up"
[ -f "$P7/.claude/hooks/example_hook.py" ] && pass "sc7: kit hooks installed" || fail "sc7: kit hooks missing"

# ── SC8: a corrupt/partial upstream never becomes a mass delete ──────────────
U8="$WORK/up8"; build_upstream "$U8" new
P8="$WORK/p8"; new_project "$P8"; run_setup "$P8" "$U8"
git -C "$U8" rm -rq skills           # whole MANIFEST path vanishes upstream
git -C "$U8" commit -qm "half-fetched"
RC=0; run_update "$P8" "$U8" || RC=$?
{ [ -f "$P8/skills/optimize/SKILL.md" ] && [ -f "$P8/skills/keep/SKILL.md" ]; } \
  && pass "sc8: missing upstream path — nothing deleted" || fail "sc8: skills deleted from a partial upstream"
[ "$RC" -ne 0 ] && grep -qi 'error' "$WORK/update.log" \
  && pass "sc8: aborted deletion with an error (rc=$RC)" || fail "sc8: no error / rc=$RC"
lock_has "$P8/.claude/harness-lock.json" "skills/keep/SKILL.md" && pass "sc8: lock entries kept" || fail "sc8: lock entries dropped"

# ── SC9: a lock key with '..' never reaches rm ───────────────────────────────
U9="$WORK/up9"; build_upstream "$U9" new
P9="$WORK/p9"; new_project "$P9"; run_setup "$P9" "$U9"
printf 'victim\n' > "$P9/victim.txt"
H=$(sha256sum "$P9/victim.txt" 2>/dev/null | cut -d' ' -f1 || true)
[ -n "$H" ] || H=$(shasum -a 256 "$P9/victim.txt" | cut -d' ' -f1)
sed -i "s|\"files\": {|\"files\": {\n    \"skills/../victim.txt\": \"$H\",|" "$P9/.claude/harness-lock.json"
run_update "$P9" "$U9" || true
[ -f "$P9/victim.txt" ] && pass "sc9: '..' lock key did not delete outside the kit" || fail "sc9: victim.txt deleted via lock key"

# ── SC10: a MANIFEST line that is itself excluded is skipped BEFORE the backup ─
U10="$WORK/up10"; build_upstream "$U10" new
mkdir -p "$U10/templates/extra"; printf 'kit extra\n' > "$U10/templates/extra/x.md"
printf '%s\ntemplates/extra\n!templates/extra\n' "$MANIFEST_OLD" > "$U10/MANIFEST"
git -C "$U10" add -A; git -C "$U10" commit -q -m extra
P10="$WORK/p10"; new_project "$P10"
mkdir -p "$P10/templates/extra"; printf 'mine\n' > "$P10/templates/extra/mine.md"
run_setup "$P10" "$U10" || { fail "sc10: setup failed"; cat "$WORK/setup.log" >&2; }
{ [ "$(cat "$P10/templates/extra/mine.md" 2>/dev/null)" = "mine" ] && [ ! -e "$P10/templates/extra/x.md" ]; } \
  && pass "sc10: excluded MANIFEST path left exactly as the project had it" || fail "sc10: excluded path changed"
[ ! -e "$P10/templates/extra.bak" ] && pass "sc10: no .bak created for an excluded path" || fail "sc10: excluded path was backed up"

# ── SC6: every hook in an installed (real-kit) project runs without tests/ ───
U6="$WORK/up6"; mkdir -p "$U6"
while IFS= read -r _l; do
  _p=$(printf '%s' "$_l" | awk '$0 !~ /^[[:space:]]*(#|$|!)/ { print $1 }')
  [ -n "$_p" ] || continue
  mkdir -p "$U6/$(dirname "$_p")"; cp -R "$REPO_ROOT/$_p" "$U6/$_p"
done < "$REPO_ROOT/MANIFEST"
cp "$REPO_ROOT/MANIFEST" "$U6/MANIFEST"
mkdir -p "$U6/lib" "$U6/.claude"
cp "$REPO_ROOT/lib/"*.py "$U6/lib/"; cp "$REPO_ROOT/lib/harness-fetch.sh" "$U6/lib/" 2>/dev/null || true
cp "$REPO_ROOT/CLAUDE.md" "$REPO_ROOT/CLAUDE_LEGACY.md" "$U6/"
cp "$REPO_ROOT/.claude/settings.json" "$U6/.claude/settings.json"
git -C "$U6" init -q; git -C "$U6" config user.email t@e.x; git -C "$U6" config user.name T
git -C "$U6" add -A; git -C "$U6" commit -q -m real
P6="$WORK/p6"; new_project "$P6"; run_setup "$P6" "$U6" || { fail "sc6: setup failed"; cat "$WORK/setup.log" >&2; }
[ ! -e "$P6/.claude/hooks/tests" ] && pass "sc6: real kit installs without .claude/hooks/tests" || fail "sc6: real kit installed tests"
BAD=0; N=0
for h in "$P6"/.claude/hooks/*.py; do
  [ -f "$h" ] || continue
  N=$((N + 1))
  ( cd "$P6" && printf '{}' | python3 "$h" >/dev/null 2>&1 ); rc=$?
  if [ "$rc" -gt 1 ]; then BAD=$((BAD + 1)); printf '  hook %s exited %s\n' "$h" "$rc" >&2; fi
done
[ "$N" -gt 0 ] && [ "$BAD" -eq 0 ] && pass "sc6: $N hooks fed {} exit <= 1 without tests/" || fail "sc6: $BAD of $N hooks exited > 1"

printf '\n%s passed, %s failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
