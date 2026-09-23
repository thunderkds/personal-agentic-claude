#!/bin/sh
# setup.sh — Easy Kit installer (direct-to-repo, ADR-0001)
# Usage: curl -fsSL …/setup.sh | sh   (takes no options — everything is a menu, T115)
#
# Fresh-install model (ADR-0001): fetch the harness into a temp clone via
# lib/harness-fetch.sh, copy every MANIFEST path + CLAUDE.md/CLAUDE_LEGACY.md into
# the CURRENT git repository as real files (always overwriting), discard the temp
# clone, and record installed-file content hashes to .claude/harness-lock.json so
# update.sh can later distinguish "untouched" from "user-customized" files.
#
# Env overrides:
#   SUPERVISOR_REPO   — full git URL to fetch (defaults to the GITHUB_USERNAME repo)
#   GITHUB_USERNAME   — install from a fork (default: thunderkds)
#
# CLI selection (T097 / DDR-0007, menu since T115): on Install / Reinstall the
# user picks which CLIs this project receives directories for from a numbered
# list; a project only ever gains vendor directories the user picked. Update
# asks nothing and keeps every CLI already present.
set -e

# ── Locate this script so we can source its co-located fetch library ─────────
# SETUP_SH_DIR override: lets a test that sources this file for its function
# definitions point at the real checkout, so `dirname $0` (which resolves to the
# test's own dir when sourced) does not misfire the piped-install bootstrap.
SCRIPT_DIR="${SETUP_SH_DIR:-$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)}"

# ── Logging helpers (TTY-aware color, plain-text fallback) ────────────────────
GREEN=''; YELLOW=''; RED=''; RESET=''
if [ -t 1 ]; then
  GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; RESET='\033[0m'
fi
log_info()  { printf "${GREEN}[info]${RESET}  %s\n"  "$*"; }
log_warn()  { printf "${YELLOW}[warn]${RESET}  %s\n" "$*" >&2; }
log_error() { printf "${RED}[error]${RESET} %s\n"   "$*" >&2; }

# ── Easy Kit takes no options (T115, ADR-0002 "Removed") ──────────────────────
# Checked before anything else, the bootstrap clone included, so a stale
# `--harness codex` from old docs fails loudly with nothing written.
if [ "$#" -gt 0 ] && [ -z "${SETUP_SH_DEFINE_ONLY:-}" ]; then
  log_error "Easy Kit takes no options (got: $*). Run it and choose from the menus:"
  log_error "  curl -fsSL https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/setup.sh | sh"
  exit 1
fi

# ── Source the shared temp-clone-copy-discard fetch library (T031) ───────────
HARNESS_LIB="$SCRIPT_DIR/lib/harness-fetch.sh"
if [ ! -f "$HARNESS_LIB" ]; then
  # Piped install (curl | sh): $0 has no real file location, so SCRIPT_DIR
  # above resolved to the caller's cwd, not anywhere lib/harness-fetch.sh
  # exists (T038). Bootstrap: clone a full checkout with plain git (the
  # library that would normally do this isn't sourced yet), then re-invoke
  # the REAL setup.sh from that checkout with all original args. Not `exec`
  # — a regular call, so we can clean up the bootstrap dir afterward and
  # propagate the real invocation's exit code.
  log_info "No local checkout detected (likely a piped 'curl | sh' install) — bootstrapping a full checkout first."
  BOOTSTRAP_REPO="${SUPERVISOR_REPO:-https://github.com/${GITHUB_USERNAME:-thunderkds}/personal-agentic-claude.git}"
  BOOTSTRAP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/harness-bootstrap.XXXXXX") || {
    log_error "Failed to create a temp directory for the bootstrap clone."
    exit 1
  }
  if ! git clone --depth 1 "$BOOTSTRAP_REPO" "$BOOTSTRAP_DIR" >/dev/null 2>&1; then
    log_error "Bootstrap clone of '$BOOTSTRAP_REPO' failed. Check network connectivity and the URL."
    rm -rf "$BOOTSTRAP_DIR"
    exit 1
  fi
  # `|| _bootstrap_rc=$?` is required (not just `; _bootstrap_rc=$?` on the next
  # line) — under `set -e`, a plain failing command exits the script
  # immediately, before the next line ever runs, which would skip both the
  # exit-code capture AND the rm -rf cleanup below.
  _bootstrap_rc=0
  SUPERVISOR_REPO="$BOOTSTRAP_REPO" sh "$BOOTSTRAP_DIR/setup.sh" "$@" || _bootstrap_rc=$?
  rm -rf "$BOOTSTRAP_DIR"
  exit "$_bootstrap_rc"
