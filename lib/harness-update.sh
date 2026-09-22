#!/bin/sh
# lib/harness-update.sh — Easy Kit's Update action (ADR-0002), sourced by setup.sh.
#
# These functions were update.sh's body until T114. setup.sh is now the one
# Easy Kit command: it detects an existing install (.claude/harness-lock.json),
# offers Update / Reinstall / Cancel, and dispatches Update to run_update below.
# update.sh survives only as a thin alias for that action.
#
# Update model (ADR-0001, unchanged): the fresh upstream is already fetched into
# $HARNESS_TEMP_DIR; for EACH individual file under each MANIFEST path the
# project's current content hash is compared against the lock:
#   - hash unchanged since install  -> overwrite silently with the fresh upstream
#   - hash changed (user customized) -> show a diff and prompt per file:
#         [o]verwrite / [s]kip / [v]iew diff again
# Files upstream stopped shipping are removed if unedited, kept if edited (T113).
# The lock is then re-recorded to reflect what the user accepted.
#
# Harness projections (T097/T098): a harness is re-projected if it was passed via
# --harness on this run OR if its destination directory already exists in the
# project; re-projection replaces the destination wholesale so nothing upstream
# removed survives as an orphan. `.claude/{skills,agents}` are re-pointed at the
# canon; a pre-T096 real directory there is moved to `<link>.bak`.
#
# Define-only: this file runs nothing at top level. It relies on setup.sh for
# log_*, compute_file_hash, merge_settings, tty_read and $HARNESS_TEMP_DIR.

# ── Settings merge (T111, ADR-0002) ──────────────────────────────────────────
# `.claude/settings.json` is not a MANIFEST path — it is a per-project file the
# user extends — so the hash-lock copy loop never touched it and an upstream
# hook change never reached an installed project. This step reconciles the kit's
# hook entries into it while leaving everything the user added alone. On refusal
# merge_settings (setup.sh) writes nothing and the run exits 2 at the end.
update_settings() {
  _src="$HARNESS_TEMP_DIR/.claude/settings.json"
  _dst="./.claude/settings.json"

  if [ ! -f "$_src" ]; then
    log_warn ".claude/settings.json not found in fetched Easy Kit — hook wiring left unchanged."
    return
  fi
  if [ ! -e "$_dst" ] && [ ! -L "$_dst" ]; then
    [ -d ./.claude ] || mkdir -p ./.claude
    cp "$_src" "$_dst"
    log_info "Installed $_dst (none existed). Restart Claude Code to activate hooks."
    return
  fi
  merge_settings "$_src" "$_dst"
}

# ── Symlink refusal (all-or-nothing, before any compare/overwrite) ───────────
# If ANY MANIFEST path in the target is a symlink, this is an old symlink-model
# install. Refuse the whole run with a migration instruction — do NOT convert.
detect_symlinks() {
  _manifest="$1"
  _found=0
  while IFS= read -r _line; do
    _line=$(harness_manifest_path "$_line")   # field 1 only (T097)
    [ -n "$_line" ] || continue
    if [ -L "./$_line" ]; then
      log_error "MANIFEST path './$_line' is a symlink (old symlink-model install)."
      _found=1
    fi
  done < "$_manifest"

  if [ "$_found" -eq 1 ]; then
    log_error "This project was installed with the old symlink model. Easy Kit will not convert it."
    log_error "To migrate: remove the symlinked path(s) above, then re-run setup.sh and choose Update — it restores them as real files."
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
    _l=$(harness_manifest_path "$_l")         # field 1 only (T097)
    [ -n "$_l" ] || continue
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
  # shellcheck disable=SC2094  # read-only lookups of the MANIFEST the loop is reading
  while IFS= read -r _line; do
    _line=$(harness_manifest_path "$_line")   # field 1 only (T097)
    [ -n "$_line" ] || continue
    _src="$HARNESS_TEMP_DIR/$_line"
    if [ -d "$_src" ]; then
      ( cd "$HARNESS_TEMP_DIR" && find "$_line" -type f ) | while IFS= read -r _f; do
        harness_is_excluded "$_manifest" "$_f" || printf '%s\n' "$_f"
      done >> "$_out"
    elif [ -f "$_src" ]; then
      printf '%s\n' "$_line" >> "$_out"
    else
      log_warn "MANIFEST entry '$_line' not found in fetched clone — skipping."
    fi
  done < "$_manifest"
}

