#!/bin/bash
# tests/test_tech_lead_pack.sh — packs/tech-lead ships the agent, the skill and the user guide (T218).
#
# Covers AC 1-5, the README line (AC 6) and the negative case (AC 8) of
# tasks/TASK_GUIDE_T218.md. Mutation controls run the same checks against mutant
# copies, so the checks are seen failing on every run:
#   M1 the agent file without the "never edit PROJECT_SPEC.md" rule
#   M2 the skill without its ER diagram section
#   M3 PACK.md with a `setup.sh --pack` line
#
# Run: bash tests/test_tech_lead_pack.sh
set -u

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)
PACK="$REPO_ROOT/packs/tech-lead"

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1" >&2; }
# verdict <pass-msg> <fail-msg> <command...>
verdict() {
  _vp=$1; _vf=$2; shift 2
  if "$@" 2>/dev/null; then pass "$_vp"; else fail "$_vf"; fi
}

WORK=$(mktemp -d "${TMPDIR:-/tmp}/tech-lead-pack-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT INT TERM HUP

# fm_value <file> <key> -> the frontmatter value of <key> (first --- block only)
fm_value() {
  awk -v k="$2" '
    NR == 1 && $0 == "---" { infm = 1; next }
    infm && $0 == "---" { exit }
    infm && index($0, k ":") == 1 { sub("^" k ":[ \t]*", ""); print; exit }
  ' "$1"
}

# ── AC 1 — files and frontmatter (agent dir $1, skill dir $2) ────────────────
check_files() {
  [ -f "$1/PACK.md" ] && [ -f "$1/agents/tech-lead.md" ] && [ -f "$1/skills/architecture-docs/SKILL.md" ]
}
check_agent_frontmatter() {
  _a="$1/agents/tech-lead.md"
  [ "$(fm_value "$_a" name)" = "tech-lead" ] || return 1
  _d=$(fm_value "$_a" description | sed 's/^"//')
  case "$_d" in "Use when"*) ;; *) return 1 ;; esac
  _t=$(fm_value "$_a" tools)
  [ -n "$_t" ] || return 1
  case ", $_t," in *", Agent,"*) return 1 ;; esac
}
check_skill_frontmatter() {
  _s="$1/skills/architecture-docs/SKILL.md"
  [ "$(fm_value "$_s" name)" = "architecture-docs" ] && [ -n "$(fm_value "$_s" description)" ]
}

# ── AC 2 — one ### section per v1 document type, each with its parts ────────
# section_of <skill> <heading> -> the text of that ### section
section_of() {
  awk -v h="### $2" '
    $0 == h { on = 1; next }
    on && /^### / { exit }
    on { print }
  ' "$1"
}
check_skill_sections() {
  _s="$1/skills/architecture-docs/SKILL.md"
  # heading | Mermaid keyword that the skeleton must contain
  while IFS='|' read -r _h _kw; do
    _body=$(section_of "$_s" "$_h")
    [ -n "$_body" ] || { echo "no section: $_h" >&2; return 1; }
    for _part in "Needed when" "Required content" "Watched paths"; do
      printf '%s\n' "$_body" | grep -q "$_part" || { echo "$_h lacks '$_part'" >&2; return 1; }
    done
    printf '%s\n' "$_body" | grep -q "$_kw" || { echo "$_h lacks '$_kw'" >&2; return 1; }
  done <<'LIST'
C4 + high-level overview|C4Container
Sequence diagram|sequenceDiagram
Journey diagram|journey
ER diagram|erDiagram
Risk register|Likelihood
Roadmap|gantt
LIST
  section_of "$_s" "C4 + high-level overview" | grep -q 'flowchart' || { echo "no flowchart fallback note" >&2; return 1; }
  section_of "$_s" "C4 + high-level overview" | grep -q 'C4Context' || { echo "no C4Context" >&2; return 1; }
  section_of "$_s" "Roadmap" | grep -q 'timeline' || { echo "no timeline" >&2; return 1; }
}

# ── AC 3 — the document-map template ────────────────────────────────────────
check_map_template() {
  _s="$1/skills/architecture-docs/SKILL.md"
  grep -q '^| # | Document | Needed? | Reason (one line) | File | Watched paths |' "$_s" || { echo "map columns" >&2; return 1; }
  for _l in 'docs/adr/' 'PRD.md' 'PROJECT_SPEC.md' 'memory/glossary.md' 'to-issues' 'PROJECT_KANBAN.md' 'security-review' 'docs/architecture/README.md'; do
    grep -q -- "$_l" "$_s" || { echo "map lacks link row: $_l" >&2; return 1; }
  done
}