fi
# shellcheck source=lib/harness-fetch.sh
. "$HARNESS_LIB"
# The Update / Reinstall actions (T114: moved here from update.sh's body).
# shellcheck source=lib/harness-update.sh
. "$SCRIPT_DIR/lib/harness-update.sh"

# ── Resolve GitHub username → repo URL ───────────────────────────────────────
# Honors a pre-set SUPERVISOR_REPO (fork installs and offline/file:// testing);
# otherwise builds the canonical URL from GITHUB_USERNAME.
resolve_repo_url() {
  if [ -z "${SUPERVISOR_REPO:-}" ]; then
    GITHUB_USERNAME="${GITHUB_USERNAME:-thunderkds}"
    SUPERVISOR_REPO="https://github.com/${GITHUB_USERNAME}/personal-agentic-claude.git"
  fi
  log_info "Using repo: $SUPERVISOR_REPO"
}

# ── Selections ────────────────────────────────────────────────────────────────
# The CLIs to set up, as internal names; chosen by prompt_clis.
HARNESSES=""
VALID_HARNESSES="claude codex"

# EASYKIT_ACTION is an internal seam for update.sh, the thin alias (T114). It is
# not a user option and is never documented; an unknown value is an error.
case "${EASYKIT_ACTION:-}" in
  ''|update) ;;
  *) log_error "Unknown EASYKIT_ACTION '$EASYKIT_ACTION'."; exit 1 ;;
esac

# ── Prerequisite: git installed ──────────────────────────────────────────────
check_git() {
  if ! command -v git >/dev/null 2>&1; then
    log_error "Git is required but not installed. Install Git and re-run setup.sh."
    exit 1
  fi
}

# ── Prerequisite: the target (current) directory must be a git repository ─────
# Under the direct-install model, the working repo's own git history is the only
# undo mechanism (no symlink is left untouched), so this check is load-bearing.
# Run BEFORE any file is written.
check_target_is_git_repo() {
  if ! git -C . rev-parse --git-dir >/dev/null 2>&1; then
    log_error "The current directory is not a git repository. Run 'git init' first — setup.sh copies real files in, and git history is your only undo path."
    exit 1
  fi
}

# ── Fetch the harness into a temp clone (discarded on exit by the fetch lib) ──
fetch_harness() {
  harness_make_temp_dir              # sets $HARNESS_TEMP_DIR, registers cleanup traps
  harness_fetch "$SUPERVISOR_REPO" "$HARNESS_TEMP_DIR"
}

# ── Point .claude/{skills,agents} at the plain-root canon ────────────────────
# The kit's canon lives at skills/ and agents/ so no harness is structurally
# privileged, but Claude Code only discovers them under .claude/. These links
# bridge the two. Targets are RELATIVE (../skills, ../agents): an absolute
# target would break git worktrees, which each need the link to resolve inside
# their own checkout rather than back into the main one.
install_canon_symlinks() {
  harness_install_canon_symlinks .
}

# ── Was this CLI picked on this run? ─────────────────────────────────────
harness_selected() {
  for _h in $HARNESSES; do
    [ "$_h" = "$1" ] && return 0
  done
  return 1
}

# ── Ensure a .gitignore entry exists in the target project ───────────────────
# Projected vendor directories are GENERATED from the canon this install just
# copied, so they are reproducible by re-running setup.sh and must not be
# committed (DDR-0007: "canon is committed; projections are not"). Idempotent:
# an entry already present is left alone, so re-running never duplicates a line.
ensure_gitignore_entry() {
  _entry="$1"
  _reason="$2"
  [ -f ./.gitignore ] || : > ./.gitignore
  if grep -Fxq "$_entry" ./.gitignore 2>/dev/null; then
    return
  fi
  # Keep a trailing newline before appending so an entry is never glued onto an
  # unterminated last line.
  [ -s ./.gitignore ] && [ -n "$(tail -c 1 ./.gitignore)" ] && printf '\n' >> ./.gitignore
  printf '\n# %s\n%s\n' "$_reason" "$_entry" >> ./.gitignore
  log_info "Added '$_entry' to .gitignore ($_reason)."
}

