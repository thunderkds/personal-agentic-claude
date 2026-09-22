#!/bin/sh
# tests/test_settings_merge.sh — .claude/settings.json hook merge (T111)
#
# Self-contained and offline (file:// repo URL, no network). Builds a throwaway
# local git "harness" fixture that ships kit hook entries, then drives the REAL
# setup.sh / update.sh against scratch target repos and asserts the merge rules:
#
#   SC1 existing settings with user permissions -> kit hooks added, permissions kept
#   SC2 a user hook entry (command NOT under .claude/hooks/) survives install+update
#   SC3 upstream adds a hook entry + file       -> update adds it
#   SC4 upstream removes a kit entry + file     -> update removes it, user entry kept
#   SC5 install/update run twice                -> byte-identical settings.json
#   SC6 invalid JSON                            -> untouched, loud stderr, exit 2
#   SC7 no python3 on PATH                      -> same as SC6
#   SC8 every merged command references a file that exists
#   M1  mutation control: a merge that skips adding entries must fail SC1
#
# Plus the Edge Case Checklist: symlink refusal, empty/null event lists,
# non-ASCII preservation, atomic write (no temp-file residue), and a command
# string that quotes "$CLAUDE_PROJECT_DIR" around the path.
#
# Run: bash tests/test_settings_merge.sh
set -u

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)
# No terminal for the installer's /dev/tty prompts, even from a dev shell (T114).
# shellcheck source=tests/lib/pty.sh
. "$SCRIPT_DIR/lib/pty.sh"
detach_from_terminal "$0" "$@"
SETUP="$REPO_ROOT/setup.sh"
UPDATE="$REPO_ROOT/update.sh"
MERGE="$REPO_ROOT/lib/merge-settings.py"

for f in "$SETUP" "$UPDATE" "$MERGE"; do
  if [ ! -f "$f" ]; then
    printf 'FATAL: required file not found at %s\n' "$f" >&2
    exit 2
  fi
done

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1" >&2; }

WORK=$(mktemp -d "${TMPDIR:-/tmp}/settings-merge-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT INT TERM HUP

NO_CLONE="$WORK/should-not-exist-supervisor"

# ── JSON assertion helper ────────────────────────────────────────────────────
# assert_json <label> <settings-file> <python expression over d / cmds>
#   d    = parsed settings dict
#   cmds = flat list of every hook command string in the file
assert_json() {
  _label="$1"; _file="$2"; _expr="$3"
  if python3 - "$_file" "$_expr" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
cmds = []
for _ev, _groups in (d.get("hooks") or {}).items():
    for _g in (_groups or []):
        for _h in (_g.get("hooks") or []):
            cmds.append(_h.get("command", ""))
sys.exit(0 if eval(sys.argv[2]) else 1)
PYEOF
  then
    pass "$_label"
  else
    fail "$_label"
    printf '      expr: %s\n      file: %s\n' "$_expr" "$_file" >&2
  fi
}

# assert_contains <label> <file> <literal string>
assert_contains() {
  if grep -qF -- "$3" "$2" 2>/dev/null; then pass "$1"; else fail "$1"; fi
}

# ── Fixture harness repo (the "upstream" both scripts fetch) ─────────────────
FIXTURE="$WORK/fixture-repo"

write_fixture_settings() {
  # $1 = extra kit entry ("yes" adds kit_three) ; $2 = "drop" removes kit_two
  cat > "$FIXTURE/.claude/settings.json" <<'EOF'
{
  "hooks": {
    "PreToolUse": [
      {
        "description": "kit one",
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/kit_one.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "description": "kit two",
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/kit_two.py"
          }
        ]
      }
    ]
  }
}
EOF
}

build_fixture() {
  mkdir -p "$FIXTURE/agents" \
           "$FIXTURE/skills/brainstorming" \
           "$FIXTURE/.claude/hooks" \
           "$FIXTURE/lib" \
           "$FIXTURE/templates"
  printf 'backend-agent-content\n'  > "$FIXTURE/agents/backend.md"
  printf 'skill-content\n'          > "$FIXTURE/skills/brainstorming/SKILL.md"
  printf 'template-content\n'       > "$FIXTURE/templates/PRD_template.md"
  printf 'kit-one\n'                > "$FIXTURE/.claude/hooks/kit_one.py"
  printf 'kit-two\n'                > "$FIXTURE/.claude/hooks/kit_two.py"
  printf 'GREENFIELD SUPERVISOR RULES\n' > "$FIXTURE/CLAUDE.md"
  printf 'BROWNFIELD SUPERVISOR RULES\n' > "$FIXTURE/CLAUDE_LEGACY.md"
  cp "$MERGE" "$FIXTURE/lib/merge-settings.py"
  write_fixture_settings
  cat > "$FIXTURE/MANIFEST" <<'EOF'
# fixture MANIFEST
agents
skills
.claude/hooks
templates
EOF
  git -C "$FIXTURE" init -q
  git -C "$FIXTURE" config user.email "test@example.com"
  git -C "$FIXTURE" config user.name "Test"
  git -C "$FIXTURE" add -A
  git -C "$FIXTURE" commit -q -m "fixture harness"
}

