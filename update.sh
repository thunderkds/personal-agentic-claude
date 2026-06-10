#!/bin/sh
# update.sh — Supervisor Agent Deployment System updater
# Usage: bash update.sh
# SUPERVISOR_PATH overrides the default central clone location (~/.supervisor)
set -e

SUPERVISOR_PATH="${SUPERVISOR_PATH:-$HOME/.supervisor}"

# ── Logging helpers (TTY-aware color, plain-text fallback) ────────────────────
GREEN=''; YELLOW=''; RED=''; RESET=''
if [ -t 1 ]; then
  GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; RESET='\033[0m'
fi
log_info()  { printf "${GREEN}[info]${RESET}  %s\n"  "$*"; }
log_warn()  { printf "${YELLOW}[warn]${RESET}  %s\n" "$*" >&2; }
log_error() { printf "${RED}[error]${RESET} %s\n"   "$*" >&2; }

# ── Check git installed ───────────────────────────────────────────────────────
if ! command -v git >/dev/null 2>&1; then
  log_error "Git is required but not installed. Install Git and re-run update.sh."
  exit 1
fi

# ── Verify central clone exists and is a git repo ────────────────────────────
if [ ! -d "$SUPERVISOR_PATH" ] || ! git -C "$SUPERVISOR_PATH" rev-parse --git-dir >/dev/null 2>&1; then
  log_error "$SUPERVISOR_PATH is not a git repository. Run setup.sh first."
  exit 1
fi

# ── Capture pre-pull state ────────────────────────────────────────────────────
pre_sha="$(git -C "$SUPERVISOR_PATH" rev-parse HEAD)"
pre_manifest="$(git -C "$SUPERVISOR_PATH" show HEAD:MANIFEST 2>/dev/null || true)"

# ── Pull ──────────────────────────────────────────────────────────────────────
log_info "Pulling latest changes into $SUPERVISOR_PATH ..."
if ! git -C "$SUPERVISOR_PATH" pull --ff-only; then
  log_error "git pull failed. If you have local changes, run: git -C \"$SUPERVISOR_PATH\" stash"
  exit 1
fi

# ── Report what changed ───────────────────────────────────────────────────────
post_sha="$(git -C "$SUPERVISOR_PATH" rev-parse HEAD)"

if [ "$pre_sha" = "$post_sha" ]; then
  log_info "Already up to date. (HEAD: ${post_sha})"
else
  log_info "Updated ${pre_sha} → ${post_sha}"
  git -C "$SUPERVISOR_PATH" log --oneline "${pre_sha}..${post_sha}"

  post_manifest="$(git -C "$SUPERVISOR_PATH" show HEAD:MANIFEST 2>/dev/null || true)"
  if [ "$pre_manifest" != "$post_manifest" ]; then
    log_warn "New resources available — re-run setup.sh to deploy"
  fi
fi

log_info "Last update: $(git -C "$SUPERVISOR_PATH" log -1 --format='%ci %s' HEAD)"