# ── Project the canon into each selected non-Claude harness ──────────────────
# `claude` is deliberately NOT handled here: .claude/{skills,agents} are relative
# symlinks onto the plain-root canon (install_canon_symlinks), not copies.
# Everything else is a real-copy projection driven by MANIFEST's destination
# column, so adding a harness is a MANIFEST entry rather than a code change.
install_harness_projections() {
  _manifest="$1"
  for _h in $HARNESSES; do
    [ "$_h" = "claude" ] && continue
    log_info "Setting up $(cli_names "$_h"): copying the kit's skills into its folder."
    harness_project_manifest "$HARNESS_TEMP_DIR" "." "$_manifest" "$_h" || {
      log_error "Setup aborted: setting up $(cli_names "$_h") failed. The target tree may be partial."
      exit 2
    }
    case "$_h" in
      codex) ensure_gitignore_entry ".codex/skills/" "generated by Easy Kit for Codex (T097); regenerate, do not commit" ;;
    esac
  done
}

# ── Terminal input (T114) ────────────────────────────────────────────────────
# Every prompt reads /dev/tty, never stdin: under `curl | sh`, stdin IS the
# script, so a prompt reading it would never reach the user. The probe opens
# /dev/tty in a subshell because the device can exist and still be unopenable
# (no controlling terminal: CI, containers, `ssh` without -t, `setsid`).
TTY_OK=0
tty_probe() {
  if ( : </dev/tty ) 2>/dev/null; then TTY_OK=1; else TTY_OK=0; fi
}

# Read one line from the terminal into TTY_ANSWER. Returns non-zero — "no
# answer" — when there is no usable terminal or the user sent EOF; every caller
# then takes its safe path instead of guessing.
TTY_ANSWER=""
tty_read() {
  TTY_ANSWER=""
  [ "$TTY_OK" -eq 1 ] || return 1
  IFS= read -r TTY_ANSWER 2>/dev/null </dev/tty
}

# ── Menu: which CLIs (T115) ──────────────────────────────────────────────────
# Pre-selection for Install: every CLI found on PATH (a real executable — the
# script runs in sh, so shell aliases/functions never count); Claude Code when
# neither is found. Reinstall pre-selects what the project already has instead,
# so Enter never adds a CLI the project did not have.
default_clis() {
  _dc_manifest="$1"
  _dc=""
  if [ "$ACTION" = "reinstall" ]; then
    _dc_saved="$HARNESSES"; HARNESSES=""
    resolve_projection_harnesses "$_dc_manifest"
    HARNESSES="$_dc_saved"
    _dc="$PROJECTION_HARNESSES"
  fi
  if [ -z "$_dc" ]; then
    for _h in $VALID_HARNESSES; do
      command -v "$_h" >/dev/null 2>&1 && _dc="$_dc $_h"
    done
  fi
  [ -n "$_dc" ] || _dc="claude"
  printf '%s' "${_dc# }"
}

# Menu number <-> internal name, in VALID_HARNESSES order.
cli_numbers() {
  _cnum=""
  _i=0
  for _v in $VALID_HARNESSES; do
    _i=$((_i + 1))
    for _h in $1; do [ "$_h" = "$_v" ] && _cnum="$_cnum $_i"; done
  done
  printf '%s' "${_cnum# }"
}

# Sets HARNESSES. Enter keeps the pre-selection; numbers may be separated by
# spaces or commas ("1 2", "1,2" — T108's lesson). A line with separators but no
# number re-prompts "pick at least one"; anything else unknown re-prompts. EOF
# at the terminal cancels, as the action menu does. No terminal: the default.
prompt_clis() {
  _pc_default=$(default_clis "$1")
  HARNESSES="$_pc_default"
  [ "$TTY_OK" -eq 1 ] || return 0
  printf '\nWhich CLIs should Easy Kit set up?\n'
  printf '  1) Claude Code  2) Codex\n'
  while :; do
    printf 'Choose one or more [%s]: ' "$(cli_numbers "$_pc_default")"
    if ! tty_read; then
      printf '\n'
      cancel_run
    fi
    [ -n "$TTY_ANSWER" ] && [ -z "$(printf '%s' "$TTY_ANSWER" | tr -d ' \t')" ] && TTY_ANSWER=""
    [ -n "$TTY_ANSWER" ] || return 0
    _pc_picked=""
    _pc_bad=0
    # `set -f` for the split: the answer is unquoted here so it word-splits,
    # which also makes it glob. Without this, typing `*` in a project that
    # happens to hold files named `1` or `2` expands to those names and is
    # accepted as a selection instead of re-prompting.
    set -f
    for _pc_n in $(printf '%s' "$TTY_ANSWER" | tr ',' ' '); do
      case "$_pc_n" in
        1) _pc_picked="$_pc_picked claude" ;;
        2) _pc_picked="$_pc_picked codex" ;;
        *) _pc_bad=1 ;;
      esac
    done
    set +f
    if [ "$_pc_bad" -eq 1 ]; then
      printf 'Please enter 1, 2 or both (e.g. 1 2).\n'
    elif [ -z "$_pc_picked" ]; then
      printf 'Pick at least one CLI.\n'
    else
      # Menu order, each once, whatever order or repeats were typed.
      HARNESSES=""
      for _v in $VALID_HARNESSES; do
        case " $_pc_picked " in *" $_v "*) HARNESSES="$HARNESSES $_v" ;; esac
      done
      HARNESSES="${HARNESSES# }"
      return 0
    fi
  done
}

