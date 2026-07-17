#!/bin/sh
# tests/test_harness_fetch.sh — POSIX-sh test harness for lib/harness-fetch.sh (T031)
#
# Self-contained: builds a throwaway local git fixture repo, fetches it via a
# file:// URL (no network), and asserts on file presence, real-copy semantics,
# temp-dir cleanup, loud failure on a bad URL, and cleanup-on-interrupt (SIGINT).
#
# Trap-dependent assertions run the scenario in a real child shell process (via
# driver scripts) rather than a $(...) command-substitution subshell, so the
# library's EXIT trap fires deterministically on process exit.
#
# Run: bash tests/test_harness_fetch.sh   (or: sh tests/test_harness_fetch.sh)
set -u

# ── Locate the library under test (relative to this script) ──────────────────
SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)
LIB="$REPO_ROOT/lib/harness-fetch.sh"

if [ ! -f "$LIB" ]; then
  printf 'FATAL: library not found at %s\n' "$LIB" >&2
  exit 2
fi

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1" >&2; }

# ── Test workspace (cleaned on exit) ─────────────────────────────────────────
WORK=$(mktemp -d "${TMPDIR:-/tmp}/harness-fetch-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT INT TERM HUP

FIXTURE="$WORK/fixture-repo"
mkdir -p "$FIXTURE"

# ── Build a minimal fixture harness repo ─────────────────────────────────────
mkdir -p "$FIXTURE/.claude/agents" "$FIXTURE/templates"
printf 'agent-content\n'    > "$FIXTURE/.claude/agents/foo.md"
printf 'template-content\n' > "$FIXTURE/templates/bar.md"
cat > "$FIXTURE/MANIFEST" <<'EOF'
# fixture MANIFEST
.claude/agents
templates
# entry intentionally absent from the clone (must warn + skip, not abort)
does/not/exist
EOF

git -C "$FIXTURE" init -q
git -C "$FIXTURE" config user.email "test@example.com"
git -C "$FIXTURE" config user.name "Test"
git -C "$FIXTURE" add -A
git -C "$FIXTURE" commit -q -m "fixture"

export LIB

# =============================================================================
# Test 1 — successful fetch + copy; real copy (not symlink); temp dir removed
# =============================================================================
TARGET1="$WORK/target1"; mkdir -p "$TARGET1"
PATHFILE1="$WORK/tmp_path_1"

cat > "$WORK/driver1.sh" <<'DRIVER'
. "$LIB"
harness_make_temp_dir
printf '%s' "$HARNESS_TEMP_DIR" > "$PATHFILE1"
harness_fetch "$REPO_URL" "$HARNESS_TEMP_DIR"
harness_copy_manifest "$HARNESS_TEMP_DIR" "$TARGET1" "$HARNESS_TEMP_DIR/MANIFEST"
DRIVER

REPO_URL="file://$FIXTURE" TARGET1="$TARGET1" PATHFILE1="$PATHFILE1" \
  sh "$WORK/driver1.sh" >/dev/null 2>&1 \
  && pass "test1: fetch/copy pipeline exited 0" \
  || fail "test1: fetch/copy pipeline returned non-zero"

if [ -f "$TARGET1/.claude/agents/foo.md" ] && [ -f "$TARGET1/templates/bar.md" ]; then
  pass "test1: MANIFEST paths copied into target"
else
  fail "test1: expected copied files missing in target"
fi

if [ ! -L "$TARGET1/.claude/agents" ] && [ ! -L "$TARGET1/.claude/agents/foo.md" ]; then
  pass "test1: copied entries are real files, not symlinks"
else
  fail "test1: copied entry is a symlink (expected real copy)"
fi

# Absent MANIFEST entry ('does/not/exist') must be skipped, not created.
if [ ! -e "$TARGET1/does/not/exist" ]; then
  pass "test1: absent MANIFEST entry skipped (warn, not abort)"
else
  fail "test1: absent MANIFEST entry was created"
fi

T1_TMP=$(cat "$PATHFILE1" 2>/dev/null || true)
if [ -n "$T1_TMP" ] && [ ! -d "$T1_TMP" ]; then
  pass "test1: temp clone dir removed after process exit ($T1_TMP)"
else
  fail "test1: temp clone dir still present ($T1_TMP)"
fi

# =============================================================================
# Test 2 — unreachable/invalid repo URL: non-zero, error, target untouched
# =============================================================================
TARGET2="$WORK/target2"; mkdir -p "$TARGET2"
BAD_URL="file://$WORK/does-not-exist-repo"

cat > "$WORK/driver2.sh" <<'DRIVER'
. "$LIB"
harness_make_temp_dir
harness_fetch "$BAD_URL" "$HARNESS_TEMP_DIR"
DRIVER

T2_RC=0
T2_ERR=$(BAD_URL="$BAD_URL" sh "$WORK/driver2.sh" 2>&1) || T2_RC=$?

if [ "$T2_RC" -ne 0 ]; then
  pass "test2: harness_fetch on bad URL exits non-zero (rc=$T2_RC)"
else
  fail "test2: harness_fetch on bad URL unexpectedly succeeded"
fi

if printf '%s' "$T2_ERR" | grep -q '\[error\]'; then
  pass "test2: harness_fetch printed a clear error message"
else
  fail "test2: no error message emitted on failed clone"
fi

if [ -z "$(ls -A "$TARGET2" 2>/dev/null)" ]; then
  pass "test2: target left untouched on clone failure (no partial copy)"
else
  fail "test2: target was modified despite clone failure"
fi

# =============================================================================
# Test 3 — cleanup-on-interrupt: SIGINT to a registered-temp-dir process
# =============================================================================
PATHFILE3="$WORK/tmp_path_3"
rm -f "$PATHFILE3"

cat > "$WORK/driver3.sh" <<'DRIVER'
. "$LIB"
harness_make_temp_dir
printf '%s' "$HARNESS_TEMP_DIR" > "$PATHFILE3"
sleep 10
DRIVER

PATHFILE3="$PATHFILE3" sh "$WORK/driver3.sh" &
CHILD=$!

i=0
while [ ! -s "$PATHFILE3" ] && [ "$i" -lt 100 ]; do
  sleep 0.1
  i=$((i + 1))
done

if [ -s "$PATHFILE3" ]; then
  T3_TMP=$(cat "$PATHFILE3")
  if [ -d "$T3_TMP" ]; then
    kill -INT "$CHILD" 2>/dev/null
    wait "$CHILD" 2>/dev/null
    if [ ! -d "$T3_TMP" ]; then
      pass "test3: temp dir removed after SIGINT ($T3_TMP)"
    else
      fail "test3: temp dir persisted after SIGINT ($T3_TMP)"
    fi
  else
    fail "test3: temp dir was not created ($T3_TMP)"
  fi
else
  kill "$CHILD" 2>/dev/null
  wait "$CHILD" 2>/dev/null
  fail "test3: background process never published its temp path"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
printf '\n----- summary: %d passed, %d failed -----\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