commit_fixture() {
  git -C "$FIXTURE" add -A
  git -C "$FIXTURE" commit -q -m "$1"
}

build_fixture

# ── Target-repo helpers ──────────────────────────────────────────────────────
new_target() {
  _t="$WORK/$1"
  mkdir -p "$_t/.claude"
  git -C "$_t" init -q
  git -C "$_t" config user.email "test@example.com"
  git -C "$_t" config user.name "Test"
  printf '%s' "$_t"
}

run_setup() {
  ( cd "$1" \
      && SUPERVISOR_REPO="file://$FIXTURE" SUPERVISOR_PATH="$NO_CLONE" \
         bash "$SETUP" </dev/null >"$WORK/setup.log" 2>&1 )
}

run_update() {
  ( cd "$1" \
      && SUPERVISOR_REPO="file://$FIXTURE" \
         bash "$UPDATE" </dev/null >"$WORK/update.log" 2>&1 )
}


# A project settings.json with user permissions, a user hook entry, an empty
# event list, a null event list and non-ASCII content.
write_project_settings() {
  cat > "$1/.claude/settings.json" <<'EOF'
{
  "permissions": {
    "allow": ["Bash(ls:*)"],
    "note": "ünïcodé — keep me"
  },
  "hooks": {
    "PreToolUse": [
      {
        "description": "my own guard",
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "echo mine" }
        ]
      }
    ],
    "SessionStart": [],
    "Notification": null
  }
}
EOF
}

# ─────────────────────────────────────────────────────────────────────────────
# SC1 / SC2 / SC8 — install into a project that already has settings.json
# ─────────────────────────────────────────────────────────────────────────────
T1=$(new_target target-install)
write_project_settings "$T1"
# Seed a group-readable mode so the merge's mode preservation is observable:
# mkstemp creates 0600 and os.replace carries the temp file's mode onto the
# destination, so an unguarded atomic write silently tightens 0644 -> 0600.
chmod 644 "$T1/.claude/settings.json"
if run_setup "$T1"; then
  pass "SC1: setup.sh exits 0 over an existing settings.json"
else
  fail "SC1: setup.sh exited non-zero"
  cat "$WORK/setup.log" >&2
fi
S1="$T1/.claude/settings.json"

assert_json "SC1: user permissions.allow preserved" "$S1" \
  'd["permissions"]["allow"] == ["Bash(ls:*)"]'
assert_json "SC1: kit_one.py wired" "$S1" \
  'any("kit_one.py" in c for c in cmds)'
assert_json "SC1: kit_two.py wired" "$S1" \
  'any("kit_two.py" in c for c in cmds)'
assert_json "SC2: user hook entry survives install" "$S1" \
  '"echo mine" in cmds'
assert_json "edge: non-ASCII preserved unescaped" "$S1" \
  'd["permissions"]["note"] == "ünïcodé — keep me"'
assert_contains "edge: non-ASCII written as UTF-8, not \\u escapes" "$S1" 'ünïcodé'
assert_json "edge: empty/null event lists do not crash the merge" "$S1" \
  'd["hooks"].get("SessionStart") in (None, []) and d["hooks"].get("Notification") in (None, [])'
assert_json "edge: quoted \$CLAUDE_PROJECT_DIR command matched by path" "$S1" \
  'any(c.startswith("python3 \"$CLAUDE_PROJECT_DIR\"") and "kit_one.py" in c for c in cmds)'

# SC8 — every kit command points at a file that exists in the project
if python3 - "$S1" "$T1" <<'PYEOF'
import json, re, sys, os
d = json.load(open(sys.argv[1], encoding="utf-8"))
root = sys.argv[2]
bad = []
for ev, groups in (d.get("hooks") or {}).items():
    for g in (groups or []):
        for h in (g.get("hooks") or []):
            m = re.search(r"\.claude/hooks/[^\s\"']+", h.get("command", ""))
            if m and not os.path.exists(os.path.join(root, m.group(0))):
                bad.append(m.group(0))
