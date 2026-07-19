#!/bin/sh
# setup.sh — Supervisor Agent Deployment System installer (direct-to-repo, ADR-0001)
# Usage: bash setup.sh [--copy] [--pack=<name>]
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
#   SUPERVISOR_PATH   — legacy central-clone location, still used ONLY by packs
#                       (install_pack), which stay out of scope per ADR-0001
set -e

# Legacy central-clone path — referenced only by the (unchanged, out-of-scope)
# pack installer. The base install never creates or requires this directory.
SUPERVISOR_PATH="${SUPERVISOR_PATH:-$HOME/.supervisor}"

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

# ── Parse flags ───────────────────────────────────────────────────────────────
# --copy is retained for backward-compat: the base install is ALWAYS a real copy
# now (no symlink mode), so --copy is a no-op there. It still selects copy-vs-
# symlink for out-of-scope packs (install_pack), whose behavior is unchanged.
USE_COPY=0
PACKS=""  # space-separated list of packs to install (e.g. " mobile data")
for arg in "$@"; do
  case "$arg" in
    --copy) USE_COPY=1 ;;
    --pack=*) pack_val="${arg#--pack=}"; PACKS="$PACKS $pack_val" ;;
    *) log_error "Unknown flag: $arg. Valid flags: --copy, --pack=<name>"; exit 1 ;;
  esac
done

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

# ── Prompt pack selection (interactive only, skipped if --pack= flags given) ──
prompt_packs() {
  # Skip if packs were already specified via --pack= flags
  if [ -n "$PACKS" ]; then
    return
  fi
  # Skip in non-interactive mode
  if [ ! -t 0 ]; then
    log_info "Non-interactive mode: no packs installed. Re-run with --pack=<name> to add packs."
    return
  fi

  printf "[info]  Optional packs extend the core with domain-specific agents and skills.\n"
  printf "        Available packs:\n"
  printf "          1) mobile   — Flutter, React Native, Swift, Kotlin\n"
  printf "          2) data     — Pipelines, notebooks, ETL, dbt\n"
  printf "          3) devops   — Terraform, K8s, CI/CD, Docker\n"
  printf "          4) ai-agent — LLM apps, RAG, MCP servers, multi-agent\n"
  printf "          5) api      — REST/gRPC, OpenAPI, auth flows, SDK design\n"
  printf "        Enter numbers separated by spaces, or press Enter to skip: "
  read -r pack_choices
  for choice in $pack_choices; do
    case "$choice" in
      1) PACKS="$PACKS mobile" ;;
      2) PACKS="$PACKS data" ;;
      3) PACKS="$PACKS devops" ;;
      4) PACKS="$PACKS ai-agent" ;;
      5) PACKS="$PACKS api" ;;
      *) log_warn "Unknown pack choice '$choice' — skipping." ;;
    esac
  done
}

# ── Install a single file using symlink or copy mode ─────────────────────────
# Takes absolute src and relative dst (from project root). Used only by packs
# (install_pack), which stay out of scope per ADR-0001 — do not repurpose for
# the base install, which always copies via harness_copy_manifest.
install_abs() {
  src="$1"
  dst="$2"

  parent="$(dirname "$dst")"
  [ -d "$parent" ] || mkdir -p "$parent"

  if [ $USE_COPY -eq 1 ]; then
    if [ -L "$dst" ]; then
      log_warn "'$dst' is a symlink from a previous install. Remove it manually to switch to --copy mode."
      return
    fi
    if [ -e "$dst" ]; then
      return
    fi
    cp -r "$src" "$dst"
  else
    if [ -L "$dst" ] && [ ! -e "$dst" ]; then
      log_warn "'$dst' is a broken symlink — removing and re-linking."
      rm "$dst"
    elif [ -L "$dst" ]; then
      return
    elif [ -e "$dst" ]; then
      log_warn "'$dst' exists as a real path (not a symlink). Skipping — remove manually to allow symlinking."
      return
    fi
    ln -s "$src" "$dst"
  fi
}

# ── Install a single pack by name ─────────────────────────────────────────────
# OUT OF SCOPE per ADR-0001: packs keep their symlink-from-central-clone behavior
# until a follow-up revisits them. Unchanged from the pre-ADR-0001 file.
install_pack() {
  pack_name="$1"
  pack_dir="$SUPERVISOR_PATH/packs/$pack_name"

  if [ ! -d "$pack_dir" ]; then
    log_warn "Pack '$pack_name' not found in central clone ($pack_dir) — skipping."
    return
  fi

  # Symlink/copy each agent file into .claude/agents/
  if [ -d "$pack_dir/agents" ]; then
    for agent_file in "$pack_dir/agents"/*.md; do
      [ -e "$agent_file" ] || continue
      agent_name="$(basename "$agent_file")"
      install_abs "$agent_file" "./.claude/agents/$agent_name"
    done
  fi

  # Symlink/copy each skill directory into .claude/skills/
  if [ -d "$pack_dir/skills" ]; then
    for skill_dir in "$pack_dir/skills"/*/; do
      [ -d "$skill_dir" ] || continue
      skill_name="$(basename "$skill_dir")"
      install_abs "$skill_dir" "./.claude/skills/$skill_name"
    done
  fi

  log_info "Pack '$pack_name' installed."
}

