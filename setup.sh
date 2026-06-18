#!/bin/sh
# setup.sh — Supervisor Agent Deployment System installer
# Usage: bash setup.sh [--copy]
# SUPERVISOR_PATH overrides the default central clone location (~/.supervisor)
set -e

SUPERVISOR_PATH="${SUPERVISOR_PATH:-$HOME/.supervisor}"

# ── Resolve GitHub username → repo URL ───────────────────────────────────────
# Defaults to the canonical repo; set GITHUB_USERNAME to install from a fork.
resolve_repo_url() {
  GITHUB_USERNAME="${GITHUB_USERNAME:-thunderkds}"
  SUPERVISOR_REPO="https://github.com/${GITHUB_USERNAME}/personal-agentic-claude.git"
  log_info "Using repo: $SUPERVISOR_REPO"
}

# ── Logging helpers (TTY-aware color, plain-text fallback) ────────────────────
GREEN=''; YELLOW=''; RED=''; RESET=''
if [ -t 1 ]; then
  GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; RESET='\033[0m'
fi
log_info()  { printf "${GREEN}[info]${RESET}  %s\n"  "$*"; }
log_warn()  { printf "${YELLOW}[warn]${RESET}  %s\n" "$*" >&2; }
log_error() { printf "${RED}[error]${RESET} %s\n"   "$*" >&2; }

# ── Parse flags ───────────────────────────────────────────────────────────────
USE_COPY=0
PACKS=""  # space-separated list of packs to install (e.g. " mobile data")
for arg in "$@"; do
  case "$arg" in
    --copy) USE_COPY=1 ;;
    --pack=*) pack_val="${arg#--pack=}"; PACKS="$PACKS $pack_val" ;;
    *) log_error "Unknown flag: $arg. Valid flags: --copy, --pack=<name>"; exit 1 ;;
  esac
done

# ── Pillar: check_git (before any filesystem change) ─────────────────────────
check_git() {
  if ! command -v git >/dev/null 2>&1; then
    log_error "Git is required but not installed. Install Git and re-run setup.sh."
    exit 1
  fi
}

# ── Clone or verify the central clone ────────────────────────────────────────
clone_or_verify() {
  # Detect if script is running from inside the central clone itself
  script_dir="$(cd "$(dirname "$0")" && pwd)"
  central="$(cd "$SUPERVISOR_PATH" 2>/dev/null && pwd)" || true
  if [ -n "$central" ] && [ "$script_dir" = "$central" ]; then
    log_error "Cannot run setup.sh from inside the central clone ($SUPERVISOR_PATH). Run it from your target project."
    exit 1
  fi

  if [ -d "$SUPERVISOR_PATH" ]; then
    if ! git -C "$SUPERVISOR_PATH" rev-parse --git-dir >/dev/null 2>&1; then
      log_error "$SUPERVISOR_PATH exists but is not a git repository. Remove it and re-run, or set SUPERVISOR_PATH to a different location."
      exit 1
    fi
    # Already a valid repo — nothing to do
  else
    # Create parent directories only; git clone creates the leaf itself
    mkdir -p "$(dirname "$SUPERVISOR_PATH")"
    git clone "$SUPERVISOR_REPO" "$SUPERVISOR_PATH"
  fi
}

# ── Prompt pack selection (interactive only, skipped if --pack= flags given) ──
AVAILABLE_PACKS="mobile data devops ai-agent api"

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
# Takes absolute src and relative dst (from project root)
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
  # Detect WSL for informational note
  if uname -r 2>/dev/null | grep -qi microsoft; then
    log_warn "WSL detected. Symlinks work in the Linux filesystem. Avoid placing the project on a Windows NTFS mount (/mnt/c/...) — use --copy there instead."
  fi

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