sys.exit(1 if bad else 0)
PYEOF
then
  pass "SC8: every kit command references an existing hook file (fresh install)"
else
  fail "SC8: a kit command references a missing hook file (fresh install)"
fi

# SC5 (install half) — a second install is byte-identical
cp "$S1" "$WORK/after-install-1.json"
run_setup "$T1" || true
if cmp -s "$WORK/after-install-1.json" "$S1"; then
  pass "SC5: second install leaves settings.json byte-identical"
else
  fail "SC5: second install churned settings.json"
  diff -u "$WORK/after-install-1.json" "$S1" >&2 || true
fi

# edge: no temp-file residue from the atomic write
if [ -z "$(find "$T1/.claude" -maxdepth 1 -name '.settings.json.*' -o -maxdepth 1 -name 'settings.json.tmp*' 2>/dev/null)" ]; then
  pass "edge: atomic write leaves no temp-file residue"
else
  fail "edge: atomic write left a temp file behind"
fi

# edge: the atomic write preserves the file's existing permission bits.
# git tracks only the exec bit, so a regression here would never show in a diff.
_mode_after=$(stat -c '%a' "$S1" 2>/dev/null || stat -f '%Lp' "$S1")
if [ "$_mode_after" = "644" ]; then
  pass "edge: atomic write preserves the file's permission bits (644)"
else
  fail "edge: atomic write changed the file mode 644 -> $_mode_after"
fi

# ─────────────────────────────────────────────────────────────────────────────
# SC3 — upstream ADDS a hook entry + file; update delivers it
# ─────────────────────────────────────────────────────────────────────────────
printf 'kit-three\n' > "$FIXTURE/.claude/hooks/kit_three.py"
python3 - "$FIXTURE/.claude/settings.json" <<'PYEOF'
import json, sys
p = sys.argv[1]
d = json.load(open(p, encoding="utf-8"))
d["hooks"].setdefault("Stop", []).append({
    "description": "kit three",
    "hooks": [{"type": "command",
               "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/kit_three.py"}],
})
json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
open(p, "a", encoding="utf-8").write("\n")
PYEOF
commit_fixture "upstream adds kit_three"

if run_update "$T1"; then
  pass "SC3: update.sh exits 0"
else
  fail "SC3: update.sh exited non-zero"
  cat "$WORK/update.log" >&2
fi
assert_json "SC3: upstream-added entry present after update" "$S1" \
  'any("kit_three.py" in c for c in cmds)'
assert_json "SC2: user hook entry survives update" "$S1" \
  '"echo mine" in cmds'
assert_json "SC3: user permissions still untouched after update" "$S1" \
  'd["permissions"]["allow"] == ["Bash(ls:*)"]'

# SC5 (update half) — a second update is byte-identical
cp "$S1" "$WORK/after-update-1.json"
run_update "$T1" || true
if cmp -s "$WORK/after-update-1.json" "$S1"; then
  pass "SC5: second update leaves settings.json byte-identical"
else
  fail "SC5: second update churned settings.json"
  diff -u "$WORK/after-update-1.json" "$S1" >&2 || true
fi

# ─────────────────────────────────────────────────────────────────────────────
# SC4 — upstream REMOVES a kit entry + file; update removes it, user entry kept
# ─────────────────────────────────────────────────────────────────────────────
rm -f "$FIXTURE/.claude/hooks/kit_two.py"
python3 - "$FIXTURE/.claude/settings.json" <<'PYEOF'
import json, sys
p = sys.argv[1]
d = json.load(open(p, encoding="utf-8"))
d["hooks"].pop("PostToolUse", None)
json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
open(p, "a", encoding="utf-8").write("\n")
PYEOF
commit_fixture "upstream removes kit_two"

run_update "$T1" || { fail "SC4: update.sh exited non-zero"; cat "$WORK/update.log" >&2; }
assert_json "SC4: upstream-removed kit entry is gone" "$S1" \
  'not any("kit_two.py" in c for c in cmds)'
assert_json "SC4: user entry still present after a kit removal" "$S1" \
  '"echo mine" in cmds'
assert_json "SC4: surviving kit entries still wired" "$S1" \
  'any("kit_one.py" in c for c in cmds) and any("kit_three.py" in c for c in cmds)'

