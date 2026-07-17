#!/bin/sh
# update.sh — Supervisor Agent Deployment System updater (direct-to-repo, ADR-0001)
# Usage: bash update.sh
#
# Update model (ADR-0001): the old central-clone `git pull` is gone. update.sh
# operates on the CURRENT git repository. It re-fetches the harness fresh into a
# temp clone (via lib/harness-fetch.sh), then for EACH individual file under each
# MANIFEST path compares the working repo's current content hash against the hash
# recorded in .claude/harness-lock.json (written by setup.sh, T032):
#   - hash unchanged since install  -> overwrite silently with the fresh upstream
#   - hash changed (user customized) -> show a diff and prompt per file:
#         [o]verwrite / [s]kip / [v]iew diff again
# Files never tracked in the lock, or new upstream files, are handled explicitly
# (see below). The lock is then re-recorded to reflect what the user accepted.
#
# Refuses to run if the target is not a git repo, or if any MANIFEST path is a
# symlink (an old symlink-model install) — it detects and refuses, it does NOT
# auto-convert (migration is out of scope per ADR-0001).
#
# Env overrides (fetch source only; NO central clone is created or required):
#   SUPERVISOR_REPO   — full git URL to fetch (defaults to the GITHUB_USERNAME repo)
#   GITHUB_USERNAME   — update from a fork (default: thunderkds)
set -e

# ── Locate this script so we can source its co-located fetch library ─────────
SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)

# ── Logging helpers (TTY-aware color, plain-text fallback) ────────────────────
GREEN=''; YELLOW=''; RED=''; RESET=''
if [ -t 1 ]; then
  GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; RESET='\033[0m'
fi
log_info()  { printf "${GREEN}[info]${RESET}  %s\n"  "$*"; }
log_warn()  { printf "${YELLOW}[warn]${RESET}  %s\n" "$*" >&2; }
log_error() { printf "${RED}[error]${RESET} %s\n"   "$*" >&2; }

# ── Source the shared temp-clone-copy-discard fetch library (T031) ───────────
HARNESS_LIB="$SCRIPT_DIR/lib/harness-fetch.sh"
if [ ! -f "$HARNESS_LIB" ]; then
  log_error "Required library not found: $HARNESS_LIB. Run update.sh from a full checkout of the harness repo."
  exit 1
fi
# shellcheck source=lib/harness-fetch.sh
. "$HARNESS_LIB"

# ── Content hash of a single file (content-only, chmod-safe) ─────────────────
# Cross-checked against setup.sh's compute_file_hash (T032): identical algorithm
# and normalization (sha256sum/shasum, first field only) so hashes compare 1:1.
compute_file_hash() {
  _f="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$_f" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$_f" | awk '{print $1}'
  else
    log_error "Neither sha256sum nor shasum is available; cannot compare file hashes."
    exit 1
  fi
}

# ── Prerequisite: git installed ──────────────────────────────────────────────
check_git() {
  if ! command -v git >/dev/null 2>&1; then
    log_error "Git is required but not installed. Install Git and re-run update.sh."
    exit 1
  fi
}

# ── Prerequisite: the target (current) directory must be a git repository ─────
# Mirrors setup.sh: git history is the only undo path for the real files we copy.
# Run BEFORE any fetch or file write so a non-git dir is rejected touching nothing.
check_target_is_git_repo() {
  if ! git -C . rev-parse --git-dir >/dev/null 2>&1; then
    log_error "The current directory is not a git repository. Run update.sh from inside your project (git history is your only undo path)."
    exit 1
  fi
}

# ── Resolve GitHub username → repo URL (honors a pre-set SUPERVISOR_REPO) ─────
resolve_repo_url() {
  if [ -z "${SUPERVISOR_REPO:-}" ]; then
    GITHUB_USERNAME="${GITHUB_USERNAME:-thunderkds}"
    SUPERVISOR_REPO="https://github.com/${GITHUB_USERNAME}/personal-agentic-claude.git"
  fi
  log_info "Using repo: $SUPERVISOR_REPO"
}

