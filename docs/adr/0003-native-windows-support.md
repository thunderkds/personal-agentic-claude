# 0003. Native Windows support

**Status**: Accepted (user, 2026-11-06)
**Date**: 2026-11-06
**Deciders**: User (thunderkds), Supervisor
**Related**: tasks T262 (this record, `.gitattributes`) · T263..T268 (the work it plans) · `docs/windows-support-plan.md` · `ADR-0001` (temp-clone install) · `ADR-0002` (one menu-driven installer)

---

## Context

Easy Kit runs today on macOS and Linux only. A scan of the repo (`docs/windows-support-plan.md`, ten findings) shows what breaks on native Windows:

- The installer (`setup.sh`, `update.sh`, `lib/*.sh`) is Bash.
- `.claude/skills` and `.claude/agents` are load-bearing relative symlinks. Creating a symlink on Windows needs Developer Mode or admin rights, and git needs `core.symlinks=true`.
- Three hooks and scripts import `fcntl`, and `stop_auto_verify.py` uses `os.killpg` and `SIGKILL`. Neither exists on Windows.
- The eleven hook commands in `.claude/settings.json` call `python3`, which is often missing on Windows.
- A Windows checkout with `core.autocrlf=true` turns `#!/bin/bash` into `#!/bin/bash\r`, a broken shebang.

**Hard to reverse**: the installer language and the shell target decide which files the project must keep in step for years. **Surprising without context**: the kit gets a second installer in a second language, while `setup.sh` stays as it is. **Genuine trade-off**: four shapes were weighed (see Alternatives Considered).

On 2026-11-06 the user set the scope: "by pass the wsl, focus on the native window".

---

## Decision

We will support Windows through the native tool chain only. Five decisions follow, each with its own heading.

### 1. Native Windows only (no WSL2)

The target is native Windows with Claude Code running on Windows. WSL2 gets no documentation and no detection in the installer. Inside WSL2 the kit already runs as Linux. Also out of scope: Windows ARM, Git Bash as a separate target, and `cmd.exe`-only environments.

### 2. PowerShell is the shell target

PowerShell is the one Windows shell the kit supports. The installer (`setup.ps1`, `update.ps1`) and any Windows-side command text target it. The merge-gate parser (T267) tokenizes PowerShell quoting and fails closed: an unparsable command on Windows is blocked, never allowed. The Hard-Stop Gates stay as strong on Windows as on Linux.

### 3. Python launcher: `py -3`, else `python`

On Windows the Python launcher is `py -3`, and `python` when `py` is absent. `python3` stays the name on macOS and Linux. Python stays the common runtime: the hooks are already Python, and only the installer is shell. The hook commands in `.claude/settings.json` and the plugin `hooks.json` become launcher-independent in T266.

### 4. Installer language: a PowerShell port

We will write `setup.ps1` and `update.ps1` as a port of the installer. `setup.sh` stays untouched and stays the source of truth for behavior. A parity test runs both and compares what they do, so the two stay in step. The user chose this on 2026-11-06 ("as you recommend"). T268 builds it, after the Python fixes T264..T267 land.

### 5. Symlink fallback: junction first, else copy plus drift check

The installer links `.claude/skills` and `.claude/agents` onto the plain-root canon (`skills/`, `agents/`). On Windows it tries a directory junction first, because a junction needs no admin rights. When a junction cannot be made, it copies the canon into those two paths and records that it did. A drift check then compares the copy with the canon, and `update` re-runs that check, so the copy never goes stale in silence. The install never breaks `.claude/skills` without telling the user.

Source of this decision: the user's default. The Supervisor offered it on 2026-11-06 and the user went on without changing it. No Debate ran, because the task is Risk Low. T268 designs the drift check in detail.

### Line endings (T262)

A root `.gitattributes` sets `* text=auto eol=lf`, so a Windows checkout keeps LF in shell and Python files whatever `core.autocrlf` says. It marks `*.png`, `*.jpg`, `*.ico` and `*.woff2` as `binary`. It does not change how git stores the symlinks under `plugin/`.

---

## Alternatives Considered

| Alternative | Pros | Cons | Why not chosen |
|-------------|------|------|----------------|
| PowerShell port of the installer (`setup.ps1`), `setup.sh` untouched | Native, no extra tool for the user; `setup.sh` risk stays zero | Two installers to keep in step | **Selected** |
| Rewrite the installer in Python, one file for all systems | One code path | Rewrites a working, tested 910-line installer; `curl \| sh` Quick Start changes; high risk | Too large for the gain; the user chose the port |
| Require Git Bash and run `setup.sh` as is | Smallest change | Bash on PATH is an extra install; hooks still break on `fcntl`, `killpg` and `python3` | Fixes only the installer, not the hooks |
| Support WSL2 | Kit already runs as Linux there | Does not serve a native Windows user | The user dropped WSL2 from scope |
| Symlink only, require Developer Mode | No fallback code | The install fails for a user without it | A junction or copy works without admin rights |

---

## Consequences

### Positive
- A native Windows user can install and run the kit without WSL2 or Bash.
- `setup.sh` and every Linux and macOS path stay untouched, so the port cannot regress them.
- Windows CI (T263) shows what is still red, so each later task has a measurable target.

### Negative (accepted trade-offs)
- Two installers must stay in step. The parity test lowers that cost but does not remove it.
- A copy fallback can drift from the canon. The drift check on every `update` contains it.
- `cmd.exe`-only users get no support.

### Follow-up
- [ ] T263: Windows CI job (`windows-latest`) that runs the Python tests.
- [ ] T264: portable file lock instead of `fcntl`.
- [ ] T265: portable process start and kill instead of `killpg` and `SIGKILL`.
- [ ] T266: launcher-independent hook commands, `block-dangerous-git` rewritten in Python.
- [ ] T267: merge-gate parser for PowerShell, fail closed.
- [ ] T268: `setup.ps1` and `update.ps1`, the junction and copy fallback, the parity test.

### Addendum (T276, 2026-11-07): what the v2.3.0 beta does not claim

A first real Windows run (Windows 11, Python 3.15, no Developer Mode) passed install, update and the T272 preflight. It also showed two risks that Linux cannot prove. Both stay **unverified** in the beta. Neither is a promise.

- **Plugin install on Windows is unverified.** `plugin/` is a folder of git symlinks. A Windows clone without the symlink right turns them into plain files, and 8 tests in `tests/test_plugin_source.py` fail there. Claude Code's marketplace install may dereference the links on its own, as it does on Linux (T242), but nobody has checked on Windows. **The supported Windows install is `setup.ps1`.** Those 8 tests are skipped on Windows with this reason.
- **The agent-write deny rule is unverified on Windows.** `Edit(~/.claude/projects/**/*.jsonl)` (T251) is written with `/` and `~`. Whether Claude Code matches it against a Windows path is not tested. `test_ac5_record_lives_where_settings_json_denies_agent_writes` fnmatches a Windows path against a POSIX glob, so it is skipped on Windows with this reason. A person checks the real behavior with step 9 of `docs/windows-manual-checklist.md`.
- **Follow-up change:** the `block-dangerous-git` Python twin listed under T266 was cut from T266. T277 builds it.
