#!/bin/sh
# setup.sh — Supervisor Agent Deployment System installer
# Usage: bash setup.sh [--copy]
# SUPERVISOR_PATH overrides the default central clone location (~/.supervisor)
set -e

SUPERVISOR_REPO_TEMPLATE="https://github.com/%s/personal-agentic-claude.git"
SUPERVISOR_PATH="${SUPERVISOR_PATH:-$HOME/.supervisor}"

# ── Resolve GitHub username → repo URL ───────────────────────────────────────
resolve_repo_url() {
  if [ -n "$GITHUB_USERNAME" ]; then
    SUPERVISOR_REPO="$(printf "$SUPERVISOR_REPO_TEMPLATE" "$GITHUB_USERNAME")"
    return
  fi
  if [ -t 0 ]; then
    printf "[info]  Enter your GitHub username: "
    read -r GITHUB_USERNAME
    if [ -z "$GITHUB_USERNAME" ]; then
      log_error "GitHub username is required. Set GITHUB_USERNAME env var or enter it at the prompt."
      exit 1
    fi
  else
    log_error "Non-interactive mode: set GITHUB_USERNAME env var before running setup.sh."
    exit 1
  fi
  SUPERVISOR_REPO="$(printf "$SUPERVISOR_REPO_TEMPLATE" "$GITHUB_USERNAME")"
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
for arg in "$@"; do
  case "$arg" in
    --copy) USE_COPY=1 ;;
    *) log_error "Unknown flag: $arg"; exit 1 ;;
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
  # Strip any trailing carriage return (CRLF-safe)
  entry="${1%$'\r'}"
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

# ── Scaffold project-specific folders ────────────────────────────────────────
scaffold_project() {
  [ -d ./tasks ]  || mkdir ./tasks
  [ -d ./memory ] || mkdir ./memory
  if [ ! -f ./memory/MEMORY.md ]; then
    cat > ./memory/MEMORY.md <<'EOF'
# MEMORY.md — Session-Persistent Insights Index

> Read this file at the start of every session. Each entry links to a detailed memory file.
> Write new entries when new patterns, decisions, or feedback are learned.
> Keep entries under 150 characters. Full details live in the linked files.

---

## Index

<!-- Add entries below as memories are created. Format:
- [Title](filename.md) — one-line description of what this memory captures
-->
EOF
  fi
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
  check_git
  resolve_repo_url
  clone_or_verify
  prompt_mode

  # Read MANIFEST and install each listed path
  manifest="$SUPERVISOR_PATH/MANIFEST"
  if [ ! -f "$manifest" ]; then
    log_error "MANIFEST not found in central clone ($SUPERVISOR_PATH). The repo may be corrupt."
    exit 1
  fi

  while IFS= read -r line; do
    case "$line" in
      '#'*|''|$'\r') continue ;;  # skip comments, blank lines, bare CRs
      *) install_path "$line" ;;
    esac
  done < "$manifest"

  install_claude
  scaffold_project

  log_info "Setup complete. Installed from: $SUPERVISOR_PATH"
  log_info "Mode: $([ $USE_COPY -eq 1 ] && echo 'copy' || echo 'symlink') | CLAUDE: $CLAUDE_SRC"
}

main