# ── Interactive per-file conflict prompt ─────────────────────────────────────
# Sets CONFLICT_DECISION to: o (overwrite) | s (skip) | eof (no input available).
# Reads the terminal (tty_read, /dev/tty) — never stdin, which under `curl | sh`
# is the script itself (T114). With no terminal, or on EOF, it does NOT guess —
# returns "eof" so the caller skips the file and flags the run for a re-run.
CONFLICT_DECISION=""
prompt_conflict() {
  _cur="$1"   # working-copy path
  _fresh="$2" # freshly-fetched upstream path
  while :; do
    printf '  Resolve: [o]verwrite / [s]kip / [v]iew diff again: ' >&2
    if ! tty_read; then
      printf '\n' >&2
      CONFLICT_DECISION="eof"
      return 0
    fi
    case "$TTY_ANSWER" in
      o|O|overwrite) CONFLICT_DECISION="o"; return 0 ;;
      s|S|skip)      CONFLICT_DECISION="s"; return 0 ;;
      v|V|view)      diff -u "$_cur" "$_fresh" >&2 || true ;;
      *)             printf '  Please enter o, s, or v.\n' >&2 ;;
    esac
  done
}

# ── Compare + update a single file, recording its final hash to $_decisions
# and marking $_rel handled in $_processed. Shared by process_files (MANIFEST
# entries) and process_claude_md (T110) so both go through one comparison +
# prompt path. Sets LAST_FILE_INSTALLED to 1 iff install_file actually ran, so
# a caller can tell "installed" apart from "skipped/left alone".
# _force_conflict=1 skips the untouched/no-diff fast paths and always prompts
# (used when the caller could not establish which upstream file backs $_dst).
LAST_FILE_INSTALLED=0
process_one_file() {
  _src="$1"
  _dst="$2"
  _rel="$3"
  _lock="$4"
  _decisions="$5"
  _processed="$6"
  _force_conflict="${7:-}"
  LAST_FILE_INSTALLED=0
  _fresh_hash=$(compute_file_hash "$_src")
  printf '%s\n' "$_rel" >> "$_processed"

  # New file added upstream since install — install directly, no conflict.
  if [ ! -e "$_dst" ]; then
    install_file "$_src" "$_dst"
    LAST_FILE_INSTALLED=1
    printf '%s\t%s\n' "$_rel" "$_fresh_hash" >> "$_decisions"
    log_info "new file installed: $_rel"
    return
  fi

  _cur_hash=$(compute_file_hash "$_dst")
  _rec_hash=$(lookup_lock_hash "$_lock" "$_rel")

  if [ "$_force_conflict" != "1" ]; then
    # Untouched since install (hash still matches the lock) — overwrite silently.
    if [ -n "$_rec_hash" ] && [ "$_cur_hash" = "$_rec_hash" ]; then
      install_file "$_src" "$_dst"
      LAST_FILE_INSTALLED=1
      printf '%s\t%s\n' "$_rel" "$_fresh_hash" >> "$_decisions"
      return
    fi

    # No real diff (current content already equals upstream) — no-op overwrite,
    # nothing to resolve. Covers "edited back to upstream" and "identical but
    # never tracked" without a pointless empty-diff prompt.
    if [ "$_cur_hash" = "$_fresh_hash" ]; then
      install_file "$_src" "$_dst"
      LAST_FILE_INSTALLED=1
      printf '%s\t%s\n' "$_rel" "$_fresh_hash" >> "$_decisions"
      return
    fi
  fi

  # Real conflict: user customized this file (or it was never tracked and the
  # content genuinely differs), or the caller forced the conflict path because
  # it could not identify $_dst's upstream source. Show the diff and prompt.
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
      LAST_FILE_INSTALLED=1
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
}

# ── Compare + update every MANIFEST file, recording final hashes ─────────────
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
    process_one_file "$HARNESS_TEMP_DIR/$_rel" "./$_rel" "$_rel" "$_lock" "$_decisions" "$_processed"
  done 3< "$_list"
}

