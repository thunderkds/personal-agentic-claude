#!/bin/sh
# smoke-install.sh — end-to-end install smoke test for setup.sh.
#
# Treats the current checkout as the central clone (SUPERVISOR_PATH) and runs
# setup.sh --copy non-interactively into a throwaway target project, then
# asserts every expected artifact landed. Catches installer regressions before
# a user hits them.
#
# Usage: sh scripts/smoke-install.sh   (run from repo root, must be a git repo)

set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# setup.sh requires the central clone to be a git repo (rev-parse check).
if ! git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  printf 'smoke-install: ERROR — %s is not a git repo (setup.sh needs one)\n' "$ROOT"
  exit 1
fi

TARGET="$(mktemp -d)"
# shellcheck disable=SC2317  # cleanup is invoked indirectly via the EXIT trap
cleanup() { rm -rf "$TARGET"; }
trap cleanup EXIT

# setup.sh aborts if invoked from *inside* the central clone, so copy it into
# the target dir and run it there. SUPERVISOR_PATH points back at the checkout.
cp "$ROOT/setup.sh" "$TARGET/setup.sh"

printf '== Running setup.sh --copy (non-interactive) ==\n'
# stdin from /dev/null => non-interactive => greenfield (CLAUDE.md) default.
( cd "$TARGET" && SUPERVISOR_PATH="$ROOT" sh setup.sh --copy </dev/null )

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

# Greenfield default must install the greenfield CLAUDE.md (not legacy).
if grep -q "Project Supervisor" "$TARGET/CLAUDE.md" 2>/dev/null; then
  printf '  [ok]   CLAUDE.md is the supervisor ruleset\n'
else
  printf '  [FAIL] CLAUDE.md content unexpected\n'; FAIL=1
fi

# --copy mode => real files, not symlinks.
if [ -L "$TARGET/CLAUDE.md" ]; then
  printf '  [FAIL] CLAUDE.md is a symlink under --copy\n'; FAIL=1
else
  printf '  [ok]   --copy produced a real CLAUDE.md\n'
fi

printf '\n'
if [ "$FAIL" -eq 0 ]; then printf 'smoke-install.sh: PASS\n'; else printf 'smoke-install.sh: FAIL\n'; fi
exit "$FAIL"
