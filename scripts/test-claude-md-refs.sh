#!/bin/sh
# test-claude-md-refs.sh — reference-resolution + scope-guard test for CLAUDE.md (T039).
#
# Validates that the `## Skills vs Agents` dedup did not break any live reference and
# stayed within the agreed scope bounds. Checks (AC numbers from
# tasks/TASK_GUIDE_T039.md):
#   AC1 — `## Skills vs Agents` section is <=30 lines (was 72)
#   AC2 — every `Skill({ skill: "X" })` ref resolves to .claude/skills/X/SKILL.md or a
#         documented built-in
#   AC3 — every `subagent_type` value resolves to a `.claude/agents/*.md` whose `name:`
#         field matches
#
# AC4 (the four preserved "keep" items) is intentionally NOT automated here — it asserts the
# *presence of specific prose content* (mechanism table, subagent_type mapping, spawn-prompt
# note, blast-radius disambiguation), which is a manual editorial judgment call, not a
# structural invariant grep can reliably distinguish from paraphrase. Checked manually at
# Stage 4 review instead.
#   AC5 — `### Hard-Stop Gates` and `## Permanent Rules` sections are byte-identical to BASELINE_REF
#   AC6 — total CLAUDE.md line count decreased by >=40 and <=80 vs BASELINE_REF
#
# AC1/AC2/AC3 are permanent invariants: they hold for CLAUDE.md at any commit, forever, and
# always run. AC5/AC6 are a one-shot scope guard for this specific dedup (T039) — they compare
# the working tree against BASELINE_REF, the commit immediately before the dedup landed
# (99940b8). Once T039 is merged, HEAD == BASELINE_REF's descendant, not "the dedup itself",
# so these two checks stay meaningful only relative to that fixed pre-change commit, not a
# floating HEAD. Override via `BASELINE_REF=<sha> sh scripts/test-claude-md-refs.sh` if this
# script is ever reused for a future CLAUDE.md scope guard.
#
# No shellcheck available in this environment (memory/learnings.md) — substituted with
# `sh -n CLAUDE.md`-equivalent static check (N/A, this is a Markdown file, not shell) plus
# a real `sh` execution of this script itself; see Completion Checklist in the TASK_GUIDE.
#
# Usage: sh scripts/test-claude-md-refs.sh
#        BASELINE_REF=<sha> sh scripts/test-claude-md-refs.sh

set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_MD="$ROOT/CLAUDE.md"
BASELINE_REF="${BASELINE_REF:-99940b8}"
FAIL=0

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  FAIL=1
}

pass() {
  printf 'PASS: %s\n' "$1"
}

if [ ! -f "$CLAUDE_MD" ]; then
  printf 'test-claude-md-refs: ERROR — CLAUDE.md not found at %s\n' "$CLAUDE_MD" >&2
  exit 1
fi

# Documented built-in skills — not backed by a .claude/skills/<name>/SKILL.md file,
# but named explicitly in CLAUDE.md's "Built-in Claude Code skills" table.
BUILTINS="security-review verify run update-config fewer-permission-prompts"

# --- AC2: every Skill({ skill: "X" }) reference resolves ---------------------------
# Exclude only the literal mechanism/syntax-example line itself (Skill({ skill: "name" })),
# not any token named "name" or "X" wherever it appears — a real broken ref that happens to
# be literally named "name" or "X" must still be caught.
skill_refs="$(grep -v 'Skill({ skill: "name" })' "$CLAUDE_MD" \
  | grep -oE 'skill: "[a-zA-Z0-9_-]+"' | sed -E 's/skill: "(.*)"/\1/' | sort -u)"
if [ -z "$skill_refs" ]; then
  fail "AC2: no Skill({ skill: \"X\" }) references found — extraction regex may be broken"
else
  bad_skill_refs=""
  for name in $skill_refs; do
    is_builtin=0
    for b in $BUILTINS; do
      [ "$name" = "$b" ] && is_builtin=1 && break
    done
    if [ "$is_builtin" -eq 0 ] && [ ! -f "$ROOT/.claude/skills/$name/SKILL.md" ]; then
      bad_skill_refs="$bad_skill_refs $name"
    fi
  done
  if [ -n "$bad_skill_refs" ]; then
    fail "AC2: unresolved skill reference(s):$bad_skill_refs"
  else
    pass "AC2: all Skill({ skill: \"X\" }) references resolve"
  fi
fi

# --- AC3: every subagent_type value (project sub-agent table rows) resolves --------
# Real subagent_type values live in table rows shaped:
#   | Role | `subagent_type-value` | `.claude/agents/<file>.md` |
# Extract the subagent_type cell from any row that also names a .claude/agents/ path.
type_refs="$(grep -E '^\|.*\| *`[a-zA-Z0-9_-]+` *\| *`\.claude/agents/[a-zA-Z0-9_-]+\.md` *\|' "$CLAUDE_MD" \
  | sed -E 's/^\|[^|]*\| *`([a-zA-Z0-9_-]+)` *\|.*/\1/' \
  | sort -u)"