# ── Prompt greenfield vs brownfield ──────────────────────────────────────────
# Defaults to greenfield when stdin is not a TTY (e.g. curl | sh)
prompt_mode() {
  if [ -t 0 ]; then
    printf "[info]  Is this a greenfield (new) or brownfield (existing/legacy) project?\n"
    printf "        1) greenfield — use CLAUDE.md\n"
    printf "        2) brownfield — use CLAUDE_LEGACY.md\n"
    printf "        Choice [1/2]: "
    read -r mode_choice
  else
    # Non-interactive (piped install) — default to greenfield
    log_info "Non-interactive mode detected. Defaulting to greenfield (CLAUDE.md). Re-run interactively to choose brownfield."
    mode_choice=1
  fi

  case "$mode_choice" in
    2) CLAUDE_SRC="CLAUDE_LEGACY.md" ;;
    *) CLAUDE_SRC="CLAUDE.md" ;;
  esac
}

# ── Install CLAUDE.md as a real copy (always overwrite — fresh install) ───────
install_claude() {
  src="$HARNESS_TEMP_DIR/$CLAUDE_SRC"
  dst="./CLAUDE.md"

  if [ ! -e "$src" ]; then
    log_error "Source '$CLAUDE_SRC' not found in fetched harness. Aborting."
    exit 1
  fi

  parent="$(dirname "$dst")"
  [ -d "$parent" ] || mkdir -p "$parent"
  [ -e "$dst" ] && rm -rf "$dst"
  cp "$src" "$dst"
}

# ── Install settings.json (hook wiring) ──────────────────────────────────────
# Copy-only, never overwrite an existing one: projects append their own
# permissions to it (e.g. fewer-permission-prompts), which must not be clobbered.
# Behavior preserved from the pre-ADR-0001 file; only the source is now the temp
# clone instead of a persistent central clone.
install_settings() {
  src="$HARNESS_TEMP_DIR/.claude/settings.json"
  dst="./.claude/settings.json"

  if [ ! -e "$src" ]; then
    log_warn ".claude/settings.json not found in fetched harness — hooks will not be wired."
    return
  fi
  if [ -e "$dst" ] || [ -L "$dst" ]; then
    return  # never overwrite project settings; merge hook changes manually
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
    while IFS= read -r _line; do
      _line=$(printf '%s' "$_line" | tr -d '\r')
      case "$_line" in '#'*|'') continue ;; esac
      [ -e "./$_line" ] || continue
      if [ -d "./$_line" ]; then
        find "./$_line" -type f
      elif [ -f "./$_line" ]; then
        printf '%s\n' "./$_line"
      fi
    done < "$_manifest"
    [ -f ./CLAUDE.md ] && printf '%s\n' ./CLAUDE.md
  } | sed 's|^\./||' | LC_ALL=C sort -u > "$_files_list"

  _count=$(wc -l < "$_files_list" | tr -d ' ')

  {
    printf '{\n  "files": {\n'
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

> **Rules**: Supervisor-only writes. Max 200 lines. One-line summaries + links to cold files.
> Injected in full into every sub-agent spawn prompt.
> Updated by the Supervisor — prompted by the PostToolUse hook on `git push` / `git merge` (diff-driven pass), or via the `/compact-memory` skill.

---

## Memory Architecture

- [decisions.md](decisions.md) — code + infra architectural decisions (the "why")
- [glossary.md](glossary.md) — canonical biz domain terms and core domain models
- [learnings.md](learnings.md) — specs/requirement clarifications, patterns, gotchas

---

## Index

<!-- Format: - [Title](cold-file.md#section) — one-line summary (≤150 chars) -->
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

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
  check_git
  check_target_is_git_repo   # BEFORE any file write (fetch writes only to temp)
  resolve_repo_url
  prompt_mode
  prompt_packs

  fetch_harness

  manifest="$HARNESS_TEMP_DIR/MANIFEST"
  if [ ! -f "$manifest" ]; then
    log_error "MANIFEST not found in fetched harness. The repo may be corrupt."
    exit 1
  fi

  # Copy every MANIFEST path as real files (always overwrite — fresh install).
  harness_copy_manifest "$HARNESS_TEMP_DIR" "." "$manifest"

  install_claude
  install_settings
  scaffold_project
  write_harness_lock "$manifest"

  # Install selected packs (out of scope per ADR-0001 — unchanged behavior).
  for pack in $PACKS; do
    install_pack "$pack"
  done

  log_info "Setup complete. Harness copied into $(pwd)"
  log_info "CLAUDE source: $CLAUDE_SRC | lock: .claude/harness-lock.json"
  if [ -n "$PACKS" ]; then
    log_info "Packs requested:$PACKS"
  fi
}

main
