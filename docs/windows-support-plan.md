# Windows support plan

Mode: auto. Track: extended (C2+, Risk High, many sessions, touches the installer and every hook).
Status: plan only. No code written. Nothing is registered on `PROJECT_KANBAN.md` yet.

## Verdict

Scope (user, after the first draft): native Windows only. WSL2 is out of scope: no WSL docs, no WSL detection.
Seven tasks. Do the CI job early, because nothing else is verified without it.

## What breaks on native Windows today

Found by scanning the repo (facts, not guesses):

| # | Area | Evidence | Why it fails on Windows |
|---|---|---|---|
| 1 | Installer | `setup.sh` (910 lines), `update.sh`, `lib/harness-fetch.sh` (546), `lib/harness-update.sh` (949) | Bash only. Uses GNU `sed -i`, `mktemp`, `realpath` and similar (8 hits). |
| 2 | Symlinks | `.claude/skills` and `.claude/agents` are load-bearing relative symlinks (`AGENTS.md`, `harness_install_canon_symlinks`) | Creating a symlink on Windows needs Developer Mode or admin. Git needs `core.symlinks=true`. |
| 3 | File locks | `fcntl.flock` in `post_tool_trace.py:183`, `lib/auto_closeout.py:192`, `scripts/verify_trace.py:50` | `fcntl` does not exist on Windows. The hook raises `ImportError`. |
| 4 | Process control | `os.killpg` + `signal.SIGKILL` + `start_new_session` in `stop_auto_verify.py:206,373,380` | No process groups or `SIGKILL` on Windows. Auto verify cannot start or time out. |
| 5 | Hook commands | `.claude/settings.json`: `python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/*.py` (10 hooks) | `python3` is often missing on Windows (the launcher is `py` or `python`). `$VAR` quoting differs under cmd and PowerShell. |
| 6 | Bash-command parser | `pre_bash_block_unsafe_merge.py` uses `shlex` POSIX mode and `/dev/null` (line 852) | Claude Code on Windows may run PowerShell. The merge gate would not parse those commands. This is a safety gap, not only a crash. |
| 7 | Git guardrail | `skills/git-guardrails-claude-code/scripts/block-dangerous-git.sh` | A `.sh` hook needs bash on PATH. |
| 8 | Tests | 19 `tests/*.sh` plus `tests/lib/pty.sh`; 115 Python test files | Shell tests cannot run natively. `pty` is POSIX only. |
| 9 | Paths | `pre_tool_sensitive_path.py` already normalises `\` to `/` (lines 145-188) | Good: partial Windows awareness exists. Other hooks have not been checked. |
| 10 | Line endings | Shell and Python files in a Windows checkout | `core.autocrlf=true` turns `#!/bin/bash\r` into a broken shebang. Needs `.gitattributes` (`eol=lf`). |

Not a blocker: the Python hooks already use `os.path`, `os.replace` and `os.makedirs(mode=0o700)` (the mode is
ignored on Windows, not an error).

## Tasks (in this order)

Each task gets a `tasks/TASK_GUIDE_Txxx.md` at Stage 2 and a test that can fail (Gate 5).

