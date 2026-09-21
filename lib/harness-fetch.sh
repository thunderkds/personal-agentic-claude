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
#   harness_manifest_path <line>       -> field 1 of a MANIFEST line (CR-stripped; '' for `!` exclusions)
#   harness_manifest_exclusions <manifest>
#                                      -> the `!<path>` exclusions, one per line (T113)
#   harness_is_excluded <manifest> <rel>
#                                      -> 0 if <rel> is, or is under, an exclusion (T113)
#   harness_manifest_dest <line> <harness>
#                                      -> that line's destination for <harness> ('' if none)
#   harness_copy_manifest <tmp> <target> <manifest>
#                                      -> copy each MANIFEST-listed path from <tmp> into <target>
#   harness_backup_path <src> <dst>    -> move a differing <dst> aside to <dst>.bak[.N] (T112)
#   harness_project_manifest <src> <target> <manifest> <harness>
#                                      -> project MANIFEST paths into <harness>'s own directories
#   harness_install_canon_symlinks [target]
#                                      -> (re)point .claude/{skills,agents} at the plain-root canon
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

  # shellcheck disable=SC2094  # read-only lookups of the MANIFEST the loop is reading
  while IFS= read -r _line; do
    # Field 1 only: an optional trailing destination column (T097) is not part
    # of the base install's path, so a mapped line copies exactly where it
    # always did.  CRLF-safe; comments and blank lines yield an empty field.
    _line=$(harness_manifest_path "$_line")
    [ -n "$_line" ] || continue

    _src="$_tmp_dir/$_line"
    _dst="$_target_dir/$_line"

    if [ ! -e "$_src" ]; then
      _harness_log_warn "MANIFEST entry '$_line' not found in fetched clone — skipping."
      continue
    fi

    # A path the MANIFEST excludes is left alone entirely (T113). This must
    # come BEFORE harness_backup_path: backing up an excluded dest would move a
    # project's own directory to <path>.bak and never put it back.
    if harness_is_excluded "$_manifest_path" "$_line"; then
      continue
    fi

    _parent=$(dirname "$_dst")
    [ -d "$_parent" ] || mkdir -p "$_parent"
    # An exclusion UNDER this path (T113): stage the kit's copy without it.
    if [ -n "$(_harness_exclusions_under "$_manifest_path" "$_line")" ]; then
      _harness_install_excluding "$_src" "$_dst" "$_line" "$_manifest_path" || return 1
      continue
    fi
    # Real copy (no symlink). A differing pre-existing dest is moved to a
    # backup first (T112); what is left is identical to the kit's, so removing
    # it lets a directory copy replace cleanly instead of nesting inside itself.
    harness_backup_path "$_src" "$_dst" || return 1
    { [ -e "$_dst" ] || [ -L "$_dst" ]; } && rm -rf "$_dst"
    cp -r "$_src" "$_dst"
  done < "$_manifest_path"
}