# ── AC 4 — the agent's hard rules (agent file $1) ───────────────────────────
check_agent_rules() {
  _a="$1/agents/tech-lead.md"
  grep -q 'Map first' "$_a" || { echo "map-first" >&2; return 1; }
  grep -q 'Write no other document until the user approves the map' "$_a" || { echo "approval" >&2; return 1; }
  grep -q '`\[auto\]` means map only' "$_a" || { echo "auto" >&2; return 1; }
  grep -q 'Never edit `PRD.md`, `PROJECT_SPEC.md` or `PROJECT_KANBAN.md`' "$_a" || { echo "never-edit" >&2; return 1; }
  grep -q 'Never overwrite a file under `docs/architecture/` that the map does not list' "$_a" || { echo "overwrite" >&2; return 1; }
  grep -q 'Sources' "$_a" && grep -q '(inferred)' "$_a" || { echo "sources" >&2; return 1; }
  grep -q 'update only the documents whose watched paths the diff matched' "$_a" || { echo "refresh" >&2; return 1; }
}

# ── AC 5 — PACK.md layout and user guide (pack dir $1) ──────────────────────
check_pack_md() {
  _p="$1/PACK.md"
  for _h in "## When to use this pack" "**Do NOT select if:**" "## What this pack adds" "**Boundary from core agents:**" "## Agents installed" "## Skills installed" "## User guide"; do
    grep -qF -- "$_h" "$_p" || { echo "PACK.md lacks '$_h'" >&2; return 1; }
  done
  grep -q 'cp packs/tech-lead/agents/tech-lead.md agents/' "$_p" || { echo "no agent copy line" >&2; return 1; }
  grep -q 'cp -r packs/tech-lead/skills/architecture-docs skills/' "$_p" || { echo "no skill copy line" >&2; return 1; }
  for _w in "Stage 2" "On demand" "Refresh" "Agent({ subagent_type: \"tech-lead\"" "docs/architecture/"; do
    grep -qF -- "$_w" "$_p" || { echo "PACK.md lacks '$_w'" >&2; return 1; }
  done
  if grep -q 'setup\.sh.*--pack' "$_p"; then echo "PACK.md has a setup.sh --pack line" >&2; return 1; fi
}

# ── AC 6 (README part) and AC 8 (nothing activated) ──────────────────────────
check_readme_line() { grep -q '`tech-lead`' "$REPO_ROOT/README.md"; }
check_not_activated() {
  [ ! -e "$REPO_ROOT/agents/tech-lead.md" ] && [ ! -e "$REPO_ROOT/skills/architecture-docs" ] \
    && [ ! -e "$REPO_ROOT/.claude/agents/tech-lead.md" ] && [ ! -e "$REPO_ROOT/.claude/skills/architecture-docs" ]
}

# ── Checks on the real pack ──────────────────────────────────────────────────
verdict "AC1: PACK.md, agent and skill files exist" "AC1 files" check_files "$PACK"
verdict "AC1: agent frontmatter (name, 'Use when', tools without Agent)" "AC1 agent frontmatter" check_agent_frontmatter "$PACK"
verdict "AC1: skill frontmatter (name, description)" "AC1 skill frontmatter" check_skill_frontmatter "$PACK"
verdict "AC2: one section per document type, each with its parts and Mermaid keyword" "AC2 skill sections" check_skill_sections "$PACK"
verdict "AC3: document-map template has its columns and the link rows" "AC3 map template" check_map_template "$PACK"
verdict "AC4: agent file states the hard rules" "AC4 agent rules" check_agent_rules "$PACK"
verdict "AC5: PACK.md layout, user guide, no setup.sh --pack line" "AC5 PACK.md" check_pack_md "$PACK"
verdict "AC6: README pack list names tech-lead" "AC6 README" check_readme_line
verdict "AC8: the pack is not activated (nothing in agents/, skills/, .claude/)" "AC8 activated" check_not_activated

# ── Mutation controls: the checks must fail on a mutant copy ─────────────────
make_mutant() {  # make_mutant <name> -> a copy of the pack under $WORK/<name>
  mkdir -p "$WORK/$1"
  cp -r "$PACK" "$WORK/$1/tech-lead"
}

make_mutant m1
sed -i '/Never edit `PRD.md`, `PROJECT_SPEC.md`/d' "$WORK/m1/tech-lead/agents/tech-lead.md"
if ! check_agent_rules "$WORK/m1/tech-lead" 2>/dev/null; then
  pass "M1: without the never-edit rule, the AC4 check fails"
else
  fail "M1: the AC4 check passed on an agent without the never-edit rule"
fi

make_mutant m2
sed -i 's/^### ER diagram$/### Entities/' "$WORK/m2/tech-lead/skills/architecture-docs/SKILL.md"
if ! check_skill_sections "$WORK/m2/tech-lead" 2>/dev/null; then
  pass "M2: without the ER diagram section, the AC2 check fails"
else
  fail "M2: the AC2 check passed on a skill without the ER section"
fi

make_mutant m3
printf '\nsh ~/.supervisor/setup.sh --pack=tech-lead\n' >> "$WORK/m3/tech-lead/PACK.md"
if ! check_pack_md "$WORK/m3/tech-lead" 2>/dev/null; then
  pass "M3: with a setup.sh --pack line, the AC5 check fails"
else
  fail "M3: the AC5 check passed on a PACK.md with a setup.sh --pack line"
fi

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
