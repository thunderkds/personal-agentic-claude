#!/bin/sh
# tests/lib/pty.sh — terminal helpers for the installer suites (T114).
#
# Since T114 every installer prompt reads /dev/tty, never stdin. Two things
# follow for a test:
#
#   * `</dev/null` alone no longer means "non-interactive": a suite started from
#     a developer's terminal would still reach /dev/tty and wait at the menu.
#     detach_from_terminal re-runs the whole suite in a new session (setsid), so
#     every plain run takes the no-terminal path exactly as it does in CI.
#   * Answers can no longer be piped into stdin. run_in_pty drives the command
#     inside a real pty (`script -qec`), which reaches /dev/tty prompts a pipe
#     cannot (memory/learnings.md, T108). Answers are queued up front; each prompt
#     reads one line.

#
# Sourcing this file also runs hide_real_clis: since T115 the CLI menu
# pre-selects whichever of `claude` / `codex` is on PATH, so a developer machine
# with either installed would silently change every suite's defaults. Suites
# that need a CLI "installed" put a fake executable on PATH themselves.

hide_real_clis() {
  _hc_new=""
  _hc_ifs=$IFS
  IFS=:
  for _hc_d in $PATH; do
    if [ -x "$_hc_d/claude" ] || [ -x "$_hc_d/codex" ]; then continue; fi
    _hc_new="${_hc_new:+$_hc_new:}$_hc_d"
  done
  IFS=$_hc_ifs
  PATH=$_hc_new
  export PATH
  for _hc_t in git python3 script sh mktemp; do
    command -v "$_hc_t" >/dev/null 2>&1 && continue
    printf 'FATAL: hiding claude/codex from PATH also hid %s (same directory). Move one of them, then re-run.\n' "$_hc_t" >&2
    exit 2
  done
}
hide_real_clis

# usage: detach_from_terminal "$0" "$@"   (call once, near the top of a suite)
detach_from_terminal() {
  [ -n "${EASYKIT_TEST_DETACHED:-}" ] && return 0
  ( : </dev/tty ) 2>/dev/null || return 0   # no terminal already (CI, setsid)
  if command -v setsid >/dev/null 2>&1; then
    EASYKIT_TEST_DETACHED=1 exec setsid -w bash "$@"
  fi
  printf 'FATAL: cannot detach this suite from your terminal (no setsid on PATH); the installer would wait at its menu. Run it where setsid exists, or without a controlling terminal.\n' >&2
  exit 2
}

# usage: run_in_pty '<answers, printf %b escapes>' '<shell command string>'
# Exit status is the command's own (script -e). Output includes the echoed
# answers and CRLF line ends, as a terminal would show them.
run_in_pty() {
  printf '%b' "$1" | SHELL=/bin/sh script -qec "$2" /dev/null
}