# ── Symlink refusal (all-or-nothing, before any compare/overwrite) ───────────
# If ANY MANIFEST path in the target is a symlink, this is an old symlink-model
# install. Refuse the whole run with a migration instruction — do NOT convert.
detect_symlinks() {
  _manifest="$1"
  _found=0
  while IFS= read -r _line; do
    _line=$(printf '%s' "$_line" | tr -d '\r')
    case "$_line" in '#'*|'') continue ;; esac
    if [ -L "./$_line" ]; then
      log_error "MANIFEST path './$_line' is a symlink (old symlink-model install)."
      _found=1
    fi
  done < "$_manifest"

  if [ "$_found" -eq 1 ]; then
    log_error "This project was installed with the old symlink model. update.sh will not convert it."
    log_error "To migrate: remove the symlinked path(s) above, then re-run setup.sh to install real files, then use update.sh."
    exit 1
  fi
}

# ── Look up a file's recorded hash in the lock (empty string if absent) ───────
# Lock lines look like:     "path": "hash"
# The leading double-quote anchors the key so one path is not matched as a
# substring of a longer one. Always exits 0 (last pipeline stage is sed).
lookup_lock_hash() {
  _lk="$1"
  _key="$2"
  grep -F "\"$_key\": \"" "$_lk" 2>/dev/null | head -n1 | sed -e 's/.*: "//' -e 's/".*//'
}

# ── Emit key<TAB>hash for every file entry in the lock ────────────────────────
# Skips the top-level "files": { line (its value is `{`, not a hex hash).
extract_lock_pairs() {
  grep -E '^[[:space:]]*"[^"]+"[[:space:]]*:[[:space:]]*"[0-9a-f]+"[[:space:]]*,?[[:space:]]*$' "$1" 2>/dev/null \
    | sed -E 's/^[[:space:]]*"([^"]+)"[[:space:]]*:[[:space:]]*"([0-9a-f]+)".*/\1	\2/'
}

