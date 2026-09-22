#!/bin/sh
# update.sh — thin alias for the Update action of the one Easy Kit command (ADR-0002).
# setup.sh detects the install and offers Update / Reinstall / Cancel with a plan
# screen; this file only keeps existing `update.sh` references working. The
# EASYKIT_ACTION seam is internal (it refuses to run where nothing is installed).
set -e
_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
if [ ! -f "$_dir/setup.sh" ]; then
  printf '[error] update.sh is now part of the one Easy Kit command. Run this inside your project and choose Update:\n' >&2
  printf '  curl -fsSL https://raw.githubusercontent.com/thunderkds/personal-agentic-claude/main/setup.sh | sh\n' >&2
  exit 1
fi
EASYKIT_ACTION=update exec sh "$_dir/setup.sh" "$@"