# ── Menu: project type (T115 wording; was greenfield / brownfield) ───────────
# Defaults to New project when there is no terminal (e.g. CI, `setsid`) or at EOF.
prompt_mode() {
  mode_choice=1
  if [ "$TTY_OK" -eq 1 ]; then
    printf '\nIs this a new or an existing project?\n'
    printf '  1) New project\n'
    printf '  2) Existing / legacy project\n'
    while :; do
      printf 'Choose [1]: '
      tty_read || { printf '\n'; break; }
      case "$TTY_ANSWER" in
        ''|1) mode_choice=1; break ;;
        2)    mode_choice=2; break ;;
      esac
      printf 'Please enter 1 or 2.\n'
    done
  fi

  case "$mode_choice" in
    2) CLAUDE_SRC="CLAUDE_LEGACY.md" ;;
    *) CLAUDE_SRC="CLAUDE.md" ;;
  esac
}

# ── Install CLAUDE.md as a real copy (a differing existing one is backed up) ──
install_claude() {
  src="$HARNESS_TEMP_DIR/$CLAUDE_SRC"
  dst="./CLAUDE.md"

  if [ ! -e "$src" ]; then
    log_error "Source '$CLAUDE_SRC' not found in the fetched Easy Kit. Aborting."
    exit 1
  fi

  parent="$(dirname "$dst")"
  [ -d "$parent" ] || mkdir -p "$parent"
  harness_backup_path "$src" "$dst" || exit 1
  { [ -e "$dst" ] || [ -L "$dst" ]; } && rm -rf "$dst"
  cp "$src" "$dst"
}

# ── Settings merge: loud refusal (T111) ──────────────────────────────────────
# Set when the kit's hooks could NOT be merged into the project's settings.json.
# The run still finishes the rest of its work; main() exits 2 at the end.
SETTINGS_FAILED=0

# Print the exact block the user must add by hand, and record the failure.
# Writes nothing — the project's settings.json is left byte-identical.
settings_merge_refused() {
  _reason="$1"
  _src="$2"
  SETTINGS_FAILED=1
  log_error "Could not merge Easy Kit hooks into ./.claude/settings.json: $_reason"
  log_error "Nothing was written. Add the \"hooks\" entries below to ./.claude/settings.json by hand (keep your own entries), then re-run:"
  cat "$_src" >&2
}

# ── Merge the kit's hook entries into an existing settings.json (ADR-0002) ────
# Runs lib/merge-settings.py from the TEMP CLONE, so the merge logic always
# pairs with the settings file it is merging and is never installed into the
# user's project. python3 is a hard prerequisite: every wired hook runs as
# `python3 …`, so an install without it produces no working hooks anyway.
merge_settings() {
  _src="$1"
  _dst="$2"
  _merge="$HARNESS_TEMP_DIR/lib/merge-settings.py"

  if [ ! -f "$_merge" ]; then
    settings_merge_refused "the fetched Easy Kit has no lib/merge-settings.py" "$_src"
    return
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    settings_merge_refused "python3 is not on PATH (every kit hook runs as 'python3 …', so it is a hard prerequisite)" "$_src"
    return
  fi
  if ! python3 "$_merge" "$_src" "$_dst" "."; then
    settings_merge_refused "the merge refused this file (reason above)" "$_src"
    return
  fi
  log_info "Merged Easy Kit hooks into $_dst (your permissions and your own hook entries are kept)."
}

# ── Install settings.json (hook wiring) ──────────────────────────────────────
# No settings file yet: copy the kit's, exactly as before. One already there:
# MERGE into it (ADR-0002) instead of returning silently — the pre-T111 early
# return left every project that had a settings.json with zero kit hooks wired
# and said nothing about it.
install_settings() {
  src="$HARNESS_TEMP_DIR/.claude/settings.json"
  dst="./.claude/settings.json"

  if [ ! -e "$src" ]; then
    log_warn ".claude/settings.json not found in the fetched Easy Kit — hooks will not be wired."
    return
  fi
  if [ -e "$dst" ] || [ -L "$dst" ]; then
    merge_settings "$src" "$dst"
    return
  fi
  [ -d ./.claude ] || mkdir -p ./.claude
  cp "$src" "$dst"
  log_info "Installed .claude/settings.json (copy). Restart Claude Code to activate hooks."
}