# ── Is a lock key covered by a current MANIFEST path? ─────────────────────────
is_under_manifest() {
  _k="$1"
  _mf="$2"
  while IFS= read -r _l; do
    _l=$(printf '%s' "$_l" | tr -d '\r')
    case "$_l" in '#'*|'') continue ;; esac
    case "$_k" in "$_l"/*|"$_l") return 0 ;; esac
  done < "$_mf"
  return 1
}

# ── Copy one fresh file into the target, creating parent dirs as needed ───────
install_file() {
  _s="$1"
  _d="$2"
  _parent=$(dirname "$_d")
  [ -d "$_parent" ] || mkdir -p "$_parent"
  cp "$_s" "$_d"
}

# ── Build the flat list of individual files under all MANIFEST paths ──────────
# Enumerated from the FRESH temp clone (upstream's current set), one repo-relative
# path per line, matching lock-key shape (no leading ./). Directories in MANIFEST
# are expanded to their files; a plain-file MANIFEST entry is emitted as-is.
build_fresh_file_list() {
  _manifest="$1"
  _out="$2"
  : > "$_out"
  while IFS= read -r _line; do
    _line=$(printf '%s' "$_line" | tr -d '\r')
    case "$_line" in '#'*|'') continue ;; esac
    _src="$HARNESS_TEMP_DIR/$_line"
    if [ -d "$_src" ]; then
      ( cd "$HARNESS_TEMP_DIR" && find "$_line" -type f ) >> "$_out"
    elif [ -f "$_src" ]; then
      printf '%s\n' "$_line" >> "$_out"
    else
      log_warn "MANIFEST entry '$_line' not found in fetched clone — skipping."
    fi
  done < "$_manifest"
}

# ── Interactive per-file conflict prompt ─────────────────────────────────────
# Sets CONFLICT_DECISION to: o (overwrite) | s (skip) | eof (no input available).
# Reads from the script's stdin so piped answers (tests) and a real TTY both work.
# On EOF (e.g. stdin is /dev/null) it does NOT guess — returns "eof" so the caller
# skips the file and flags the run for an interactive re-run.
CONFLICT_DECISION=""
prompt_conflict() {
  _cur="$1"   # working-copy path
  _fresh="$2" # freshly-fetched upstream path
  while :; do
    printf '  Resolve: [o]verwrite / [s]kip / [v]iew diff again: ' >&2
    if ! IFS= read -r _ans; then
      printf '\n' >&2
      CONFLICT_DECISION="eof"
      return 0
    fi
    case "$_ans" in
      o|O|overwrite) CONFLICT_DECISION="o"; return 0 ;;
      s|S|skip)      CONFLICT_DECISION="s"; return 0 ;;
      v|V|view)      diff -u "$_cur" "$_fresh" >&2 || true ;;
      *)             printf '  Please enter o, s, or v.\n' >&2 ;;
    esac
  done
}

# ── Compare + update every fresh file, recording final hashes to a decisions file
# Writes key<TAB>hash lines to $_decisions and each handled key to $_processed.
# Sets UNRESOLVED to the count of conflicts left unresolved due to no input.
UNRESOLVED=0
process_files() {
  _lock="$1"
  _list="$2"
  _decisions="$3"
  _processed="$4"
  UNRESOLVED=0

  # Loop over the file list via fd 3 so fd 0 (stdin) stays free for prompts.
  while IFS= read -r _rel <&3; do
    [ -n "$_rel" ] || continue
    _src="$HARNESS_TEMP_DIR/$_rel"
    _dst="./$_rel"
    _fresh_hash=$(compute_file_hash "$_src")
    printf '%s\n' "$_rel" >> "$_processed"

    # New file added upstream since install — install directly, no conflict.
    if [ ! -e "$_dst" ]; then
      install_file "$_src" "$_dst"
      printf '%s\t%s\n' "$_rel" "$_fresh_hash" >> "$_decisions"
      log_info "new file installed: $_rel"
      continue
    fi

    _cur_hash=$(compute_file_hash "$_dst")
    _rec_hash=$(lookup_lock_hash "$_lock" "$_rel")

    # Untouched since install (hash still matches the lock) — overwrite silently.
    if [ -n "$_rec_hash" ] && [ "$_cur_hash" = "$_rec_hash" ]; then
      install_file "$_src" "$_dst"
      printf '%s\t%s\n' "$_rel" "$_fresh_hash" >> "$_decisions"
      continue
    fi

    # No real diff (current content already equals upstream) — no-op overwrite,
    # nothing to resolve. Covers "edited back to upstream" and "identical but
    # never tracked" without a pointless empty-diff prompt.
    if [ "$_cur_hash" = "$_fresh_hash" ]; then
      install_file "$_src" "$_dst"
      printf '%s\t%s\n' "$_rel" "$_fresh_hash" >> "$_decisions"
      continue
    fi

    # Real conflict: user customized this file (or it was never tracked and the
    # content genuinely differs). Show the diff and prompt.
    if [ -n "$_rec_hash" ]; then
      log_warn "conflict: '$_rel' has local changes since install"
    else
      log_warn "conflict: '$_rel' is not recorded in the lock and differs from upstream"
    fi
    log_info "diff (current vs upstream) for $_rel:"
    diff -u "$_dst" "$_src" >&2 || true

    prompt_conflict "$_dst" "$_src"
    case "$CONFLICT_DECISION" in
      o)
        install_file "$_src" "$_dst"
        printf '%s\t%s\n' "$_rel" "$_fresh_hash" >> "$_decisions"
        log_info "overwrote: $_rel"
        ;;
      s)
        # Keep the local file; preserve its prior recorded hash if it had one.
        if [ -n "$_rec_hash" ]; then
          printf '%s\t%s\n' "$_rel" "$_rec_hash" >> "$_decisions"
        fi
        log_info "skipped: $_rel (kept your local version)"
        ;;
      eof)
        UNRESOLVED=$((UNRESOLVED + 1))
        if [ -n "$_rec_hash" ]; then
          printf '%s\t%s\n' "$_rel" "$_rec_hash" >> "$_decisions"
        fi
        log_warn "no input for '$_rel' — left your local version untouched; re-run interactively to resolve."
        ;;
    esac
  done 3< "$_list"
}

# ── Preserve lock entries not seen in this run (e.g. CLAUDE.md, removed-upstream)
# Appends untouched prior entries to the decisions file so the rewritten lock
# keeps them. Warns when an entry that WAS under a MANIFEST path is gone upstream.
carry_over_unprocessed() {
  _lock="$1"
  _manifest="$2"
  _decisions="$3"
  _processed="$4"

  extract_lock_pairs "$_lock" | while IFS='	' read -r _k _h; do
    [ -n "$_k" ] || continue
    if grep -Fxq "$_k" "$_processed" 2>/dev/null; then
      continue
    fi
    printf '%s\t%s\n' "$_k" "$_h" >> "$_decisions"
    if is_under_manifest "$_k" "$_manifest"; then
      log_warn "upstream no longer ships '$_k' — leaving your local copy untouched (not deleted)."
    fi
  done
}

# ── Rewrite .claude/harness-lock.json from the decisions file ────────────────
# Same JSON shape setup.sh writes: { "files": { "<path>": "<hash>", ... } }.
write_new_lock() {
  _decisions="$1"
  _lock="$2"
  _sorted="$HARNESS_TEMP_DIR/.update-lock-sorted"
  # Unique by full line; keys are already unique so this only stabilizes order.
  LC_ALL=C sort -u "$_decisions" > "$_sorted"

  {
    printf '{\n  "files": {\n'
    _first=1
    while IFS='	' read -r _k _h; do
      [ -n "$_k" ] || continue
      _esc=$(printf '%s' "$_k" | sed 's/\\/\\\\/g; s/"/\\"/g')
      if [ "$_first" -eq 1 ]; then
        _first=0
      else
        printf ',\n'
      fi
      printf '    "%s": "%s"' "$_esc" "$_h"
    done < "$_sorted"
    printf '\n  }\n}\n'
  } > "$_lock"
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
  check_git
  check_target_is_git_repo   # BEFORE any fetch/write (non-git => reject, no side effects)
  resolve_repo_url

  lock="./.claude/harness-lock.json"
  if [ ! -f "$lock" ]; then
    log_error "No .claude/harness-lock.json found in this repo. Run setup.sh first to install the harness."
    exit 1
  fi

  # Fetch fresh upstream into a temp clone (discarded on exit by the fetch lib).
  harness_make_temp_dir              # sets $HARNESS_TEMP_DIR, registers cleanup traps
  harness_fetch "$SUPERVISOR_REPO" "$HARNESS_TEMP_DIR"

  manifest="$HARNESS_TEMP_DIR/MANIFEST"
  if [ ! -f "$manifest" ]; then
    log_error "MANIFEST not found in fetched harness. The repo may be corrupt."
    exit 1
  fi

  # Refuse outright on an old symlink-model install (touches nothing in target).
  detect_symlinks "$manifest"

  # Working temp files live under HARNESS_TEMP_DIR so the fetch lib cleans them up.
  decisions="$HARNESS_TEMP_DIR/.update-decisions"
  processed="$HARNESS_TEMP_DIR/.update-processed"
  fresh_list="$HARNESS_TEMP_DIR/.update-fresh-list"
  : > "$decisions"; : > "$processed"

  build_fresh_file_list "$manifest" "$fresh_list"
  process_files "$lock" "$fresh_list" "$decisions" "$processed"
  carry_over_unprocessed "$lock" "$manifest" "$decisions" "$processed"
  write_new_lock "$decisions" "$lock"

  log_info "Update complete. Re-recorded $lock"

  if [ "$UNRESOLVED" -gt 0 ]; then
    log_error "$UNRESOLVED conflict(s) could not be resolved (no interactive input). Re-run 'bash update.sh' in a terminal to resolve them."
    exit 2
  fi
}

main