# ── Install one path from MANIFEST ───────────────────────────────────────────
install_path() {
  entry="$1"
  src="$SUPERVISOR_PATH/$entry"
  dst="./$entry"

  if [ ! -e "$src" ]; then
    log_warn "MANIFEST entry '$entry' not found in central clone — skipping."
    return
  fi

  # Hoist parent-dir creation (shared by both modes)
  parent="$(dirname "$dst")"
  [ -d "$parent" ] || mkdir -p "$parent"

  if [ $USE_COPY -eq 1 ]; then
    # --copy mode: warn if it's a symlink; skip silently if already a real copy
    if [ -L "$dst" ]; then
      log_warn "'$dst' is a symlink from a previous install. Remove it manually to switch to --copy mode."
      return
    fi
    if [ -e "$dst" ]; then
      return  # already copied, idempotent
    fi
    cp -r "$src" "$dst"
  else
    # Symlink mode: warn on broken or real-file conflicts
    if [ -L "$dst" ] && [ ! -e "$dst" ]; then
      log_warn "'$dst' is a broken symlink — removing and re-linking."
      rm "$dst"
    elif [ -L "$dst" ]; then
      return  # already a valid symlink, idempotent
    elif [ -e "$dst" ]; then
      log_warn "'$dst' exists as a real path (not a symlink). Skipping — remove it manually to allow symlinking."
      return
    fi
    ln -s "$src" "$dst"
  fi
}

# ── Install CLAUDE.md symlink/copy ────────────────────────────────────────────
install_claude() {
  src="$SUPERVISOR_PATH/$CLAUDE_SRC"
  dst="./CLAUDE.md"

  if [ ! -e "$src" ]; then
    log_error "Source '$CLAUDE_SRC' not found in central clone ($SUPERVISOR_PATH). Aborting."
    exit 1
  fi

  # Handle broken symlink: remove and re-link
  if [ -L "$dst" ] && [ ! -e "$dst" ]; then
    log_warn "'$dst' is a broken symlink — removing and re-linking."
    rm "$dst"
  fi

  # Existing real file: prompt (interactive only) or skip (non-interactive)
  if [ -e "$dst" ] && [ ! -L "$dst" ]; then
    if [ -t 0 ]; then
      log_warn "'./CLAUDE.md' already exists as a real file. Overwrite? [y/N]: "
      read -r overwrite
      case "$overwrite" in
        [Yy]*) rm "$dst" ;;
        *) log_warn "Skipping CLAUDE.md — remove it manually if you want supervisor rules installed."; return ;;
      esac
    else
      log_warn "'./CLAUDE.md' already exists. Skipping in non-interactive mode — remove it manually to allow install."
      return
    fi
  fi

  if [ -L "$dst" ]; then
    return  # already a valid symlink, idempotent
  fi

  if [ $USE_COPY -eq 1 ]; then
    cp "$src" "$dst"
  else
    ln -s "$src" "$dst"
  fi
}

# ── Install settings.json (hook wiring) ──────────────────────────────────────
# Always a copy, never a symlink: projects append their own permissions to it
# (e.g. fewer-permission-prompts), which must not leak into the central clone.
install_settings() {
  src="$SUPERVISOR_PATH/.claude/settings.json"
  dst="./.claude/settings.json"

  if [ ! -e "$src" ]; then
    log_warn ".claude/settings.json not found in central clone — hooks will not be wired."
    return
  fi
  if [ -e "$dst" ] || [ -L "$dst" ]; then
    return  # never overwrite project settings; merge hook changes manually
  fi
  [ -d ./.claude ] || mkdir -p ./.claude
  cp "$src" "$dst"
  log_info "Installed .claude/settings.json (copy). Restart Claude Code to activate hooks."
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
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
  check_git
  resolve_repo_url
  clone_or_verify
  prompt_mode
  prompt_packs

  # Read MANIFEST and install each listed path
  manifest="$SUPERVISOR_PATH/MANIFEST"
  if [ ! -f "$manifest" ]; then
    log_error "MANIFEST not found in central clone ($SUPERVISOR_PATH). The repo may be corrupt."
    exit 1
  fi

  while IFS= read -r line; do
    # Strip carriage returns here (CRLF-safe; $'\r' is a bashism and this runs under sh/dash)
    line=$(printf '%s' "$line" | tr -d '\r')
    case "$line" in
      '#'*|'') continue ;;  # skip comments and blank lines
      *) install_path "$line" ;;
    esac
  done < "$manifest"

  install_claude
  install_settings
  scaffold_project

  # Install selected packs
  for pack in $PACKS; do
    install_pack "$pack"
  done

  log_info "Setup complete. Installed from: $SUPERVISOR_PATH"
  log_info "Mode: $([ $USE_COPY -eq 1 ] && echo 'copy' || echo 'symlink') | CLAUDE: $CLAUDE_SRC"
  if [ -n "$PACKS" ]; then
    log_info "Packs installed:$PACKS"
  fi
}

main