| Task | Goal | C / Risk | Depends on |
|---|---|---|---|
| T-W1 | **Decision record (ADR) plus `.gitattributes`.** Pick the native shell target, the Python launcher and the installer language (see "Open decision"). Add `.gitattributes` (`* text=auto eol=lf`, `*.sh text eol=lf`) so a Windows checkout keeps LF line endings (fixes row 10). | C1 / Low | none |
| T-W2 | **Windows CI.** A GitHub Actions `windows-latest` job that runs the Python tests. Mark POSIX-only tests with a skip reason (shell tests, `pty`). Expect red at first; the job lists what T-W3..T-W6 must fix. T-W7 adds the `setup.ps1` smoke install to it. Gate: the job is required before T-W3 moves to Done. | C2 / Medium | T-W1 |
| T-W3 | **Portable file lock.** One helper `lib/filelock.py` (`msvcrt.locking` on Windows, `fcntl.flock` elsewhere). Replace the 3 `fcntl` uses. Test: two processes append to the same trace file, no lost line, on Linux now and Windows in CI. | C2 / Medium | T-W2 |
| T-W4 | **Portable process control.** One helper `lib/proc.py`: start detached (`CREATE_NEW_PROCESS_GROUP` on Windows, `start_new_session` elsewhere), kill the tree (`taskkill /T /F` on Windows, `killpg` elsewhere). Replace the 3 uses in `stop_auto_verify.py`. Test: a child that sleeps is killed on timeout. | C2 / High | T-W2 |
| T-W5 | **Hook launcher.** Make the 10 hook commands launcher-independent: either a tiny `hooks/run.py` shim called as `python`/`py`, or per-OS settings written by the installer. Plugin `hooks.json` gets the same fix. Test: every hook command in `settings.json` resolves on a Windows runner. | C2 / High | T-W2 |
| T-W6 | **Merge-gate parser for PowerShell.** Extend `pre_bash_block_unsafe_merge.py` and `lib/session_work.py` to tokenise `git merge`, `git push`, and `git branch -D` written in PowerShell (and cmd, if the ADR keeps it). Fail closed: an unparsable command on Windows is blocked, not allowed. Test: the existing gate test matrix, replayed with PowerShell quoting. | C3 / High | T-W5 |
| T-W7 | **Native installer `setup.ps1` / `update.ps1`.** Port the menu, backups, settings merge and canon install. Replace symlinks with real directory junctions where permitted, else a copy plus a drift check that `update` re-runs. Keep `setup.sh` as the source of truth for behaviour; compare outputs in a parity test. | C3 / High | T-W3..T-W6 |

The `git-guardrails` hook (row 7) is rewritten as a Python script inside T-W5, so it needs no bash.

## Decided: installer language

PowerShell port (`setup.ps1`, `update.ps1`) for T-W7. `setup.sh` stays untouched. A parity test keeps the two in step.
Chosen by the user on 2026-11-06 ("as you recommend"). T-W1 no longer debates this; it records it in the ADR.

## Decisions already made

| Decision | Choice | Reason |
|---|---|---|
| Scope | Native Windows only; WSL2 dropped | You said so |
| Python is the common runtime | Yes | Fact: hooks are already Python; only the installer is shell |
| PowerShell merge parser fails closed | Yes | The Hard-Stop Gates are not skippable |
| Installer language | PowerShell port; `setup.sh` untouched | User, 2026-11-06 |
| Symlink fallback | Junction, then copy plus drift check | Never silently break `.claude/skills`; revisit in T-W1 |

Still open: the symlink fallback. Risk is High, so T-W1 runs it as a 3-Advocate Debate unless you decide it first.

## Cut list (deliberately not planned)

- cmd.exe-only environments, if T-W1 picks PowerShell.
- Windows ARM, and Git Bash as a separate target.
- Codex and Cursor on native Windows: they have no hooks (`AGENTS.md` "Non-Claude CLIs"), so only the docs change.
- Signing or packaging `setup.ps1` (winget, Scoop).

## Risks

1. The merge gate is a safety control. A Windows parser that is too loose breaks Gate enforcement. Mitigation: T-W6 fails closed and replays the full gate test matrix.
2. Auto verify (`stop_auto_verify.py`) has the most moving parts on Windows (detached process, kill tree, `claude` on PATH). Mitigation: T-W4 tests it in isolation before T-W7.
3. Pin tests fail on later tasks (LR-0004). Mitigation: each task repoints its own pin before the verify run.
4. Without the Windows CI job all Windows work is unverified. Mitigation: T-W2 comes right after the decision record.

## Next step

Register T-W1 on the board, then write its `TASK_GUIDE`. Board IDs: T-W1 = T262 (guide written, Todo), T-W2 = T263, T-W3 = T264, T-W4 = T265, T-W5 = T266, T-W6 = T267, T-W7 = T268. T263..T268 are reserved here; their guides and board rows come when each is picked up.
