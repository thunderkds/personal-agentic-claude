#!/bin/sh
# validate.sh — framework-integrity linter for the Supervisor distribution.
#
# Verifies the repo can be deployed cleanly and that every reference resolves:
#   1. MANIFEST entries all exist on disk
#   2. Skills + agents carry valid YAML frontmatter (name + description)
#   3. File paths referenced inside CLAUDE.md actually exist
#   4. Required folders/templates listed in CLAUDE.md are present
#
# Pure POSIX sh + grep/sed — no external deps. Exit non-zero on any failure.
# Usage: sh scripts/validate.sh   (run from repo root)

set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FAIL=0
err()  { printf '  [FAIL] %s\n' "$*"; FAIL=1; }
ok()   { printf '  [ok]   %s\n' "$*"; }
section() { printf '\n== %s ==\n' "$*"; }

# ── 1. MANIFEST entries resolve ──────────────────────────────────────────────
section "MANIFEST entries resolve on disk"
if [ ! -f MANIFEST ]; then
  err "MANIFEST file is missing"
else
  # Field 1 only: a line may carry trailing `<harness>=<dest>` destination pairs
  # (T097). Those name a projection target, not a path that must exist on disk.
  # A `!<path>` line is an exclusion (T113), not an entry — skipped like a comment.
  while IFS= read -r line; do
    line=$(printf '%s' "$line" | tr -d '\r' | awk '$0 !~ /^[[:space:]]*(#|$|!)/ { print $1 }')
    [ -n "$line" ] || continue
    if [ -e "$line" ]; then ok "$line"; else err "MANIFEST entry not found: $line"; fi
  done < MANIFEST
fi

# ── 2. Frontmatter on skills + agents ────────────────────────────────────────
# A valid file starts with '---', has name: and description: before the closing '---'.
check_frontmatter() {
  f="$1"
  [ -f "$f" ] || { err "missing file: $f"; return; }
  first=$(sed -n '1p' "$f")
  if [ "$first" != "---" ]; then err "$f: no opening '---' frontmatter"; return; fi
  fm=$(sed -n '2,/^---$/p' "$f")
  printf '%s\n' "$fm" | grep -q '^name:'        || { err "$f: frontmatter missing 'name:'"; return; }
  printf '%s\n' "$fm" | grep -q '^description:' || { err "$f: frontmatter missing 'description:'"; return; }
  ok "$f"
}

section "Skill frontmatter (skills/*/SKILL.md)"
for d in skills/*/; do
  [ -d "$d" ] || continue
  check_frontmatter "${d}SKILL.md"
done

section "Agent frontmatter (agents/*.md)"
for f in agents/*.md; do
  [ -f "$f" ] || continue
  check_frontmatter "$f"
done

# ── 3. File paths referenced in CLAUDE.md exist ──────────────────────────────
# Extract backticked tokens that look like in-repo paths (contain '/', end in a
# file/dir name). Skip per-project generated paths that are gitignored.
section "Path references in CLAUDE.md resolve"
skip_path() {
  case "$1" in
    tasks/TASK_GUIDE_Txxx.md|tasks/*) return 0 ;;   # generated per project
    PRD.md|PROJECT_SPEC.md|PROJECT_KANBAN.md|BRAINSTORMING_LOG.md) return 0 ;;
    memory/*) return 0 ;;                            # scaffolded per project
    docs/legacy/*) return 0 ;;                       # legacy-mode optional
    */) return 0 ;;                                  # bare dirs handled loosely below
  esac
  return 1
}
# Only check backticked tokens that contain a '/' — i.e. real in-repo relative
# paths. Bare filenames (architecture.md, TASK_GUIDE_Txxx.md) are prose mentions
# or per-project placeholders, not deployable references, so they're skipped.
# (Subshells can't set FAIL in POSIX sh, so failures are tallied into a file.)
MISSFILE="$(mktemp)"
# shellcheck disable=SC2016  # backticks in the regex are literal, not expansion
grep -oE '`[A-Za-z0-9_./-]+`' CLAUDE.md \
  | tr -d '`' \
  | grep '/' \
  | grep -E '\.(md|json|py|sh)$' \
  | sort -u \
  | while IFS= read -r p; do
      if skip_path "$p"; then continue; fi
      if [ -e "$p" ]; then ok "$p"; else err "CLAUDE.md references missing path: $p"; printf 'x' >> "$MISSFILE"; fi
    done
[ ! -s "$MISSFILE" ] || FAIL=1
rm -f "$MISSFILE"

# ── 4. Mandatory folders from CLAUDE.md ──────────────────────────────────────
section "Mandatory framework folders present"
for d in agents skills templates; do
  if [ -d "$d" ]; then ok "$d/"; else err "required folder missing: $d/"; fi
done

# ── 5. Canon symlinks Claude Code reads through ──────────────────────────────
section "Claude harness symlinks (.claude/{skills,agents} -> ../{skills,agents})"
for c in skills agents; do
  if [ ! -L ".claude/$c" ]; then
    err ".claude/$c is not a symlink (canon lives at ./$c; .claude must link to it)"
  elif [ "$(readlink ".claude/$c")" != "../$c" ]; then
    err ".claude/$c -> $(readlink ".claude/$c") (must be the relative path ../$c)"
  elif [ ! -e ".claude/$c" ]; then
    err ".claude/$c is a broken symlink"
  else
    ok ".claude/$c -> ../$c"
  fi
done

# ── Result ───────────────────────────────────────────────────────────────────
printf '\n'
if [ "$FAIL" -eq 0 ]; then
  printf 'validate.sh: PASS\n'
else
  printf 'validate.sh: FAIL\n'
fi
exit "$FAIL"