# ── Content hash of a single file (permission-independent: content only) ──────
compute_file_hash() {
  _f="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$_f" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$_f" | awk '{print $1}'
  else
    log_error "Neither sha256sum nor shasum is available; cannot write harness-lock.json."
    exit 1
  fi
}

# ── Write .claude/harness-lock.json ──────────────────────────────────────────
# Records one content-hash entry per installed file, keyed by repo-relative path.
# Directories listed in MANIFEST are expanded to their files so update.sh (T033)
# can compare and prompt per-file. Hashes are content-only (chmod-safe).
# Arg $1: path to the MANIFEST in the temp clone.
write_harness_lock() {
  _manifest="$1"
  _lock="./.claude/harness-lock.json"
  [ -d ./.claude ] || mkdir -p ./.claude

  _files_list="$(mktemp "${TMPDIR:-/tmp}/harness-lock-files.XXXXXX")"

  # Enumerate every installed file: expand each MANIFEST dir to its files, add
  # the installed CLAUDE.md. Strip the leading ./, sort stably, de-duplicate.
  {
    # shellcheck disable=SC2094  # read-only lookups of the MANIFEST the loop is reading
    while IFS= read -r _line; do
      # Field 1 only — the optional destination column (T097) is not a path, and
      # projected vendor dirs are generated + gitignored, never lock-tracked.
      _line=$(harness_manifest_path "$_line")
      [ -n "$_line" ] || continue
      [ -e "./$_line" ] || continue
      if [ -d "./$_line" ]; then
        find "./$_line" -type f | while IFS= read -r _f; do
          harness_is_excluded "$_manifest" "${_f#./}" || printf '%s\n' "$_f"
        done
      elif [ -f "./$_line" ]; then
        printf '%s\n' "./$_line"
      fi
    done < "$_manifest"
    [ -f ./CLAUDE.md ] && printf '%s\n' ./CLAUDE.md
  } | sed 's|^\./||' | LC_ALL=C sort -u > "$_files_list"

  _count=$(wc -l < "$_files_list" | tr -d ' ')

  {
    printf '{\n'
    _esc_src=$(printf '%s' "$CLAUDE_SRC" | sed 's/\\/\\\\/g; s/"/\\"/g')
    printf '  "claude_md_source": "%s",\n' "$_esc_src"
    printf '  "files": {\n'
    _first=1
    while IFS= read -r _rel; do
      [ -n "$_rel" ] || continue
      _hash=$(compute_file_hash "./$_rel")
      # JSON-escape backslash then double-quote in the path key.
      _esc=$(printf '%s' "$_rel" | sed 's/\\/\\\\/g; s/"/\\"/g')
      if [ "$_first" -eq 1 ]; then
        _first=0
      else
        printf ',\n'
      fi
      printf '    "%s": "%s"' "$_esc" "$_hash"
    done < "$_files_list"
    printf '\n  }\n}\n'
  } > "$_lock"

  rm -f "$_files_list"
  log_info "Wrote $_lock ($_count file hashes)."
}