# ── Determine which upstream file backs the project's CLAUDE.md (T110) ───────
# Prefers the recorded lock field (AC4: "claude_md_source"). Falls back to
# heading inference for old locks written before this field existed (AC5):
# compares CLAUDE.md's first line against each candidate's first line in the
# fetched temp clone. Sets CLAUDE_MD_SOURCE to the winning filename, or
# "conflict" when neither/both match — never guessed.
CLAUDE_MD_SOURCE=""
resolve_claude_md_source() {
  _lock="$1"
  _dst="$2"
  _recorded=$(lookup_lock_hash "$_lock" "claude_md_source")
  if [ -n "$_recorded" ]; then
    case "$_recorded" in
      CLAUDE.md|CLAUDE_LEGACY.md)
        CLAUDE_MD_SOURCE="$_recorded"
        return
        ;;
      *)
        log_warn "recorded claude_md_source '$_recorded' is not an allowed value (CLAUDE.md or CLAUDE_LEGACY.md) — falling back to heading inference."
        ;;
    esac
  fi
  if [ ! -e "$_dst" ]; then
    # Deleted by the user, or never installed — treat like any missing file.
    CLAUDE_MD_SOURCE="CLAUDE.md"
    return
  fi
  _dst_first=$(head -n1 "$_dst" 2>/dev/null || true)
  _match=""
  for _cand in CLAUDE.md CLAUDE_LEGACY.md; do
    _cand_path="$HARNESS_TEMP_DIR/$_cand"
    [ -f "$_cand_path" ] || continue
    _cand_first=$(head -n1 "$_cand_path")
    if [ "$_dst_first" = "$_cand_first" ]; then
      if [ -n "$_match" ]; then
        CLAUDE_MD_SOURCE="conflict"
        return
      fi
      _match="$_cand"
    fi
  done
  CLAUDE_MD_SOURCE="${_match:-conflict}"
}

# ── Deliver CLAUDE.md through the same edit-safe rule as every other file (T110)
# Sets FINAL_CLAUDE_MD_SOURCE to the value write_new_lock should record — the
# resolved source when known, or empty when still unresolved (ambiguous heading
# with no overwrite this run), so a future update keeps trying to resolve it
# rather than recording a guess.
FINAL_CLAUDE_MD_SOURCE=""
process_claude_md() {
  _lock="$1"
  _decisions="$2"
  _processed="$3"
  _dst="./CLAUDE.md"
  resolve_claude_md_source "$_lock" "$_dst"

  if [ "$CLAUDE_MD_SOURCE" = "conflict" ]; then
    log_warn "conflict: 'CLAUDE.md' install source could not be determined from its first line — treating as customized."
    process_one_file "$HARNESS_TEMP_DIR/CLAUDE.md" "$_dst" "CLAUDE.md" "$_lock" "$_decisions" "$_processed" 1
    if [ "$LAST_FILE_INSTALLED" = "1" ]; then
      FINAL_CLAUDE_MD_SOURCE="CLAUDE.md"
    fi
    return
  fi

  FINAL_CLAUDE_MD_SOURCE="$CLAUDE_MD_SOURCE"
  _src="$HARNESS_TEMP_DIR/$CLAUDE_MD_SOURCE"
  if [ ! -f "$_src" ]; then
    log_error "CLAUDE.md source '$CLAUDE_MD_SOURCE' not found in fetched harness — leaving your CLAUDE.md untouched."
    return
  fi
  process_one_file "$_src" "$_dst" "CLAUDE.md" "$_lock" "$_decisions" "$_processed"
}

# ── Preserve, or remove, lock entries not seen in this run ───────────────────
# A lock entry this run never processed is one upstream stopped shipping (or
# CLAUDE.md, handled elsewhere). Under a MANIFEST path:
#   - file unedited (hash == lock)  -> deleted, its now-empty dirs pruned, entry dropped
#   - file edited                   -> kept, named, entry kept
#   - already gone                  -> entry dropped
# A user-added file is never in the lock, so it is never even considered.
# Deletion is skipped (with an error, and DELETION_ABORTED=1) when the fresh
# upstream looks corrupt: an empty file list, or a whole MANIFEST path missing.
DELETION_ABORTED=0
deletion_is_safe() {
  _manifest="$1"
  _fresh_list="$2"
  [ -s "$_fresh_list" ] || return 1
  while IFS= read -r _line; do
    _line=$(harness_manifest_path "$_line")
    [ -n "$_line" ] || continue
    [ -e "$HARNESS_TEMP_DIR/$_line" ] || return 1
  done < "$_manifest"
  return 0
}

