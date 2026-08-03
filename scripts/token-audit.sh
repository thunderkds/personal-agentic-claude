#!/bin/sh
# token-audit.sh — regenerate the Token Audit Log from memory/event-trace/*.jsonl (T040).
#
# Generator, not a hook: run on demand (e.g. at session end alongside pasting
# `/cost`), never wired into a PreToolUse/PostToolUse matcher. See
# scripts/token_audit.py for the actual derivation logic and
# docs/ddr/0001-measure-first-token-refactor.md (Amendment 1) for why this
# replaced the manual per-session logging convention.
#
# No shellcheck available in this environment (memory/learnings.md) —
# substituted with `sh -n` plus a real run of this script.
#
# Usage: sh scripts/token-audit.sh

set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  printf 'token-audit: ERROR — python3 not found on PATH\n' >&2
  exit 1
fi

exec python3 "$ROOT/scripts/token_audit.py"