# ── Scaffold project-specific folders ────────────────────────────────────────
scaffold_project() {
  [ -d ./tasks ]  || mkdir ./tasks
  [ -d ./memory ] || mkdir ./memory
  if [ ! -f ./memory/MEMORY.md ]; then
    cat > ./memory/MEMORY.md <<'EOF'
# MEMORY.md — Hot-Tier Memory Index

> **Rules**: Supervisor-only writes. Max 42,000 characters — a ratchet: `/compact-memory` may lower
> it, never raise it to fit growth. One-line summaries + links to cold files.
> Passed to every sub-agent as a path to read; the contents are not pasted into the spawn prompt.
> Updated by the Supervisor — prompted by the PostToolUse hook on `git push` / `git merge` (diff-driven pass), or via the `/compact-memory` skill.

---

## Memory Architecture

- [decisions.md](decisions.md) — code + infra architectural decisions (the "why")
- [glossary.md](glossary.md) — canonical biz domain terms and core domain models
- [learnings.md](learnings.md) — specs/requirement clarifications, patterns, gotchas

---

## Index

<!-- Format: - [Title](cold-file.md#section) — one-line summary.
     Target ≤150 chars/entry. Advisory: reported by the size test, never enforced.
     The enforced gate is the 42,000-character whole-file budget above. -->
EOF
  fi
  if [ ! -f ./memory/decisions.md ]; then
    cat > ./memory/decisions.md <<'EOF'
# decisions.md — Cold Tier: Architectural & Infrastructure Decisions

> **Rules**: Supervisor-only writes. Each entry: `### YYYY-MM-DD — Title`, then **Decision**, **Why**, and **Files** (cite paths — the diff-driven pass greps this file by changed file path).

## Architecture

## Infrastructure
EOF
  fi
  if [ ! -f ./memory/glossary.md ]; then
    cat > ./memory/glossary.md <<'EOF'
# glossary.md — Cold Tier: Domain Terms & Domain Models

> **Rules**: Supervisor-only writes. One canonical definition per term — update in place, never duplicate. Domain Models section is populated at Stage 1 step 7 (Core Domain Models scan) and confirmed by the user.

## Domain Terms

## Domain Models
EOF
  fi
  if [ ! -f ./memory/learnings.md ]; then
    cat > ./memory/learnings.md <<'EOF'
# learnings.md — Cold Tier: Clarifications, Patterns & Gotchas

> **Rules**: Supervisor-only writes. Each entry dated (`YYYY-MM-DD`) and citing the file/task it came from (the diff-driven pass greps this file by changed file path).

## Requirement Clarifications

## Patterns

## Gotchas
EOF
  fi
  mkdir -p ./memory/learning-records
  touch ./memory/learning-records/.gitkeep
}

# ── Action menu, plan screen, confirmation (T114, ADR-0002) ─────────────────
LOCK_FILE="./.claude/harness-lock.json"
ACTION=""

# User-facing names for the selected CLIs ("Claude Code, Codex").
cli_names() {
  _cn=""
  for _h in ${1-$HARNESSES}; do
    case "$_h" in
      claude) _cn="$_cn, Claude Code" ;;
      codex)  _cn="$_cn, Codex" ;;
      *)      _cn="$_cn, $_h" ;;
    esac
  done
  printf '%s' "${_cn#, }"
}

# Plan lines for the CLIs (Install and Reinstall). Reinstall never removes a CLI
# the project already has: one present but not picked is kept and refreshed
# (the Update presence rule, T098), and the plan says so — never a silent orphan.
plan_cli_lines() {
  printf '  - CLIs: %s\n' "$(cli_names)"
  [ "$ACTION" = "reinstall" ] || return 0
  _pk_saved="$HARNESSES"; HARNESSES=""
  resolve_projection_harnesses "$1"
  HARNESSES="$_pk_saved"
  _pk_kept=""
  for _h in $PROJECTION_HARNESSES; do
    case " $HARNESSES " in *" $_h "*) ;; *) _pk_kept="$_pk_kept $_h" ;; esac
  done
  [ -n "$_pk_kept" ] || return 0
  printf '  - Already set up here, not picked, kept and refreshed: %s (to remove one, delete its folder).\n' "$(cli_names "$_pk_kept")"
}

project_type_label() {
  case "$CLAUDE_SRC" in
    CLAUDE_LEGACY.md) printf 'Existing / legacy project (CLAUDE_LEGACY.md)' ;;
    *)                printf 'New project (CLAUDE.md)' ;;
  esac
}

# Sets ACTION to install | update | reinstall | cancel ($1: the MANIFEST). Enter takes the safe
# default (1). Invalid input re-prompts; EOF at a terminal cancels. With no
# terminal there is no menu: the safe default is printed and taken, and
# Reinstall is never chosen.
choose_action() {
  if [ "$TTY_OK" -ne 1 ]; then
    if [ -f "$LOCK_FILE" ]; then
      log_info "No terminal — updating, keeping your edits (any file you edited is left as it is; re-run in a terminal to resolve)."
      ACTION=update
    else
      log_info "No terminal — installing with the defaults: $(cli_names "$(default_clis "$1")"), New project (CLAUDE.md)."
      ACTION=install
    fi
    return
  fi
  printf '\n'
  if [ -f "$LOCK_FILE" ]; then
    printf 'Easy Kit is already installed in %s.\n' "$(pwd)"
    printf '  1) Update (keeps your edits)\n'
    printf '  2) Reinstall (backs up your edits)\n'
    printf '  3) Cancel\n'
  else
    printf 'Easy Kit is not installed in %s yet.\n' "$(pwd)"
    printf '  1) Install\n'
    printf '  2) Cancel\n'
  fi
  while :; do
    printf 'Choose [1]: '
    if ! tty_read; then
      printf '\n'
      ACTION=cancel
      return
    fi
    if [ -f "$LOCK_FILE" ]; then
      case "$TTY_ANSWER" in
        ''|1) ACTION=update; return ;;
        2)    ACTION=reinstall; return ;;
        3)    ACTION=cancel; return ;;
      esac
      printf 'Please enter 1, 2 or 3.\n'
    else
      case "$TTY_ANSWER" in
        ''|1) ACTION=install; return ;;
        2)    ACTION=cancel; return ;;
      esac
      printf 'Please enter 1 or 2.\n'
    fi
  done
}