# _harness_exclusions_under <manifest_path> <rel> -> exclusions strictly under
# <rel>, each made relative to it, one per line.
_harness_exclusions_under() {
  harness_manifest_exclusions "$1" | while IFS= read -r _eu_x; do
    case "$_eu_x" in "$2"/*) printf '%s\n' "${_eu_x#"$2"/}" ;; esac
  done
}

# _harness_install_excluding <src> <dst> <rel> <manifest_path>
# Install <src> over <dst> as harness_copy_manifest does, when the MANIFEST
# excludes a path under <rel> (T113): the kit's copy is staged without it and the
# project's own excluded path is set aside for the duration, then put back — so
# it is neither installed, backed up, nor compared.
_harness_install_excluding() {
  _ie_src="$1"
  _ie_dst="$2"
  _ie_subs=$(_harness_exclusions_under "$4" "$3")

  _ie_work=$(mktemp -d "${TMPDIR:-/tmp}/harness-excl.XXXXXX") || return 1
  cp -r "$_ie_src" "$_ie_work/stage"
  _ie_can_hold=0
  [ -d "$_ie_dst" ] && [ ! -L "$_ie_dst" ] && _ie_can_hold=1
  _ie_list="$_ie_work/subs"
  printf '%s\n' "$_ie_subs" > "$_ie_list"
  while IFS= read -r _ie_sub; do
    rm -rf "$_ie_work/stage/$_ie_sub"
    if [ "$_ie_can_hold" -eq 1 ] && { [ -e "$_ie_dst/$_ie_sub" ] || [ -L "$_ie_dst/$_ie_sub" ]; }; then
      mkdir -p "$_ie_work/held/$(dirname "$_ie_sub")"
      mv "$_ie_dst/$_ie_sub" "$_ie_work/held/$_ie_sub"
    fi
  done < "$_ie_list"

  _ie_rc=0
  if harness_backup_path "$_ie_work/stage" "$_ie_dst"; then
    { [ -e "$_ie_dst" ] || [ -L "$_ie_dst" ]; } && rm -rf "$_ie_dst"
    cp -r "$_ie_work/stage" "$_ie_dst"
  else
    _ie_rc=1
  fi

  while IFS= read -r _ie_sub; do
    if [ -e "$_ie_work/held/$_ie_sub" ] || [ -L "$_ie_work/held/$_ie_sub" ]; then
      mkdir -p "$_ie_dst/$(dirname "$_ie_sub")"
      mv "$_ie_work/held/$_ie_sub" "$_ie_dst/$_ie_sub"
    fi
  done < "$_ie_list"
  rm -rf "$_ie_work"
  return "$_ie_rc"
}

# harness_backup_path <src> <dst>
# Before the kit replaces <dst> with <src>, move a pre-existing <dst> aside so
# install never destroys a project's own files (T112 / ADR-0002 "No silent loss").
#   missing                         -> nothing
#   identical to <src> (not a link) -> nothing; no backup, no output
#   anything else (file, directory, symlink, type mismatch)
#                                   -> moved to the first free of <dst>.bak,
#                                      <dst>.bak.1, <dst>.bak.2, ... and named
#                                      in a [warn] line. An existing backup is
#                                      never overwritten. A symlink is moved as
#                                      the link itself, its target untouched.
# Public on purpose: T114's "Reinstall (backs up your edits)" calls this rather
# than re-implementing it. Unlike harness_install_canon_symlinks, an existing
# .bak does not fail the run — the next free number keeps both backups.
# Returns 1 (after an [error] line) if the move fails; the caller must then not
# replace <dst>.
harness_backup_path() {
  _bk_src="$1"
  _bk_dst="$2"
  [ -e "$_bk_dst" ] || [ -L "$_bk_dst" ] || return 0

  if [ ! -L "$_bk_dst" ]; then
    if [ -f "$_bk_src" ] && [ -f "$_bk_dst" ] && cmp -s "$_bk_src" "$_bk_dst"; then
      return 0
    fi
    if [ -d "$_bk_src" ] && [ -d "$_bk_dst" ] && diff -rq "$_bk_src" "$_bk_dst" >/dev/null 2>&1; then
      return 0
    fi
  fi

  _bk_to="$_bk_dst.bak"
  _bk_n=0
  while [ -e "$_bk_to" ] || [ -L "$_bk_to" ]; do
    _bk_n=$((_bk_n + 1))
    _bk_to="$_bk_dst.bak.$_bk_n"
  done
  # Checked explicitly: a caller in an `if`/`&&` context runs without set -e,
  # and reporting success here would send it on to rm -rf the unsaved original.
  if ! mv "$_bk_dst" "$_bk_to"; then
    _harness_log_error "Could not back up '$_bk_dst' to '$_bk_to' — nothing was replaced. Fix the permissions, then re-run."
    return 1
  fi
  _harness_log_warn "Backed up your existing '$_bk_dst' to '$_bk_to' before installing the kit's copy — compare and merge by hand, then delete the backup."
  case "$_bk_dst" in
    */.claude/hooks)
      _harness_log_warn "Your own hooks now live in '$_bk_to'; any entries in .claude/settings.json that point at them must be updated to that path." ;;
  esac
}

# ── MANIFEST line parsing (T097) ──────────────────────────────────────────────
# A MANIFEST line is `<path>` optionally followed by whitespace-separated
# `<harness>=<destination>` pairs. Field 1 is the only field the base install
# reads, so a line with no pairs behaves exactly as it did before T097 — that is
# what makes a no-`--harness` install byte-identical to the old one.

# harness_manifest_path <line> -> field 1, CR-stripped. Empty for a comment/blank
# and for an exclusion line (`!<path>`, T113), so every consumer skips it as a path.
harness_manifest_path() {
  printf '%s' "$1" | tr -d '\r' | awk '$0 !~ /^[[:space:]]*(#|$|!)/ { print $1 }'
}

# harness_manifest_exclusions <manifest_path> -> one excluded path per line.
# An exclusion is a literal path prefix (no globs): `!.claude/hooks/tests` drops
# that directory and everything under it from install, lock and update.
harness_manifest_exclusions() {
  tr -d '\r' < "$1" | awk '$1 ~ /^![^[:space:]]/ { print substr($1, 2) }'
}

