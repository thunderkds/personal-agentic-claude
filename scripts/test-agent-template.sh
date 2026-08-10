#!/bin/sh
# test-agent-template.sh — content assertions + negative controls for
# .claude/agents/general-agent-template.md (T041).
#
# Validates (AC numbers from tasks/TASK_GUIDE_T041.md):
#   AC1 — all four Karpathy principle names + a one-line operational command each, inline in
#         each of the four ROLE GUIDES (repointed from $TEMPLATE by T069 — same strings, same
#         `grep -qF`, new location)
#   AC1b— negative (T069): the template carries neither the heading nor any of those commands
#   AC2 — `## Search Before You Build` section with exactly 7 numbered rungs (1-7)
#   AC3 — non-negotiables block (correctness/validation/error handling/security/explicit
#         requirements never traded for a shorter diff)
#   AC4 — line 22's bare principles reference now resolves within the same file (implied
#         by AC1: the content exists in this file, not just CLAUDE.md)
#   AC5 — negative: CLAUDE.md is NOT added to the Mandatory Startup Sequence read list
#   AC6 — negative: the string "ponytail" appears nowhere in .claude/agents/**
#   AC7 — negative: file grows by <=45 lines (87 -> <=132)
#   AC8 — negative: backend.md / frontend.md / qa.md / common-infrastructure.md are
#         byte-identical to HEAD (checksum, not visual inspection)
#
# No shellcheck in this environment (memory/learnings.md) — substituted with `sh -n`
# plus a real run of this script.
#
# Usage: sh scripts/test-agent-template.sh

set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE="$ROOT/.claude/agents/general-agent-template.md"
ROLE_GUIDES=".claude/agents/common-infrastructure.md .claude/agents/backend.md .claude/agents/frontend.md .claude/agents/qa.md"
BASELINE_LINES=87
BUDGET_LINES=132
FAIL=0

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  FAIL=1
}

pass() {
  printf 'PASS: %s\n' "$1"
}

if [ ! -f "$TEMPLATE" ]; then
  printf 'test-agent-template: ERROR — %s not found\n' "$TEMPLATE" >&2
  exit 1
fi

# Anti-vacuity: AC1 now greps four OTHER files. A mistyped path would make every one of its
# `grep -qF` checks fail loudly rather than silently — but a *missing* file must be an error,
# not a finding, so the failure is unambiguous.
for path in $ROLE_GUIDES; do
  if [ ! -f "$ROOT/$path" ]; then
    printf 'test-agent-template: ERROR — %s not found (AC1 would inspect nothing)\n' "$path" >&2
    exit 1
  fi
done

# --- AC1: all four Karpathy principle names + operational command, inline ----------
# T069 REPOINTED, not loosened. T041 asserted these strings against $TEMPLATE; T069 moved the
# table into the four role guides, because the harness auto-loads a role guide as the agent's
# system prompt while the template arrives only if the agent opens it. The pinned strings below
# are byte-identical to what T041 pinned and the `grep -qF` is unchanged — only the file each
# one is checked against changed, plus the new negative that the old location is really vacated.
for path in $ROLE_GUIDES; do
  for principle in "Think Before Coding" "Simplicity First" "Surgical Changes" "Goal-Driven Execution"; do
    if grep -qF "$principle" "$ROOT/$path"; then
      pass "AC1: principle name present in $path: $principle"
    else
      fail "AC1: principle name missing from $path: $principle"
    fi
  done

  for cmd in "Ask vs. Guess" "Prohibit speculation" "Scope locking" "Convert all imperative instructions"; do
    if grep -qF "$cmd" "$ROOT/$path"; then
      pass "AC1: operational command present in $path: $cmd"
    else
      fail "AC1: operational command missing from $path: $cmd"
    fi
  done
done

# --- AC1b (negative, T069): the template no longer carries the table -----------------
if grep -qF '## Karpathy Engineering Principles (Compact)' "$TEMPLATE"; then
  fail "AC1b: the Karpathy heading is still in the template (it moved to the role guides)"
else
  pass "AC1b: the Karpathy heading is no longer in the template"
fi

for cmd in "Ask vs. Guess" "Prohibit speculation" "Scope locking" "Convert all imperative instructions"; do
  if grep -qF "$cmd" "$TEMPLATE"; then
    fail "AC1b: operational command still in the template: $cmd"
  else
    pass "AC1b: operational command absent from the template: $cmd"
  fi