if [ -z "$type_refs" ]; then
  fail "AC3: no subagent_type table rows found — extraction regex may be broken"
else
  bad_type_refs=""
  for name in $type_refs; do
    found=0
    for f in "$ROOT"/.claude/agents/*.md; do
      [ -f "$f" ] || continue
      if grep -qE "^name: ${name}\$" "$f" 2>/dev/null; then
        found=1
        break
      fi
    done
    if [ "$found" -eq 0 ]; then
      bad_type_refs="$bad_type_refs $name"
    fi
  done
  if [ -n "$bad_type_refs" ]; then
    fail "AC3: unresolved subagent_type reference(s):$bad_type_refs"
  else
    pass "AC3: all subagent_type references resolve"
  fi
fi

# --- AC1: ## Skills vs Agents section is <=30 lines ---------------------------------
section_lines="$(awk '
  /^## Skills vs Agents$/ { capture=1; next }
  capture && /^## / { capture=0 }
  capture { print }
' "$CLAUDE_MD" | wc -l | tr -d ' ')"

if [ "$section_lines" -le 30 ]; then
  pass "AC1: ## Skills vs Agents section is $section_lines lines (<=30)"
else
  fail "AC1: ## Skills vs Agents section is $section_lines lines (expected <=30)"
fi

# --- AC5: Hard-Stop Gates and Permanent Rules unchanged vs BASELINE_REF -------------
# Note the real heading levels in CLAUDE.md: "### Hard-Stop Gates (...)" is H3 with a
# parenthetical (not the bare H2 "## Hard-Stop Gates" the original TASK_GUIDE AC5 text
# assumed); "## Permanent Rules" is a plain H2. Each extraction anchors on its own level.
if git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1 && git -C "$ROOT" cat-file -e "$BASELINE_REF:CLAUDE.md" 2>/dev/null; then
  extract_section() {
    # $1 = heading-line regex (anchored, e.g. '^### Hard-Stop Gates'), reads stdin.
    awk -v heading="$1" '
      $0 ~ heading { capture=1; print; next }
      capture && /^#{1,3} / { capture=0 }
      capture { print }
    '
  }

  cur_hardstop="$(extract_section '^### Hard-Stop Gates' < "$CLAUDE_MD")"
  base_hardstop="$(git -C "$ROOT" show "$BASELINE_REF:CLAUDE.md" | extract_section '^### Hard-Stop Gates')"
  cur_permanent="$(extract_section '^## Permanent Rules$' < "$CLAUDE_MD")"
  base_permanent="$(git -C "$ROOT" show "$BASELINE_REF:CLAUDE.md" | extract_section '^## Permanent Rules$')"

  if [ -z "$cur_hardstop" ] || [ -z "$base_hardstop" ]; then
    fail "AC5: ### Hard-Stop Gates extraction returned empty — heading regex is broken, not a pass"
  elif [ "$cur_hardstop" = "$base_hardstop" ]; then
    pass "AC5: ### Hard-Stop Gates byte-identical to $BASELINE_REF"
  else
    fail "AC5: ### Hard-Stop Gates differs from $BASELINE_REF"
  fi

  if [ -z "$cur_permanent" ] || [ -z "$base_permanent" ]; then
    fail "AC5: ## Permanent Rules extraction returned empty — heading regex is broken, not a pass"
  elif [ "$cur_permanent" = "$base_permanent" ]; then
    pass "AC5: ## Permanent Rules byte-identical to $BASELINE_REF"
  else
    fail "AC5: ## Permanent Rules differs from $BASELINE_REF"
  fi

  # --- AC6: total line count decreased by >=40 and <=80 vs BASELINE_REF ------------
  base_lines="$(git -C "$ROOT" show "$BASELINE_REF:CLAUDE.md" | wc -l | tr -d ' ')"
  cur_lines="$(wc -l < "$CLAUDE_MD" | tr -d ' ')"
  delta=$((base_lines - cur_lines))
  if [ "$delta" -ge 40 ] && [ "$delta" -le 80 ]; then
    pass "AC6: line count decreased by $delta (was $base_lines at $BASELINE_REF, now $cur_lines; expected 40-80)"
  else
    fail "AC6: line count decreased by $delta (was $base_lines at $BASELINE_REF, now $cur_lines; expected 40-80)"
  fi
else
  fail "AC5/AC6: cannot read $BASELINE_REF:CLAUDE.md via git — is this a git repo with that commit?"
fi

if [ "$FAIL" -ne 0 ]; then
  printf '\ntest-claude-md-refs: FAILED\n' >&2
  exit 1
fi

printf '\ntest-claude-md-refs: all checks passed\n'
exit 0