if python3 - "$S1" "$T1" <<'PYEOF'
import json, re, sys, os
d = json.load(open(sys.argv[1], encoding="utf-8"))
root = sys.argv[2]
bad = []
for ev, groups in (d.get("hooks") or {}).items():
    for g in (groups or []):
        for h in (g.get("hooks") or []):
            m = re.search(r"\.claude/hooks/[^\s\"']+", h.get("command", ""))
            if m and not os.path.exists(os.path.join(root, m.group(0))):
                bad.append(m.group(0))
sys.exit(1 if bad else 0)
PYEOF
then
  pass "SC8: no command points at a missing hook file after an upstream removal"
else
  fail "SC8: a command points at a missing hook file after an upstream removal"
fi

# ─────────────────────────────────────────────────────────────────────────────
# SC6 — invalid JSON: file untouched, loud stderr, exit 2
# ─────────────────────────────────────────────────────────────────────────────
T2=$(new_target target-badjson)
printf '{not json\n' > "$T2/.claude/settings.json"
cp "$T2/.claude/settings.json" "$WORK/badjson-before"
set +e
( cd "$T2" && SUPERVISOR_REPO="file://$FIXTURE" SUPERVISOR_PATH="$NO_CLONE" \
    bash "$SETUP" </dev/null >"$WORK/badjson.out" 2>"$WORK/badjson.err" )
rc=$?
set -e

[ "$rc" -eq 2 ] && pass "SC6: install exits 2 on invalid settings.json" \
                || fail "SC6: expected exit 2, got $rc"
cmp -s "$WORK/badjson-before" "$T2/.claude/settings.json" \
  && pass "SC6: invalid settings.json left byte-identical" \
  || fail "SC6: invalid settings.json was modified"
assert_contains "SC6: stderr names the file" "$WORK/badjson.err" 'settings.json'
assert_contains "SC6: stderr prints a \"hooks\" block" "$WORK/badjson.err" '"hooks"'
assert_contains "SC6: stderr prints the kit entries to add" "$WORK/badjson.err" 'kit_one.py'
# the rest of the run still finished
[ -f "$T2/.claude/harness-lock.json" ] \
  && pass "SC6: the run still completed its other work (lock written)" \
  || fail "SC6: the run aborted early — no harness-lock.json"