# harness_is_excluded <manifest_path> <rel_path>
# 0 when <rel_path> equals an exclusion or sits under one. Matches whole path
# segments: `!a/tests` does not exclude `a/tests_helper.py`.
harness_is_excluded() {
  _ie_rel="$2"
  _ie_hit=$(harness_manifest_exclusions "$1" | while IFS= read -r _ie_ex; do
    case "$_ie_rel" in "$_ie_ex"|"$_ie_ex"/*) echo 1; break ;; esac
  done)
  [ -n "$_ie_hit" ]
}

# harness_manifest_dest <line> <harness> -> the destination mapped to <harness>,
# or the empty string when this line maps nothing for it.
harness_manifest_dest() {
  printf '%s' "$1" | tr -d '\r' | awk -v h="$2" '
    $0 ~ /^[[:space:]]*(#|$)/ { next }
    { for (i = 2; i <= NF; i++) {
        eq = index($i, "=")
        if (eq > 1 && substr($i, 1, eq - 1) == h) { print substr($i, eq + 1); exit }
      } }'
}

# ── Per-harness skill-body size cap (T097 / DDR-0007) ─────────────────────────
# Codex caps a skill body at 8 KB. An oversize skill is SKIPPED with a named,
# loud warning — never truncated: a silently trimmed skill looks installed and
# behaves worse than a missing one, which is the one rule carried forward from
# the deferred Option C.
#
# HARNESS_SKILL_BODY_CAP overrides the cap for a run; 0 disables the check
# entirely. That override exists so the anti-vacuity test (AC5) can prove the
# check is load-bearing by watching the same oversize fixture install silently
# with it off. It is not a supported way to install oversize skills.
harness_skill_body_cap() {
  if [ -n "${HARNESS_SKILL_BODY_CAP:-}" ]; then
    # Validate the override (Stage 4 P2). An unvalidated value reaches
    # `[ "$_cap" -gt 0 ]`, which errors and falls FALSE — silently disabling the
    # cap and installing an oversize skill, the exact invisible outcome the cap
    # exists to prevent. Fail loudly by name instead.
    case "$HARNESS_SKILL_BODY_CAP" in
      *[!0-9]*|'')
        _harness_log_error "HARNESS_SKILL_BODY_CAP must be a non-negative integer (got '$HARNESS_SKILL_BODY_CAP')."
        return 2 ;;
    esac
    printf '%s' "$HARNESS_SKILL_BODY_CAP"
    return 0
  fi
  case "$1" in
    codex) printf '8192' ;;
    *)     printf '0' ;;
  esac
}

_harness_file_size() {
  wc -c < "$1" | tr -d ' '
}

# harness_project_manifest <src_dir> <target_dir> <manifest_path> <harness>
# For every MANIFEST line carrying a `<harness>=<dest>` pair, copy field 1 from
# <src_dir> to <dest> under <target_dir> as REAL file copies (ADR-0001 — never
# symlinks; the user owns what lands in their repo).
#
# The destination is removed before writing, so a re-run is idempotent and can
# never leave a half-written or orphaned tree behind (AC7): whatever is there
# after the run is exactly what this run produced.
#
# Skill-body cap: when <harness> has a non-zero cap, each top-level entry of a
# projected directory that contains a SKILL.md is measured. Over the cap, the
# WHOLE skill directory is skipped and named with its byte size, so a partially
# copied skill is never left behind either. Returns 0 with warnings on stderr —
# skip-with-a-loud-warning, not abort, because this kit itself has 4 skills over
# Codex's cap and aborting would make the flag unusable rather than honest.
# HARNESS_PROJECT_SKIPPED is set to the number of skills skipped.
HARNESS_PROJECT_SKIPPED=0
harness_project_manifest() {
  _src_dir="$1"
  _target_dir="$2"
  _manifest_path="$3"
  _harness="$4"
  if [ -z "$_src_dir" ] || [ -z "$_target_dir" ] || [ -z "$_manifest_path" ] || [ -z "$_harness" ]; then
    _harness_log_error "harness_project_manifest: usage: harness_project_manifest <src_dir> <target_dir> <manifest_path> <harness>"
    return 2
  fi
  if [ ! -f "$_manifest_path" ]; then
    _harness_log_error "MANIFEST not found at '$_manifest_path'."
    return 1
  fi

  # Command substitution swallows the exit status, so check it explicitly —
  # otherwise a rejected override would still fall through to an empty cap.
  if ! _cap=$(harness_skill_body_cap "$_harness"); then
    return 2
  fi
  HARNESS_PROJECT_SKIPPED=0
  _projected=0

  while IFS= read -r _line; do
    _rel=$(harness_manifest_path "$_line")
    [ -n "$_rel" ] || continue
    _dest=$(harness_manifest_dest "$_line" "$_harness")
    [ -n "$_dest" ] || continue

    _src="$_src_dir/$_rel"
    if [ ! -e "$_src" ]; then
      _harness_log_warn "MANIFEST entry '$_rel' not found in fetched clone — skipping for harness '$_harness'."
      continue
    fi

    # Reject a destination that escapes the target tree (Stage 4 P2). `_dst` is
    # passed to `rm -rf` below, so an absolute or `..`-bearing dest would delete
    # and write outside the user's project.
    case "$_dest" in
      /*|*/../*|*/..|../*|..)
        _harness_log_error "MANIFEST destination '$_dest' for harness '$_harness' must be a relative path inside the project (no leading '/' and no '..' segment) — skipping."
        continue ;;
    esac
    _dst="$_target_dir/$_dest"
    _parent=$(dirname "$_dst")
    [ -d "$_parent" ] || mkdir -p "$_parent"
    rm -rf "$_dst"

    if [ ! -d "$_src" ]; then
      cp "$_src" "$_dst"
      _projected=$((_projected + 1))
      continue
    fi

    mkdir -p "$_dst"
    for _entry in "$_src"/*; do
      [ -e "$_entry" ] || continue
      _name=$(basename "$_entry")
      if [ "$_cap" -gt 0 ] && [ -f "$_entry/SKILL.md" ]; then
        _size=$(_harness_file_size "$_entry/SKILL.md")
        if [ "$_size" -gt "$_cap" ]; then
          _harness_log_warn "$_harness: skill '$_name' has a ${_size}-byte body, over the ${_cap}-byte $_harness cap — SKIPPED, not truncated. Shorten or split $_rel/$_name/SKILL.md, then re-run."
          HARNESS_PROJECT_SKIPPED=$((HARNESS_PROJECT_SKIPPED + 1))
          continue
        fi
      fi
      cp -r "$_entry" "$_dst/"
      _projected=$((_projected + 1))
    done
  done < "$_manifest_path"

  _harness_log_info "Projected $_projected item(s) for harness '$_harness'."
  if [ "$HARNESS_PROJECT_SKIPPED" -gt 0 ]; then
    _harness_log_warn "$HARNESS_PROJECT_SKIPPED skill(s) were SKIPPED for '$_harness' because their body exceeds the ${_cap}-byte cap (named above). They are absent, not truncated."
  fi
}

# harness_install_canon_symlinks <target_dir>
# Re-establish `.claude/skills -> ../skills` and `.claude/agents -> ../agents`
# in <target_dir> (defaults to `.`). Idempotent: safe to call on every setup AND
# every update run, which is what keeps Claude Code reading the freshly copied
# plain-root canon rather than a stale copy (DDR-0007).
#
# Per canon directory:
#   symlink (any target) -> replaced with the correct RELATIVE link
#   missing              -> created
#   real directory       -> pre-T096 install: moved aside to `<link>.bak` and
#                           replaced with the link. If `<link>.bak` already
#                           exists the run FAILS (return 1) rather than
#                           overwrite a previous backup.
#   regular file         -> left to `ln -s`, which fails; under `set -e` the
#                           caller exits non-zero. Failing loudly is correct.
#
# Never returns 0 while `.claude/<canon>` still holds content Claude Code would
# read instead of the canon — a silent success there is the bug this prevents.
harness_install_canon_symlinks() {
  _target_dir="${1:-.}"
  [ -d "$_target_dir/.claude" ] || mkdir -p "$_target_dir/.claude"

  for _canon in skills agents; do
    _link="$_target_dir/.claude/$_canon"

    if [ -L "$_link" ]; then
      rm "$_link"
    elif [ -d "$_link" ]; then
      _backup="$_link.bak"
      if [ -e "$_backup" ]; then
        _harness_log_error "'$_link' is a real directory from an older install and '$_backup' already exists."
        _harness_log_error "Move or delete '$_backup', then re-run — Claude Code cannot see the canon at './$_canon' until '$_link' is a symlink."
        return 1
      fi
      mv "$_link" "$_backup"
      _harness_log_warn "'$_link' was a real directory from an older install — moved to '$_backup' and replaced with a symlink onto './$_canon'."
    fi

    ln -s "../$_canon" "$_link"
  done
}