# Returns 0 to act, 1 to go back to the action menu. EOF at a terminal cancels
# (exit 0, nothing written). With no terminal the plan was already printed and
# the safe default proceeds.
confirm_plan() {
  if [ "$TTY_OK" -ne 1 ]; then
    log_info "No terminal — proceeding with the plan above."
    return 0
  fi
  while :; do
    printf 'Proceed? [Y/n] '
    if ! tty_read; then
      printf '\n'
      cancel_run
    fi
    case "$TTY_ANSWER" in
      ''|y|Y|yes|Yes) return 0 ;;
      n|N|no|No)      return 1 ;;
      *)              printf 'Please enter y or n.\n' ;;
    esac
  done
}

cancel_run() {
  log_info "Cancelled — nothing was changed."
  exit 0
}

# Would the install move this existing path aside? The same test
# harness_backup_path applies (a link always; otherwise only when the content
# differs), with the paths a MANIFEST `!` line keeps out removed from BOTH sides
# first, because the install never touches them (T113).
install_would_back_up() {
  _iw_src="$1"
  _iw_dst="$2"
  _iw_rel="$3"
  _iw_manifest="$4"
  [ -e "$_iw_dst" ] || [ -L "$_iw_dst" ] || return 1
  [ -L "$_iw_dst" ] && return 0
  if [ -f "$_iw_src" ] && [ -f "$_iw_dst" ]; then
    cmp -s "$_iw_src" "$_iw_dst" && return 1
    return 0
  fi
  { [ -d "$_iw_src" ] && [ -d "$_iw_dst" ]; } || return 0
  _iw_subs=$(_harness_exclusions_under "$_iw_manifest" "$_iw_rel")
  [ -n "$_iw_subs" ] || { diff -rq "$_iw_src" "$_iw_dst" >/dev/null 2>&1 && return 1; return 0; }
  _iw_work="$HARNESS_TEMP_DIR/.plan-excl"
  rm -rf "$_iw_work"; mkdir -p "$_iw_work"
  cp -r "$_iw_src" "$_iw_work/kit"; cp -r "$_iw_dst" "$_iw_work/project"
  for _iw_sub in $_iw_subs; do
    rm -rf "$_iw_work/kit/$_iw_sub" "$_iw_work/project/$_iw_sub"
  done
  _iw_rc=0
  diff -rq "$_iw_work/kit" "$_iw_work/project" >/dev/null 2>&1 || _iw_rc=1
  rm -rf "$_iw_work"
  [ "$_iw_rc" -eq 1 ]
}

plan_install() {
  _manifest="$1"
  _p_bk="$HARNESS_TEMP_DIR/.plan-install-backups"
  : > "$_p_bk"
  # shellcheck disable=SC2094  # read-only lookups of the MANIFEST the loop is reading
  while IFS= read -r _line; do
    _line=$(harness_manifest_path "$_line")
    [ -n "$_line" ] || continue
    [ -e "$HARNESS_TEMP_DIR/$_line" ] || continue
    harness_is_excluded "$_manifest" "$_line" && continue
    if install_would_back_up "$HARNESS_TEMP_DIR/$_line" "./$_line" "$_line" "$_manifest"; then
      printf '%s -> %s.bak\n' "$_line" "$_line" >> "$_p_bk"
    fi
  done < "$_manifest"
  if install_would_back_up "$HARNESS_TEMP_DIR/$CLAUDE_SRC" ./CLAUDE.md CLAUDE.md "$_manifest"; then
    printf '%s\n' "CLAUDE.md -> CLAUDE.md.bak" >> "$_p_bk"
  fi

  printf '\n'
  printf 'Plan: Install Easy Kit into %s\n' "$(pwd)"
  plan_cli_lines "$_manifest"
  printf '  - Project type: %s\n' "$(project_type_label)"
  printf '  - Copies in: %s, CLAUDE.md\n' "$(grep -v '^[[:space:]]*[#!]' "$_manifest" | awk 'NF {print $1}' | paste -sd, - | sed 's/,/, /g')"
  printf '  - Existing paths that differ from the kit are moved aside first:\n'
  plan_list "$_p_bk" "(none)"
  printf '  - Hooks: .claude/settings.json is created, or Easy Kit entries are merged into yours.\n'
}

