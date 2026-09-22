#!/bin/sh
# Local mirror of CI's "Shellcheck install scripts" step (.github/workflows/ci.yml).
# Resolves shellcheck from PATH, honoring a SHELLCHECK override for environments
# where it isn't installed under its usual name. Fails loudly — never silently
# skips-as-pass — when no shellcheck binary can be found.
set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

SHELLCHECK="${SHELLCHECK:-shellcheck}"

if ! command -v "$SHELLCHECK" >/dev/null 2>&1; then
  echo "test_shellcheck_clean: FAIL — cannot verify: no shellcheck binary found" \
       "(looked for '\$SHELLCHECK' env override, then 'shellcheck' on PATH)." >&2
  echo "Set SHELLCHECK=/path/to/shellcheck to point at a binary, then re-run." >&2
  exit 1
fi

# Same six files, same order, as .github/workflows/ci.yml's shellcheck step.
if OUTPUT=$("$SHELLCHECK" -x setup.sh update.sh lib/harness-update.sh scripts/validate.sh \
  scripts/smoke-install.sh tests/test_harness_projection.sh 2>&1); then
  STATUS=0
else
  STATUS=$?
fi

if [ "$STATUS" -eq 0 ] && [ -z "$OUTPUT" ]; then
  echo "test_shellcheck_clean: PASS — exit 0, no output"
  exit 0
fi

echo "test_shellcheck_clean: FAIL — shellcheck exited $STATUS" >&2
echo "$OUTPUT" >&2
exit 1
