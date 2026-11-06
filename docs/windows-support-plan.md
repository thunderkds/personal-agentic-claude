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
| 5 | Hook commands | `.claude/settings.json`: `python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/*.py` (11 hook commands) | `python3` is often missing on Windows (the launcher is `py` or `python`). `$VAR` quoting differs under cmd and PowerShell. |
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
| T-W5 | **Hook matchers and the Windows hook form (built as T266).** Matchers `Bash\|PowerShell` in `settings.json` and `hooks.json`; the sensitive-path and memory hooks accept the PowerShell tool; `merge-settings.py` and `project_root.py` read `args`; `lib/windows_hooks.py` converts the kit hooks to exec form (`py -3`/`python`, no shell) for the installer. Plugin `hooks.json` commands stay `python3` on Windows (known limit). | C3 / High | none |
| T-W6 | **Merge gate and the PowerShell tool (built as T267).** The gate reads `tool_name` "PowerShell" like Bash. For the PowerShell tool it never narrows to one task and uses one rule: strip backtick, `^`, `+` and quotes, then any push, merge, rebase, pull or `alias.` word anywhere goes to the whole-board check. On Git Bash (Bash tool on win32) a same-line `git.exe ... verb` fallback runs. No PowerShell lexer (Debate, 3 Advocates). Known limit: a verb built at run time. | C3 / High | none |
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
5. On Windows the file lock is mandatory (`msvcrt`) and sits on byte 0 of the trace file. `stop_auto_mode_check.py` (about lines 212-219) reads that trace without a lock, so a read during a hook append can raise `PermissionError`. It is caught and counted as an empty trace, so check 7 ("no test run in the trace") could fire wrongly. Found in the T264 review. Watch for it in the first Windows CI run; fix by a retry-once on `PermissionError` in the unlocked readers.
6. `.claude/hooks/lib/filelock.py` shares its name with the PyPI package `filelock` (a `tox`/`virtualenv` dependency). Hooks put `lib` first on `sys.path`, so they are safe; a test session that imported the PyPI package first would not be. Rename to `portable_lock` if it ever bites.
7. T263 skips about 114 `tests/test_auto_verify.py` tests on Windows because they use `#!` stub `claude` scripts and a `/usr/bin:/bin` PATH. Until a portable stub exists, Windows CI has almost no coverage of `stop_auto_verify.py`. No planned task covers it. Candidate follow-up: T-W2b, portable stub for the auto verify tests (needed before T268 can claim auto verify works on Windows).
8. **Follow-up T270 (candidate, all OSes):** `GIT_ALIAS_PATTERN` in `pre_bash_block_unsafe_merge.py` (about line 122) is quadratic. A 240 KB command takes about 68 s, past the default 60 s hook timeout, and a timed-out hook does not block, so the push runs. Present on the base code; found in the T267 review. Fix: make it linear and add a `main()`-level timing test, or fail closed above a length cap.
9. **Follow-up (candidate):** `site/docs.html:1972-1977` and `skills/git-guardrails-claude-code/SKILL.md:33` still show the matcher `Bash`; update after T266 merges. The git-guardrails Python twin moves to T268.

## Release (user, 2026-11-06: "this will be the new version that support window")

The finished Windows work ships as a new kit version. Today: v2.2.0 (`.claude-plugin/plugin.json`, `plugin/.claude-plugin/plugin.json`, `README.md` line 3; tags v2.0.0..v2.2.0).
Version: **v2.3.0**, confirmed by the user on 2026-11-06 (a minor bump: Windows is added and POSIX behaviour does not change).
Task **T-W8 = T269** (reserved): bump the three version strings, add a README "Windows" section (install steps for `setup.ps1`, the symlink fallback, known limits), write release notes and a rollback plan with the `ship` skill. It runs last, after T268 and a green Windows CI run. No tag is created and nothing is pushed without the user.

## Next step

Register T-W1 on the board, then write its `TASK_GUIDE`. Board IDs: T-W1 = T262 (guide written, Todo), T-W2 = T263, T-W3 = T264, T-W4 = T265, T-W5 = T266, T-W6 = T267, T-W7 = T268. T263..T268 are reserved here; their guides and board rows come when each is picked up.