# ── Install (the pre-T114 main body, after the fetch) ────────────────────────
run_install() {
  manifest="$1"
  # Copy every MANIFEST path as real files; differing pre-existing paths are
  # moved to <path>.bak[.N] first (T112).
  harness_copy_manifest "$HARNESS_TEMP_DIR" "." "$manifest"

  # Canon now lands at plain root (skills/, agents/); Claude Code still reads
  # .claude/. Skipped when Claude Code was not
  # picked — a project receives only the directories for CLIs it actually uses.
  if harness_selected claude; then
    install_canon_symlinks
  else
    log_info "Claude Code not picked — skipping .claude/{skills,agents} symlinks."
  fi

  # Real-copy projections for every other selected harness (e.g. .codex/skills).
  install_harness_projections "$manifest"

  install_claude
  install_settings
  scaffold_project
  write_harness_lock "$manifest"
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
  check_git
  check_target_is_git_repo   # BEFORE any file write (fetch writes only to temp)
  if [ "${EASYKIT_ACTION:-}" = "update" ] && [ ! -f "$LOCK_FILE" ]; then
    log_error "No .claude/harness-lock.json found in this repo. Easy Kit is not installed here — run setup.sh to install it."
    exit 1
  fi
  resolve_repo_url
  tty_probe

  # The fetch writes only to the temp clone; the plan needs upstream content to
  # say what would be backed up or removed. Every prompt below comes BEFORE any
  # write to the project, so Cancel (or Ctrl-C) leaves it untouched.
  fetch_harness
  manifest="$HARNESS_TEMP_DIR/MANIFEST"
  if [ ! -f "$manifest" ]; then
    log_error "MANIFEST not found in the fetched Easy Kit. The repo may be corrupt."
    exit 1
  fi
  fresh_list="$HARNESS_TEMP_DIR/.fresh-list"
  reinstall_backups="$HARNESS_TEMP_DIR/.reinstall-backups"
  if [ -f "$LOCK_FILE" ]; then
    # Refuse an old symlink-model install before offering any action.
    detect_symlinks "$manifest"
    build_fresh_file_list "$manifest" "$fresh_list"
  fi

  CLAUDE_SRC="CLAUDE.md"
  while :; do
    choose_action "$manifest"
    case "$ACTION" in
      cancel) cancel_run ;;
      update)
        plan_update "$LOCK_FILE" "$manifest" "$fresh_list"
        ;;
      install)
        prompt_clis "$manifest"
        prompt_mode
        plan_install "$manifest"
        ;;
      reinstall)
        prompt_clis "$manifest"
        prompt_mode
        plan_reinstall "$reinstall_backups" "$LOCK_FILE" "$fresh_list" "$manifest"
        ;;
    esac
    confirm_plan && break
  done

  case "$ACTION" in
    update)
      # Update asks for no CLI: it keeps exactly what is present (T098).
      HARNESSES=""
      run_update "$LOCK_FILE" "$manifest" "$fresh_list"
      return
      ;;
    install)
      run_install "$manifest"
      ;;
    reinstall)
      run_reinstall "$LOCK_FILE" "$manifest" "$fresh_list" "$reinstall_backups"
      scaffold_project
      ;;
  esac

  log_info "Setup complete. Easy Kit copied into $(pwd)"
  log_info "CLAUDE source: $CLAUDE_SRC | lock: .claude/harness-lock.json"
  log_info "CLIs: $(cli_names)"
  # packs/ arrives through MANIFEST as a dormant catalog (ADR-0002): nothing
  # links or projects it, so no CLI loads a pack until the Supervisor activates it.
  log_info "Pack catalog: every pack is in packs/, inactive. Your Supervisor recommends packs for this project."

  # The hook merge is the only step allowed to fail without aborting the install
  # (the rest of the kit is still worth having). Report it in the exit code so a
  # script or CI run cannot mistake a hook-less install for a complete one.
  if [ "$SETTINGS_FAILED" -ne 0 ]; then
    log_error "Setup finished, but Easy Kit hooks were NOT wired (see the message above)."
    exit 2
  fi
}

# Run main unless sourced define-only (tests set SETUP_SH_DEFINE_ONLY=1 to load
# the function definitions without executing the installer). Unset — the real
# install path — runs main exactly as before.
[ -n "${SETUP_SH_DEFINE_ONLY:-}" ] || main
