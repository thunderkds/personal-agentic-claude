#!/bin/sh
# tests/test_tech_lead_pipeline_pointer.sh — the pipeline doctrine points at the
# tech-lead pack only when the pack is activated (T219, FR-007 a/c, FR-009).
#
# Covers AC 1-3 of tasks/TASK_GUIDE_T219.md: a conditional Stage 2 item and a
# conditional Stage 5 item 4 sub-bullet in pipeline-stages.md. AC 3b (one
# AGENTS.md line) is blocked: AGENTS.md has 0 lines of headroom (196-line cap in
# test_vital_slice.py / test_auto_mode.py), so this test only guards that cap.
# Mutation controls M1-M2 strip the `agents/tech-lead.md` condition from a copy
# of pipeline-stages.md; each check must then fail.
#
# Run: bash tests/test_tech_lead_pipeline_pointer.sh
set -u

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)
STAGES="$REPO_ROOT/docs/claude-md/pipeline-stages.md"
AGENTS="$REPO_ROOT/AGENTS.md"

PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1" >&2; }
verdict() {
  _vp=$1; _vf=$2; shift 2
  if "$@"; then pass "$_vp"; else fail "$_vf"; fi
}

WORK=$(mktemp -d "${TMPDIR:-/tmp}/tl-pointer-test.XXXXXX")
trap 'rm -rf "$WORK"' EXIT INT TERM HUP

# Stage 2 pointer: a numbered item after item 5, before "Task State Management".
stage2_ok() {
  _s=$(awk '/^## Stage 2:/{f=1} /^\*\*Task State Management/{f=0} f' "$1" | grep '^6\. ')
  [ -n "$_s" ] || return 1
  for _t in 'If `agents/tech-lead.md` exists' 'packs/tech-lead/PACK.md' 'PROJECT_SPEC.md' \
            'spawn `tech-lead`' 'docs/architecture/README.md' 'user approval' 'Auto mode: map only'; do
    printf '%s\n' "$_s" | grep -qF -- "$_t" || return 1
  done
}

# Stage 5 pointer: a sub-bullet of item 4, right after the git diff bullet.
stage5_ok() {
  _s=$(awk '/^## Stage 5:/{f=1} f' "$1" | awk '/^4\. /{g=1} /^5\. /{g=0} g')
  _l=$(printf '%s\n' "$_s" | grep -A1 'git diff HEAD~1 --name-only' | tail -1)
  [ -n "$_l" ] || return 1
  for _t in 'If `agents/tech-lead.md` and `docs/architecture/README.md` both exist' \
            'packs/tech-lead/PACK.md' 'watched paths' 'spawn `tech-lead`' 'refresh mode' \
            'matched documents only' 'nothing'; do
    printf '%s\n' "$_l" | grep -qF -- "$_t" || return 1
  done
}

agents_caps_ok() {
  [ "$(wc -l < "$1")" -le 196 ] && [ "$(wc -c < "$1")" -le 32768 ]
}

# ── Positive checks on the real files ────────────────────────────────────────
verdict "AC1: Stage 2 item 6 is a conditional tech-lead spawn for the document map" \
        "AC1: Stage 2 item 6 missing or incomplete" stage2_ok "$STAGES"
verdict "AC2: Stage 5 item 4 sub-bullet matches watched paths and spawns refresh" \
        "AC2: Stage 5 item 4 sub-bullet missing or incomplete" stage5_ok "$STAGES"
verdict "AC3: pipeline-stages.md names tech-lead only in the two conditional additions" \
        "AC3: an unconditional or extra tech-lead mention in pipeline-stages.md" \
        sh -c '[ "$(grep -c "tech-lead" "$1")" -eq 2 ]' _ "$STAGES"
verdict "AC3b (blocked, see TASK_REVIEW_T219): AGENTS.md stays within its 196-line budget and 32768 bytes" \
        "AC3b: AGENTS.md exceeds its size cap" agents_caps_ok "$AGENTS"

# ── Mutation controls: drop the activation condition from a copy ─────────────
# refuses <check> <file> -> succeeds only when the check fails on the file
refuses() { ! "$@"; }

sed 's/If `agents\/tech-lead.md` exists/Always/' "$STAGES" > "$WORK/stages_m1.md"
verdict "M1: Stage 2 pointer without its condition fails the check" \
        "M1: Stage 2 check still passes on the unconditional mutant" refuses stage2_ok "$WORK/stages_m1.md"

sed 's/If `agents\/tech-lead.md` and `docs\/architecture\/README.md` both exist/Always/' "$STAGES" > "$WORK/stages_m2.md"
verdict "M2: Stage 5 sub-bullet without its condition fails the check" \
        "M2: Stage 5 check still passes on the unconditional mutant" refuses stage5_ok "$WORK/stages_m2.md"

printf '\n%s passed, %s failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
