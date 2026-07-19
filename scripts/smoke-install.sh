#!/bin/sh
# smoke-install.sh — end-to-end install smoke test for setup.sh (T036).
#
# Direct-to-repo model (ADR-0001): setup.sh no longer reads from a persistent
# SUPERVISOR_PATH central clone — it always fetches fresh via `git clone` (see
# lib/harness-fetch.sh), sourced relative to setup.sh's own location. This test
# points SUPERVISOR_REPO at the current checkout via a `file://` URL — the same
# offline, no-network pattern already proven in tests/test_setup.sh,
# tests/test_update.sh, and tests/test_install_update_smoke.sh — so setup.sh
# clones the REAL current repo state (not a synthetic fixture) into a scratch
# target directory, then asserts every expected artifact landed.
#
# setup.sh is invoked by its real path inside $ROOT (never copied elsewhere)
# so it can always find its co-located lib/harness-fetch.sh.
#
# Usage: sh scripts/smoke-install.sh   (run from repo root, must be a git repo)

set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SETUP="$ROOT/setup.sh"

if [ ! -f "$SETUP" ]; then
  printf 'smoke-install: ERROR — setup.sh not found at %s\n' "$SETUP" >&2
  exit 1
fi

# setup.sh's fetch step clones via git — the source must itself be a git repo.
if ! git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  printf 'smoke-install: ERROR — %s is not a git repo (setup.sh needs one to clone from)\n' "$ROOT"
  exit 1
fi

TARGET="$(mktemp -d)"
# shellcheck disable=SC2317  # cleanup is invoked indirectly via the EXIT trap
cleanup() { rm -rf "$TARGET"; }
trap cleanup EXIT

# setup.sh's own git-repo prerequisite check applies to the TARGET (its own
# undo mechanism under the direct-install model), separately from the source
# repo check above.
git -C "$TARGET" init -q
git -C "$TARGET" config user.email "smoke-test@example.com"
git -C "$TARGET" config user.name "smoke-test"

# Sentinel path: nothing in setup.sh's core install should ever write here.
# Pointing SUPERVISOR_PATH at it makes the "no central-clone created" assertion
# below meaningful — without setting this, that check would trivially pass no
# matter what setup.sh actually does (mirrors tests/test_setup.sh's NO_CLONE).
NO_CLONE="$TARGET/should-not-exist-supervisor"

printf '== Running setup.sh (non-interactive, offline file:// fetch) ==\n'
# stdin from /dev/null => non-interactive => greenfield (CLAUDE.md) default, no packs.
# SUPERVISOR_REPO=file://$ROOT: setup.sh clones the REAL current checkout, not a
# stale/synthetic fixture — the truest possible smoke test of "does install work."
( cd "$TARGET" && SUPERVISOR_REPO="file://$ROOT" SUPERVISOR_PATH="$NO_CLONE" sh "$SETUP" </dev/null )

FAIL=0
assert_exists() {
  if [ -e "$TARGET/$1" ]; then printf '  [ok]   %s\n' "$1"
  else printf '  [FAIL] missing after install: %s\n' "$1"; FAIL=1; fi
}

printf '\n== Asserting installed artifacts ==\n'
assert_exists CLAUDE.md
assert_exists .claude/agents
assert_exists .claude/skills
assert_exists .claude/hooks
assert_exists templates
assert_exists .claude/settings.json
assert_exists memory/MEMORY.md
assert_exists memory/decisions.md
assert_exists memory/glossary.md
assert_exists memory/learnings.md
assert_exists tasks
assert_exists .claude/harness-lock.json

# Greenfield default must install the greenfield CLAUDE.md (not legacy).
if grep -q "Project Supervisor" "$TARGET/CLAUDE.md" 2>/dev/null; then
  printf '  [ok]   CLAUDE.md is the supervisor ruleset\n'
else
  printf '  [FAIL] CLAUDE.md content unexpected\n'; FAIL=1
fi

# Direct-to-repo model always copies real files — never symlinks.
if [ -L "$TARGET/CLAUDE.md" ]; then
  printf '  [FAIL] CLAUDE.md is a symlink (should be a real file under the direct-install model)\n'; FAIL=1
else
  printf '  [ok]   setup.sh produced a real CLAUDE.md, not a symlink\n'
fi

# No persistent central clone should be created or required by the core install.
if [ -e "$NO_CLONE" ]; then
  printf '  [FAIL] a stray central-clone-like path was created\n'; FAIL=1
else
  printf '  [ok]   no central-clone directory created by the core install\n'
fi

printf '\n'
if [ "$FAIL" -eq 0 ]; then printf 'smoke-install.sh: PASS\n'; else printf 'smoke-install.sh: FAIL\n'; fi
exit "$FAIL"
