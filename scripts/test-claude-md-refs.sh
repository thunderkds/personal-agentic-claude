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
#   AC5 — `## Hard-Stop Gates` and `## Permanent Rules` sections are byte-identical to HEAD
#   AC6 — total CLAUDE.md line count decreased by >=40 and <=80 vs HEAD
#
# No shellcheck available in this environment (memory/learnings.md) — substituted with
# `sh -n CLAUDE.md`-equivalent static check (N/A, this is a Markdown file, not shell) plus
# a real `sh` execution of this script itself; see Completion Checklist in the TASK_GUIDE.
#
# Usage: sh scripts/test-claude-md-refs.sh

set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_MD="$ROOT/CLAUDE.md"
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
# Exclude literal placeholder tokens used in mechanism/syntax examples (not real refs).
PLACEHOLDERS="name X"
skill_refs="$(grep -oE 'skill: "[a-zA-Z0-9_-]+"' "$CLAUDE_MD" | sed -E 's/skill: "(.*)"/\1/' | sort -u)"
for p in $PLACEHOLDERS; do
  skill_refs="$(printf '%s\n' "$skill_refs" | grep -vx "$p" || true)"
done
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

# --- AC5: Hard-Stop Gates and Permanent Rules unchanged vs HEAD ---------------------
if git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1 && git -C "$ROOT" cat-file -e HEAD:CLAUDE.md 2>/dev/null; then
  extract_section() {
    # $1 = file (path or "HEAD:CLAUDE.md" via git show), $2 = heading regex
    awk -v heading="$2" '
      $0 ~ "^## " heading "$" { capture=1; print; next }
      capture && /^## / { capture=0 }
      capture { print }
    '
  }

  cur_hardstop="$(extract_section "$CLAUDE_MD" "Hard-Stop Gates.*" < "$CLAUDE_MD")"
  head_hardstop="$(git -C "$ROOT" show HEAD:CLAUDE.md | extract_section "-" "Hard-Stop Gates.*")"
  cur_permanent="$(extract_section "$CLAUDE_MD" "Permanent Rules" < "$CLAUDE_MD")"
  head_permanent="$(git -C "$ROOT" show HEAD:CLAUDE.md | extract_section "-" "Permanent Rules")"

  if [ "$cur_hardstop" = "$head_hardstop" ]; then
    pass "AC5: ## Hard-Stop Gates byte-identical to HEAD"
  else
    fail "AC5: ## Hard-Stop Gates differs from HEAD"
  fi

  if [ "$cur_permanent" = "$head_permanent" ]; then
    pass "AC5: ## Permanent Rules byte-identical to HEAD"
  else
    fail "AC5: ## Permanent Rules differs from HEAD"
  fi

  # --- AC6: total line count decreased by >=40 and <=80 vs HEAD --------------------
  head_lines="$(git -C "$ROOT" show HEAD:CLAUDE.md | wc -l | tr -d ' ')"
  cur_lines="$(wc -l < "$CLAUDE_MD" | tr -d ' ')"
  delta=$((head_lines - cur_lines))
  if [ "$delta" -ge 40 ] && [ "$delta" -le 80 ]; then
    pass "AC6: line count decreased by $delta (was $head_lines, now $cur_lines; expected 40-80)"
  else
    fail "AC6: line count decreased by $delta (was $head_lines, now $cur_lines; expected 40-80)"
  fi
else
  fail "AC5/AC6: cannot read HEAD:CLAUDE.md via git — is this a git repo with a committed CLAUDE.md?"
fi

if [ "$FAIL" -ne 0 ]; then
  printf '\ntest-claude-md-refs: FAILED\n' >&2
  exit 1
fi

printf '\ntest-claude-md-refs: all checks passed\n'
exit 0
