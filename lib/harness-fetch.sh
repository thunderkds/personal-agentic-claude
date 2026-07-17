# shellcheck shell=sh
# lib/harness-fetch.sh — shared temp-clone-copy-discard fetch mechanism (ADR-0001)
#
# Sourceable POSIX-sh library. setup.sh (T032) and update.sh (T033) source this
# so the fetch-and-copy logic lives in exactly one place. This file defines
# functions only — it performs no work at source time.
#
# Public functions:
#   harness_make_temp_dir              -> creates a temp dir, registers it, sets $HARNESS_TEMP_DIR
#   harness_register_cleanup <dir>     -> register an existing dir for cleanup-on-exit
#   harness_fetch <repo_url> <dest>    -> git clone --depth 1 <repo_url> into <dest>
#   harness_copy_manifest <tmp> <target> <manifest>
#                                      -> copy each MANIFEST-listed path from <tmp> into <target>
#   harness_cleanup                    -> rm -rf all registered temp dirs (idempotent)
#
# Cleanup contract (ADR-0001): the first registered dir installs traps so every
# registered temp dir is rm -rf'd on normal exit AND on interrupt (INT/TERM/HUP).
# The caller never has to invoke harness_cleanup manually.
#
# NOTE: registering a temp dir installs EXIT/INT/TERM/HUP traps in the sourcing
# shell. setup.sh/update.sh (which source this) currently set no traps of their
# own, so this is safe; a future caller that needs its own traps must chain them.

# ── Private logging helpers (self-contained; do not clobber a caller's log_*) ──
# Underscore-prefixed = internal to this library.
_HARNESS_GREEN=''; _HARNESS_YELLOW=''; _HARNESS_RED=''; _HARNESS_RESET=''
if [ -t 2 ]; then
  _HARNESS_GREEN='\033[0;32m'; _HARNESS_YELLOW='\033[0;33m'
  _HARNESS_RED='\033[0;31m'; _HARNESS_RESET='\033[0m'
fi
_harness_log_info()  { printf "${_HARNESS_GREEN}[info]${_HARNESS_RESET}  %s\n"  "$*" >&2; }
_harness_log_warn()  { printf "${_HARNESS_YELLOW}[warn]${_HARNESS_RESET}  %s\n" "$*" >&2; }
_harness_log_error() { printf "${_HARNESS_RED}[error]${_HARNESS_RESET} %s\n"   "$*" >&2; }

# ── Cleanup registry ──────────────────────────────────────────────────────────
# Newline-separated list of temp dirs to remove on exit/interrupt.
_HARNESS_TEMP_DIRS=''
_HARNESS_TRAPS_INSTALLED=''

# Install exit/interrupt traps exactly once. On a signal we re-exit so the single
# EXIT trap does the actual cleanup — this guarantees cleanup fires on Ctrl-C.
_harness_install_traps() {
  [ "$_HARNESS_TRAPS_INSTALLED" = "1" ] && return 0
  trap 'harness_cleanup' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  trap 'exit 129' HUP
  _HARNESS_TRAPS_INSTALLED=1
}

# harness_register_cleanup <dir>
# Register an existing directory for removal on exit/interrupt. Installs traps
# on first registration. Idempotent per dir is not enforced (rm -rf is safe).
harness_register_cleanup() {
  _dir="$1"
  [ -n "$_dir" ] || return 0
  if [ -z "$_HARNESS_TEMP_DIRS" ]; then
    _HARNESS_TEMP_DIRS="$_dir"
  else
    _HARNESS_TEMP_DIRS="$_HARNESS_TEMP_DIRS
$_dir"
  fi
  _harness_install_traps
}

# harness_cleanup
# Remove every registered temp dir. Idempotent: safe to call more than once and
# safe if a dir was already removed. Clears the registry when done.
harness_cleanup() {
  [ -n "$_HARNESS_TEMP_DIRS" ] || return 0
  printf '%s\n' "$_HARNESS_TEMP_DIRS" | while IFS= read -r _d; do
    [ -n "$_d" ] && [ -d "$_d" ] && rm -rf "$_d"
  done
  _HARNESS_TEMP_DIRS=''
}

# harness_make_temp_dir
# Create a unique temp dir (mktemp -d), register it for cleanup, and expose its
# path in the caller's shell as $HARNESS_TEMP_DIR. Returns non-zero if mktemp
# fails. The path is deliberately returned via a variable, NOT printed on stdout:
# capturing a printed path with $(...) would run registration inside a command-
# substitution subshell, so the EXIT trap would never fire in the caller's shell.
harness_make_temp_dir() {
  HARNESS_TEMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/harness-fetch.XXXXXX")" || {
    _harness_log_error "Failed to create a temp directory via mktemp."
    return 1
  }
  harness_register_cleanup "$HARNESS_TEMP_DIR"
}

# harness_fetch <repo_url> <dest_tmp_dir>
# Shallow-clone <repo_url> into the caller-supplied <dest_tmp_dir>. On failure,
# prints a clear error and returns non-zero without touching any other path.
harness_fetch() {
  _repo_url="$1"
  _dest="$2"
  if [ -z "$_repo_url" ] || [ -z "$_dest" ]; then
    _harness_log_error "harness_fetch: usage: harness_fetch <repo_url> <dest_tmp_dir>"
    return 2
  fi
  _harness_log_info "Fetching (shallow clone): $_repo_url"
  if ! git clone --depth 1 "$_repo_url" "$_dest" >/dev/null 2>&1; then
    _harness_log_error "Failed to clone '$_repo_url' into '$_dest'. Check the URL, network connectivity, and git credentials."
    return 1
  fi
}

# harness_copy_manifest <tmp_dir> <target_dir> <manifest_path>
# Read MANIFEST at <manifest_path>, and for each listed path copy it (real
# recursive copy) from <tmp_dir> into <target_dir>, creating parent dirs as
# needed. Comments (#...) and blank lines are skipped; CR is stripped (CRLF-safe).
# A MANIFEST entry absent from the fetched clone is warned and skipped, not fatal.
harness_copy_manifest() {
  _tmp_dir="$1"
  _target_dir="$2"
  _manifest_path="$3"
  if [ -z "$_tmp_dir" ] || [ -z "$_target_dir" ] || [ -z "$_manifest_path" ]; then
    _harness_log_error "harness_copy_manifest: usage: harness_copy_manifest <tmp_dir> <target_dir> <manifest_path>"
    return 2
  fi
  if [ ! -f "$_manifest_path" ]; then
    _harness_log_error "MANIFEST not found at '$_manifest_path'."
    return 1
  fi

  while IFS= read -r _line; do
    # CRLF-safe: strip carriage returns (matches setup.sh main loop).
    _line=$(printf '%s' "$_line" | tr -d '\r')
    case "$_line" in
      '#'*|'') continue ;;  # skip comments and blank lines
    esac

    _src="$_tmp_dir/$_line"
    _dst="$_target_dir/$_line"

    if [ ! -e "$_src" ]; then
      _harness_log_warn "MANIFEST entry '$_line' not found in fetched clone — skipping."
      continue
    fi

    _parent=$(dirname "$_dst")
    [ -d "$_parent" ] || mkdir -p "$_parent"
    # Real overwrite copy (no symlink). Remove any existing dest first so a
    # directory copy replaces cleanly instead of nesting inside itself.
    [ -e "$_dst" ] && rm -rf "$_dst"
    cp -r "$_src" "$_dst"
  done < "$_manifest_path"
}