# Print the MANIFEST path that covers lock key $1 (empty if none).
manifest_root_of() {
  _k="$1"
  _mf="$2"
  while IFS= read -r _l; do
    _l=$(harness_manifest_path "$_l")
    [ -n "$_l" ] || continue
    case "$_k" in "$_l"/*|"$_l") printf '%s' "$_l"; return 0 ;; esac
  done < "$_mf"
}

# Remove now-empty directories above file $1, stopping before MANIFEST root $2.
prune_empty_dirs() {
  _d=$(dirname "$1")
  while [ "$_d" != "$2" ] && [ "$_d" != "." ] && [ "$_d" != "/" ]; do
    rmdir "./$_d" 2>/dev/null || break
    _d=$(dirname "$_d")
  done
}

carry_over_unprocessed() {
  _lock="$1"
  _manifest="$2"
  _decisions="$3"
  _processed="$4"
  _fresh_list="$5"
  _removed_units="$HARNESS_TEMP_DIR/.update-removed-units"
  : > "$_removed_units"

  _can_delete=1
  if ! deletion_is_safe "$_manifest" "$_fresh_list"; then
    _can_delete=0
    DELETION_ABORTED=1
    log_error "The fetched upstream looks incomplete (empty file list or a MANIFEST path missing) — nothing was removed. Re-run once the upstream is whole."
  fi

  extract_lock_pairs "$_lock" | while IFS='	' read -r _k _h; do
    [ -n "$_k" ] || continue
    if grep -Fxq "$_k" "$_processed" 2>/dev/null; then
      continue
    fi
    if ! is_under_manifest "$_k" "$_manifest"; then
      printf '%s\t%s\n' "$_k" "$_h" >> "$_decisions"
      continue
    fi
    # A lock value is untrusted the moment it becomes a path: never let an
    # absolute path or a '..' segment reach rm.
    case "$_k" in
      /*|../*|*/../*|*/..|..)
        printf '%s\t%s\n' "$_k" "$_h" >> "$_decisions"
        log_warn "lock entry '$_k' is not a plain relative path — leaving it alone."
        continue ;;
    esac
    if [ "$_can_delete" -ne 1 ]; then
      printf '%s\t%s\n' "$_k" "$_h" >> "$_decisions"
      continue
    fi
    if [ ! -e "./$_k" ] && [ ! -L "./$_k" ]; then
      continue    # already gone: just drop the entry
    fi
    if [ -f "./$_k" ] && [ ! -L "./$_k" ] && [ "$(compute_file_hash "./$_k")" = "$_h" ]; then
      rm -f "./$_k"
      _root=$(manifest_root_of "$_k" "$_manifest")
      prune_empty_dirs "$_k" "$_root"
      # One "removed" line per unit: the top directory under the MANIFEST path
      # (a skill), or the file itself when it sits directly in it.
      _rest="${_k#"$_root"/}"
      case "$_rest" in
        */*) _unit="$_root/${_rest%%/*}" ;;
        *)   _unit="$_k" ;;
      esac
      if ! grep -Fxq "$_unit" "$_removed_units" 2>/dev/null; then
        printf '%s\n' "$_unit" >> "$_removed_units"
        log_info "removed '$_unit' — upstream no longer ships it and you never edited it."
      fi
    else
      printf '%s\t%s\n' "$_k" "$_h" >> "$_decisions"
      log_warn "upstream no longer ships '$_k' — you edited it, so it is kept (delete it yourself if you no longer want it)."
    fi
  done
}

# ── Rewrite .claude/harness-lock.json from the decisions file ────────────────
# Same JSON shape setup.sh writes: { "claude_md_source": "...", "files": { ... } }.
# _claude_md_source may be empty (T110 AC5: still unresolved this run) — in
# that case the field is simply omitted, same as an old pre-T110 lock, so the
# next update retries inference rather than recording a guess.
write_new_lock() {
  _decisions="$1"
  _lock="$2"
  _claude_md_source="$3"
  _sorted="$HARNESS_TEMP_DIR/.update-lock-sorted"
  # Unique by full line; keys are already unique so this only stabilizes order.
  LC_ALL=C sort -u "$_decisions" > "$_sorted"

  {
    printf '{\n'
    if [ -n "$_claude_md_source" ]; then
      _esc_src=$(printf '%s' "$_claude_md_source" | sed 's/\\/\\\\/g; s/"/\\"/g')
      printf '  "claude_md_source": "%s",\n' "$_esc_src"
    fi
    printf '  "files": {\n'
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

# ── Which harnesses does this run re-project? ────────────────────────────────
# Requested on the command line, plus every harness whose destination directory
# is already present — so an install made with `setup.sh --harness codex` stays
# up to date under a plain `bash update.sh` without any new state to keep.
# `claude` is resolved by this same "requested or present" rule as every other
# harness (T098) — it just checks presence at the two symlink destinations
# rather than at a MANIFEST dest column, because claude has no MANIFEST=dest
# pairs (it ships via harness_install_canon_symlinks, never a projected copy).
resolve_projection_harnesses() {
  _manifest="$1"
  _resolved=""
  for _h in $VALID_HARNESSES; do
    _want=0
    for _r in $HARNESSES; do
      [ "$_r" = "$_h" ] && _want=1
    done
    if [ "$_want" -eq 0 ]; then
      if [ "$_h" = "claude" ]; then
        # -e alone misses a broken (dangling) symlink, since it follows the
        # target — AC3 requires a broken/absolute link to still be repaired,
        # so presence also checks -L directly.
        { [ -e "./.claude/skills" ] || [ -L "./.claude/skills" ]; } && _want=1
        { [ -e "./.claude/agents" ] || [ -L "./.claude/agents" ]; } && _want=1
      else
        while IFS= read -r _line; do
          _dest=$(harness_manifest_dest "$_line" "$_h")
          [ -n "$_dest" ] || continue
          if [ -e "./$_dest" ]; then _want=1; break; fi
        done < "$_manifest"
      fi
    fi
    [ "$_want" -eq 1 ] && _resolved="$_resolved $_h"
  done
  PROJECTION_HARNESSES="$_resolved"
}


# ── Plan screen helpers (T114) ───────────────────────────────────────────────
# Everything below the menu is read-only until the user accepts the plan: these
# functions only hash, compare and write scratch lists under $HARNESS_TEMP_DIR.

# Print each line of file $1 indented, or $2 when the file is empty.
plan_list() {
  if [ -s "$1" ]; then
    sed 's/^/      /' "$1"
  else
    printf '      %s\n' "$2"
  fi
}

# Would Update stop and ask about this file? Same test as process_one_file's
# fast paths, in the same order: untouched since install, or already equal to
# upstream, means no question. $5=1 forces "ask" (CLAUDE.md source unknown).
plan_update_asks() {
  [ "${5:-}" = "1" ] && return 0
  _pa_cur=$(compute_file_hash "$2")
  _pa_rec=$(lookup_lock_hash "$4" "$3")
  [ -n "$_pa_rec" ] && [ "$_pa_cur" = "$_pa_rec" ] && return 1
  [ "$_pa_cur" = "$(compute_file_hash "$1")" ] && return 1
  return 0
}

# Does Reinstall have to move this file aside before copying the kit's version?
# Yes for anything that is not a plain file (a link, a directory), and for a file
# whose content differs from BOTH upstream and the lock — i.e. the user's edit,
# or content the kit never recorded. An unedited file is simply replaced.
reinstall_needs_backup() {
  [ -e "$2" ] || [ -L "$2" ] || return 1
  { [ -f "$2" ] && [ ! -L "$2" ]; } || return 0
  _rb_cur=$(compute_file_hash "$2")
  [ "$_rb_cur" = "$(compute_file_hash "$1")" ] && return 1
  _rb_rec=$(lookup_lock_hash "$4" "$3")
  [ -n "$_rb_rec" ] && [ "$_rb_cur" = "$_rb_rec" ] && return 1
  return 0
}

# ── Plan: what upstream stopped shipping (shared by Update and Reinstall) ────
# Same classification carry_over_unprocessed applies: an unedited file is listed
# (once per unit) in $4 for removal, an edited one in $5 to keep. Sets _p_safe=0
# when the fetched upstream looks incomplete, so nothing will be removed.
plan_removals() {
  _pr_lock="$1"
  _pr_manifest="$2"
  _pr_fresh="$3"
  _pr_rm="$4"
  _pr_keep="$5"
  : > "$_pr_rm"; : > "$_pr_keep"
  _p_safe=1
  deletion_is_safe "$_pr_manifest" "$_pr_fresh" || _p_safe=0
  extract_lock_pairs "$_pr_lock" | while IFS='	' read -r _k _h; do
    [ -n "$_k" ] || continue
    [ "$_k" = "CLAUDE.md" ] && continue
    grep -Fxq "$_k" "$_pr_fresh" 2>/dev/null && continue
    is_under_manifest "$_k" "$_pr_manifest" || continue
    case "$_k" in /*|../*|*/../*|*/..|..) continue ;; esac
    [ -e "./$_k" ] || [ -L "./$_k" ] || continue
    if [ -f "./$_k" ] && [ ! -L "./$_k" ] && [ "$(compute_file_hash "./$_k")" = "$_h" ]; then
      _root=$(manifest_root_of "$_k" "$_pr_manifest")
      _rest="${_k#"$_root"/}"
      case "$_rest" in
        */*) _unit="$_root/${_rest%%/*}" ;;
        *)   _unit="$_k" ;;
      esac
      grep -Fxq "$_unit" "$_pr_rm" 2>/dev/null || printf '%s\n' "$_unit" >> "$_pr_rm"
    else
      printf '%s\n' "$_k" >> "$_pr_keep"
    fi
  done
}

plan_print_removals() {
  if [ "$_p_safe" -eq 1 ]; then
    printf '  - Upstream no longer ships these and you never edited them; they will be removed:\n'
    plan_list "$1" "(none)"
  else
    printf '  - Removals skipped: the fetched upstream looks incomplete, so nothing will be removed.\n'
  fi
  printf '  - Upstream no longer ships these, but you edited them; they will be kept:\n'
  plan_list "$2" "(none)"
}

# ── Plan: Update ─────────────────────────────────────────────────────────────
# Classifies with the same rules the run applies (process_one_file for the
# fresh files, carry_over_unprocessed for what upstream stopped shipping), so
# the screen names the files the run then acts on.
plan_update() {
  _lock="$1"
  _manifest="$2"
  _fresh_list="$3"
  _p_ask="$HARNESS_TEMP_DIR/.plan-ask"
  _p_rm="$HARNESS_TEMP_DIR/.plan-remove"
  _p_keep="$HARNESS_TEMP_DIR/.plan-keep"
  : > "$_p_ask"; : > "$_p_rm"; : > "$_p_keep"
  _p_new=0

  while IFS= read -r _rel <&3; do
    [ -n "$_rel" ] || continue
    if [ ! -e "./$_rel" ]; then
      _p_new=$((_p_new + 1))
    elif plan_update_asks "$HARNESS_TEMP_DIR/$_rel" "./$_rel" "$_rel" "$_lock"; then
      printf '%s\n' "$_rel" >> "$_p_ask"
    fi
  done 3< "$_fresh_list"

  resolve_claude_md_source "$_lock" ./CLAUDE.md
  if [ ! -e ./CLAUDE.md ]; then
    _p_new=$((_p_new + 1))
  elif [ "$CLAUDE_MD_SOURCE" = "conflict" ]; then
    printf '%s\n' "CLAUDE.md" >> "$_p_ask"
  elif [ -f "$HARNESS_TEMP_DIR/$CLAUDE_MD_SOURCE" ] \
       && plan_update_asks "$HARNESS_TEMP_DIR/$CLAUDE_MD_SOURCE" ./CLAUDE.md CLAUDE.md "$_lock"; then
    printf '%s\n' "CLAUDE.md" >> "$_p_ask"
  fi

  plan_removals "$_lock" "$_manifest" "$_fresh_list" "$_p_rm" "$_p_keep"

  printf '\n'
  printf 'Plan: Update Easy Kit in %s (keeps your edits)\n' "$(pwd)"
  printf '  - Kit files you never edited are refreshed from upstream.\n'
  printf '  - Files to add or restore: %s\n' "$_p_new"
  if [ "$TTY_OK" -eq 1 ]; then
    printf '  - You edited these; you will be asked about each one ([o]verwrite / [s]kip):\n'
  else
    printf '  - You edited these; with no terminal they are kept as they are:\n'
  fi
  plan_list "$_p_ask" "(none)"
  plan_print_removals "$_p_rm" "$_p_keep"
  printf '  - Backed up: nothing. Update keeps your edits in place instead.\n'
  printf '  - Hooks: Easy Kit entries are merged into .claude/settings.json (your own entries are kept).\n'
}

# ── Plan: Reinstall ──────────────────────────────────────────────────────────
# Writes the exact backup list to $1; run_reinstall moves those files and no
# others, so what the screen shows is what happens.
plan_reinstall() {
  _backups="$1"
  _lock="$2"
  _fresh_list="$3"
  _manifest="$4"
  _p_rm="$HARNESS_TEMP_DIR/.plan-remove"
  _p_keep="$HARNESS_TEMP_DIR/.plan-keep"
  : > "$_backups"
  while IFS= read -r _rel <&3; do
    [ -n "$_rel" ] || continue
    reinstall_needs_backup "$HARNESS_TEMP_DIR/$_rel" "./$_rel" "$_rel" "$_lock" \
      && printf '%s\n' "$_rel" >> "$_backups"
  done 3< "$_fresh_list"
  reinstall_needs_backup "$HARNESS_TEMP_DIR/$CLAUDE_SRC" ./CLAUDE.md CLAUDE.md "$_lock" \
    && printf '%s\n' "CLAUDE.md" >> "$_backups"
  plan_removals "$_lock" "$_manifest" "$_fresh_list" "$_p_rm" "$_p_keep"

  printf '\n'
  printf 'Plan: Reinstall Easy Kit in %s (backs up your edits)\n' "$(pwd)"
  printf '  - Every kit file is replaced with a fresh copy, and the lock is rewritten.\n'
  printf '  - Project type: %s\n' "$(project_type_label)"
  printf '  - Your edited files are moved to <file>.bak first:\n'
  plan_list "$_backups" "(none: no kit file has been edited)"
  plan_print_removals "$_p_rm" "$_p_keep"
  printf '  - Your own files that the kit does not ship are left alone.\n'
  printf '  - Hooks: Easy Kit entries are merged into .claude/settings.json (your own entries are kept).\n'
}

# ── Re-project every selected/already-present harness (shared by both actions)
reproject_harnesses() {
  _manifest="$1"
  resolve_projection_harnesses "$_manifest"
  _rp_done=""
  _rp_linked=0
  for _rp_h in $PROJECTION_HARNESSES; do
    # claude has no MANIFEST=dest pairs to project — its install is the symlink
    # step below, so it is not added to the "re-projected" summary.
    [ "$_rp_h" = "claude" ] && continue
    log_info "Re-projecting canon for harness '$_rp_h'."
    harness_project_manifest "$HARNESS_TEMP_DIR" "." "$_manifest" "$_rp_h" || {
      log_error "Update aborted: harness projection for '$_rp_h' failed. The target tree may be partial."
      exit 2
    }
    _rp_done="$_rp_done $_rp_h"
  done
  # Re-point .claude/{skills,agents} only when claude was requested or already
  # present (T098). Fails the run (set -e) rather than reporting success over a
  # partial fix.
  case " $PROJECTION_HARNESSES " in
    *" claude "*) harness_install_canon_symlinks . ; _rp_linked=1 ;;
  esac
  if [ -n "$_rp_done" ]; then
    log_info "Re-projected harness(es):$_rp_done"
  fi
  if [ "$_rp_linked" -eq 1 ]; then
    log_info "Harness 'claude': re-pointed .claude/{skills,agents} at the plain-root canon."
  fi
  if [ -z "$PROJECTION_HARNESSES" ]; then
    log_info "No harness detected in this project — none requested, none already present."
    log_info "Run 'update.sh --harness <name>' to install one. Valid harnesses: $VALID_HARNESSES"
  fi
}

# ── The Update action (update.sh's former main, after the fetch) ─────────────
run_update() {
  _lock="$1"
  _manifest="$2"
  _fresh_list="$3"
  decisions="$HARNESS_TEMP_DIR/.update-decisions"
  processed="$HARNESS_TEMP_DIR/.update-processed"
  : > "$decisions"; : > "$processed"

  process_files "$_lock" "$_fresh_list" "$decisions" "$processed"
  process_claude_md "$_lock" "$decisions" "$processed"
  carry_over_unprocessed "$_lock" "$_manifest" "$decisions" "$processed" "$_fresh_list"
  write_new_lock "$decisions" "$_lock" "$FINAL_CLAUDE_MD_SOURCE"

  # AFTER the file copy, so every hook the merged entries reference is on disk
  # (memory/learnings.md, T074).
  update_settings
  reproject_harnesses "$_manifest"
  log_info "Update complete. Re-recorded $_lock"

  if [ "$UNRESOLVED" -gt 0 ]; then
    log_error "$UNRESOLVED conflict(s) could not be resolved (no interactive input). Re-run setup.sh in a terminal and choose Update to resolve them."
    exit 2
  fi
  if [ "$SETTINGS_FAILED" -ne 0 ]; then
    log_error "Update finished, but Easy Kit hooks were NOT merged (see the message above)."
    exit 2
  fi
  if [ "$DELETION_ABORTED" -ne 0 ]; then
    log_error "Update finished, but removal of files upstream no longer ships was skipped (see the message above)."
    exit 2
  fi
}

# ── The Reinstall action (T114) ──────────────────────────────────────────────
# Backs up exactly the files plan_reinstall listed (T112 helper, per file), then
# copies every fresh kit file, applies the removal contract (as Update), and
# rewrites the lock from the fresh list plus what that keeps — never
# from a disk scan, so a user's own file under a kit directory is not recorded
# as the kit's (a later Update would otherwise delete it as "no longer shipped").
# MANIFEST `!` exclusions are honoured because the fresh list already omits them.
run_reinstall() {
  _lock="$1"
  _manifest="$2"
  _fresh_list="$3"
  _backups="$4"
  _decisions="$HARNESS_TEMP_DIR/.reinstall-decisions"
  : > "$_decisions"

  { cat "$_fresh_list"; printf '%s\n' "CLAUDE.md"; } > "$HARNESS_TEMP_DIR/.reinstall-list"
  while IFS= read -r _rel <&3; do
    [ -n "$_rel" ] || continue
    _src="$HARNESS_TEMP_DIR/$_rel"
    [ "$_rel" = "CLAUDE.md" ] && _src="$HARNESS_TEMP_DIR/$CLAUDE_SRC"
    [ -f "$_src" ] || continue
    if grep -Fxq "$_rel" "$_backups"; then
      harness_backup_path "$_src" "./$_rel" || exit 1
    fi
    install_file "$_src" "./$_rel"
    printf '%s\t%s\n' "$_rel" "$(compute_file_hash "$_src")" >> "$_decisions"
  done 3< "$HARNESS_TEMP_DIR/.reinstall-list"
  # T113's contract, as in Update: what upstream stopped shipping is removed if
  # unedited, kept (and kept in the lock) if edited; a non-MANIFEST entry stays.
  carry_over_unprocessed "$_lock" "$_manifest" "$_decisions" "$HARNESS_TEMP_DIR/.reinstall-list" "$_fresh_list"
  write_new_lock "$_decisions" "$_lock" "$CLAUDE_SRC"

  update_settings
  reproject_harnesses "$_manifest"
  log_info "Reinstall complete. Re-recorded $_lock"
  if [ "$SETTINGS_FAILED" -ne 0 ]; then
    log_error "Reinstall finished, but Easy Kit hooks were NOT merged (see the message above)."
    exit 2
  fi
  if [ "$DELETION_ABORTED" -ne 0 ]; then
    log_error "Reinstall finished, but removal of files upstream no longer ships was skipped (see the message above)."
    exit 2
  fi
}