# ─────────────────────────────────────────────────────────────────────────────
# SC7 — python3 absent from PATH: same contract as SC6
# ─────────────────────────────────────────────────────────────────────────────
NOPY="$WORK/nopy-bin"
mkdir -p "$NOPY"
for d in /usr/bin /bin /usr/local/bin; do
  [ -d "$d" ] || continue
  for f in "$d"/*; do
    [ -x "$f" ] || continue
    b=$(basename "$f")
    case "$b" in python*) continue ;; esac
    [ -e "$NOPY/$b" ] || ln -s "$f" "$NOPY/$b" 2>/dev/null || true
  done
done
if [ -n "$(PATH="$NOPY" command -v python3 2>/dev/null)" ]; then
  fail "SC7: could not build a python3-free PATH (skipping is not a pass)"
else
  T3=$(new_target target-nopython)
  write_project_settings "$T3"
  cp "$T3/.claude/settings.json" "$WORK/nopy-before"
  set +e
  ( cd "$T3" && PATH="$NOPY" SUPERVISOR_REPO="file://$FIXTURE" SUPERVISOR_PATH="$NO_CLONE" \
      bash "$SETUP" </dev/null >"$WORK/nopy.out" 2>"$WORK/nopy.err" )
  rc=$?
  set -e
  [ "$rc" -eq 2 ] && pass "SC7: install exits 2 when python3 is absent" \
                  || fail "SC7: expected exit 2, got $rc"
  cmp -s "$WORK/nopy-before" "$T3/.claude/settings.json" \
    && pass "SC7: settings.json left byte-identical when python3 is absent" \
    || fail "SC7: settings.json was modified without python3"
  assert_contains "SC7: stderr names the file" "$WORK/nopy.err" 'settings.json'
  assert_contains "SC7: stderr prints a \"hooks\" block" "$WORK/nopy.err" '"hooks"'
  assert_contains "SC7: stderr names python3 as the cause" "$WORK/nopy.err" 'python3'
fi

# ─────────────────────────────────────────────────────────────────────────────
# Edge: settings.json is a symlink -> refuse like invalid JSON, never write through
# ─────────────────────────────────────────────────────────────────────────────
T4=$(new_target target-symlink)
REAL="$WORK/real-settings.json"
printf '{"permissions":{"allow":["Bash(ls:*)"]}}\n' > "$REAL"
ln -s "$REAL" "$T4/.claude/settings.json"
cp "$REAL" "$WORK/symlink-before"
set +e
( cd "$T4" && SUPERVISOR_REPO="file://$FIXTURE" SUPERVISOR_PATH="$NO_CLONE" \
    bash "$SETUP" </dev/null >"$WORK/symlink.out" 2>"$WORK/symlink.err" )
rc=$?
set -e
[ "$rc" -eq 2 ] && pass "edge: install exits 2 on a settings.json symlink" \
                || fail "edge: expected exit 2 on symlink, got $rc"
[ -L "$T4/.claude/settings.json" ] \
  && pass "edge: the symlink itself was not replaced" \
  || fail "edge: the symlink was replaced by a regular file"
cmp -s "$WORK/symlink-before" "$REAL" \
  && pass "edge: the symlink target was never written through" \
  || fail "edge: the merge wrote through the symlink"

# ─────────────────────────────────────────────────────────────────────────────
# AC1 regression — no settings.json at all: install writes the kit file
# ─────────────────────────────────────────────────────────────────────────────
T5=$(new_target target-fresh)
run_setup "$T5" || { fail "AC1: setup.sh exited non-zero on a fresh project"; cat "$WORK/setup.log" >&2; }
if [ -f "$T5/.claude/settings.json" ] && [ ! -L "$T5/.claude/settings.json" ]; then
  pass "AC1: fresh install writes .claude/settings.json as a real file"
else
  fail "AC1: fresh install did not write .claude/settings.json"
fi
assert_json "AC1: fresh install wires every kit hook" "$T5/.claude/settings.json" \
  'any("kit_one.py" in c for c in cmds) and any("kit_three.py" in c for c in cmds)'

# ─────────────────────────────────────────────────────────────────────────────
# Edge: a user-copied kit entry with a changed matcher is replaced by upstream's
# ─────────────────────────────────────────────────────────────────────────────
T6=$(new_target target-matcher)
cat > "$T6/.claude/settings.json" <<'EOF'
{
  "hooks": {
    "PreToolUse": [
      {
        "description": "kit one, matcher edited by the user",
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/kit_one.py"
          }
        ]
      }
    ]
  }
}
EOF
run_setup "$T6" || { fail "edge: setup.sh exited non-zero (matcher case)"; cat "$WORK/setup.log" >&2; }
assert_json "edge: an edited kit matcher is restored to upstream's value" \
  "$T6/.claude/settings.json" \
  'all(g.get("matcher") == "Bash" for g in d["hooks"]["PreToolUse"] if any("kit_one.py" in h.get("command","") for h in g.get("hooks") or []))'

# ─────────────────────────────────────────────────────────────────────────────
# M1 — mutation control: a merge that never ADDS a kit entry must fail SC1
# ─────────────────────────────────────────────────────────────────────────────
cp "$FIXTURE/lib/merge-settings.py" "$WORK/merge-settings.orig.py"
python3 - "$FIXTURE/lib/merge-settings.py" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
marker = "MUTATION POINT M1"
if marker not in s:
    sys.stderr.write("M1: mutation marker %r not found in merge-settings.py\n" % marker)
    sys.exit(3)
# Neutralise the add-missing-kit-entries step.
s = s.replace("return merged_groups", "return [g for g in project_groups if not is_kit_group(g)]", 1)
open(p, "w", encoding="utf-8").write(s)
PYEOF
mut_rc=$?
if [ "$mut_rc" -ne 0 ]; then
  fail "M1: could not apply the mutation (rc=$mut_rc)"
else
  commit_fixture "M1 mutation"
  T7=$(new_target target-mutant)
  write_project_settings "$T7"
  run_setup "$T7" >/dev/null 2>&1 || true
  if python3 - "$T7/.claude/settings.json" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
cmds = [h.get("command", "")
        for groups in (d.get("hooks") or {}).values()
        for g in (groups or [])
        for h in (g.get("hooks") or [])]
sys.exit(0 if any("kit_one.py" in c for c in cmds) else 1)
PYEOF
  then
    fail "M1: mutant still wired kit_one.py — SC1 is vacuous"
  else
    pass "M1: mutant (skip adding entries) fails the SC1 assertion, as required"
  fi
  cp "$WORK/merge-settings.orig.py" "$FIXTURE/lib/merge-settings.py"
  commit_fixture "M1 revert"
fi

# ─────────────────────────────────────────────────────────────────────────────
printf '\n--- %d passed, %d failed ---\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ] || exit 1