done

# --- AC2: ## Search Before You Build, exactly 7 numbered rungs (1-7) ---------------
if grep -qF '## Search Before You Build' "$TEMPLATE"; then
  pass "AC2: ## Search Before You Build section present"

  rung_lines="$(awk '
    /^## Search Before You Build$/ { capture=1; next }
    capture && /^## / { capture=0 }
    capture { print }
  ' "$TEMPLATE" | { grep -cE '^[0-9]+\.' || true; })"

  if [ "$rung_lines" -eq 7 ]; then
    pass "AC2: exactly 7 numbered rungs found"
  else
    fail "AC2: expected exactly 7 numbered rungs, found $rung_lines"
  fi

  for n in 1 2 3 4 5 6 7; do
    if awk '
      /^## Search Before You Build$/ { capture=1; next }
      capture && /^## / { capture=0 }
      capture { print }
    ' "$TEMPLATE" | grep -qE "^${n}\."; then
      pass "AC2: rung $n present"
    else
      fail "AC2: rung $n missing"
    fi
  done
else
  fail "AC2: ## Search Before You Build section missing"
fi

# --- AC3: non-negotiables block ------------------------------------------------------
for term in "orrectness" "alidation" "rror handling" "ecurity" "xplicit requirements"; do
  if grep -qi "$term" "$TEMPLATE"; then
    pass "AC3: non-negotiable term present: $term"
  else
    fail "AC3: non-negotiable term missing: $term"
  fi
done
if grep -qiE "never (be )?traded (away )?for a shorter diff|never trade.* for a shorter diff" "$TEMPLATE"; then
  pass "AC3: 'never traded for a shorter diff' guard present"
else
  fail "AC3: 'never traded for a shorter diff' guard missing"
fi

# --- AC5 (negative): CLAUDE.md NOT added to the Mandatory Startup Sequence ----------
startup_block="$(awk '
  /^## Mandatory Startup Sequence/ { capture=1; print; next }
  capture && /^## / { capture=0 }
  capture { print }
' "$TEMPLATE")"

if printf '%s' "$startup_block" | grep -q 'CLAUDE\.md'; then
  fail "AC5: CLAUDE.md was added to the Mandatory Startup Sequence read list (cost guard violated)"
else
  pass "AC5: CLAUDE.md not added to the Mandatory Startup Sequence"
fi

# --- AC6 (negative): "ponytail" nowhere in .claude/agents/** ------------------------
if grep -riq 'ponytail' "$ROOT/.claude/agents/"; then
  fail "AC6: the string 'ponytail' appears somewhere in .claude/agents/**"
else
  pass "AC6: 'ponytail' does not appear anywhere in .claude/agents/**"
fi

# --- AC7 (negative): file grows by <=45 lines (87 -> <=132) ------------------------
cur_lines="$(wc -l < "$TEMPLATE" | tr -d ' ')"
if [ "$cur_lines" -le "$BUDGET_LINES" ]; then
  pass "AC7: template is $cur_lines lines (budget <=$BUDGET_LINES, baseline $BASELINE_LINES)"
else
  fail "AC7: template is $cur_lines lines (budget <=$BUDGET_LINES, baseline $BASELINE_LINES)"
fi

# --- AC8 (negative): role guides byte-identical to HEAD -----------------------------
if git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  for f in backend.md frontend.md qa.md common-infrastructure.md; do
    path=".claude/agents/$f"
    if git -C "$ROOT" cat-file -e "HEAD:$path" 2>/dev/null; then
      head_sum="$(git -C "$ROOT" show "HEAD:$path" | shasum -a 256 | awk '{print $1}')"
      cur_sum="$(shasum -a 256 "$ROOT/$path" | awk '{print $1}')"
      if [ "$head_sum" = "$cur_sum" ]; then
        pass "AC8: $f byte-identical to HEAD"
      else
        fail "AC8: $f differs from HEAD (checksum mismatch)"
      fi
    else
      fail "AC8: HEAD:$path not found via git — cannot verify"
    fi
  done
else
  fail "AC8: not a git repo — cannot checksum-verify role guides against HEAD"
fi

if [ "$FAIL" -ne 0 ]; then
  printf '\ntest-agent-template: FAILED\n' >&2
  exit 1
fi

printf '\ntest-agent-template: all checks passed\n'
exit 0
