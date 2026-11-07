# Windows parity ledger

Date: 2026-11-07 (T273). Goal: the kit on native Windows behaves like the kit on Ubuntu.
This file is the measure. It lists every hook, script, library, installer entry point and shell test,
and says how each one is proven on Windows. `tests/test_windows_parity_ledger.py` fails when a file is
missing from the table, when a row has no reason, when a cited proof file does not exist, or when the
skip counts are wrong. It checks the shape and the counts only. A person must check that a status is true
(a `covered` row is not checked against the test's content), so review the prose when you change a row.

Windows CI run seen: no

A manual run on a real Windows machine (2026-11-07, Python 3.15, no Developer Mode) passed install, update and the T272 preflight. Its test run ended early (63 failed, 1111 passed, a test hung). T274 to T277 answer it: the test suite skips what a machine cannot do (T274), hook messages name a launcher that exists (T275), the plugin and deny-rule risks are written down (T276), and the git guardrail has a Windows form (T277). The manual end-to-end steps are in `docs/windows-manual-checklist.md`.

"No" means the `Python tests (Windows)` job (`.github/workflows/windows.yml`) has not run yet, so every
`covered` below means "a test exists that runs on Windows", never "it passed on Windows". Change the line
to `yes (<run URL>)` after the first run, then fix what the run shows.

## Status words

| Status | Meaning |
|---|---|
| covered | The same code runs on both systems, or a Windows twin exists, and a test for it runs in the Windows job. |
| partial | Some of it is tested on Windows. The reason says what is not. |
| gap | Nothing proves it on Windows. The reason says how to close it. |
| n/a | Windows does not use this file. The reason names the Windows twin or the decision. |

## Ledger

| Item | Ubuntu proof | Windows proof | Status | Reason / how to close |
|---|---|---|---|---|
| `setup.sh`, `update.sh` | `tests/test_setup.sh`, `tests/test_update.sh` | `setup.ps1`, `update.ps1` | n/a | POSIX installers. Windows runs the PowerShell twins (ADR-0003 decision 3). |
| `harness-fetch.sh`, `harness-update.sh` | `tests/test_harness_fetch.sh` | `lib/harness.ps1`, `lib/harness-update.ps1` | n/a | POSIX libraries. Ported to the two PowerShell libraries. |
| `setup.ps1`, `update.ps1`, `harness.ps1`, `harness-update.ps1` | `tests/test_setup_ps1_pwsh.py`, `tests/test_update_ps1_pwsh.py` (Linux pwsh in Docker) | `.github/workflows/windows.yml`, `tests/windows/smoke-install.ps1`, `tests/windows/smoke-update.ps1` | partial | No Windows run seen. Linux pwsh cannot prove junctions, CRLF or `core.symlinks=false`. T272 adds the check that stops the installer before it writes when the fetched kit has no Windows support. |
| `smoke-install.ps1`, `smoke-update.ps1` | `tests/test_setup_ps1_pwsh.py` | `.github/workflows/windows.yml` | covered | Run by the Windows job under PowerShell 5.1 and 7. |
| `smoke-install.sh` | `tests/test_setup.sh` | `tests/windows/smoke-install.ps1` | n/a | POSIX smoke test. Windows twin is `smoke-install.ps1`. |
| `merge-settings.py`, `windows_hooks.py` | `tests/test_windows_hooks.py` | `tests/test_windows_hooks.py` | covered | Python, same code on both systems. |
| `post_tool_trace.py`, `filelock.py` | `.claude/hooks/tests/test_filelock.py` | `.claude/hooks/tests/test_filelock.py` | covered | T264 replaced `fcntl` with one portable lock. |
| `pre_bash_block_unsafe_merge.py`, `shell_data.py` | `.claude/hooks/tests/test_merge_gate_guard.py` | `.claude/hooks/tests/test_windows_merge_gate.py` | partial | T267 tests the PowerShell spellings of git writes. Two merge-gate tests are `posix_only` (see Skip inventory). To close: port them with a portable stub. |
| `stop_auto_verify.py`, `proc.py`, `auto_closeout.py`, `trace_chain.py`, `verify_record.py` | `tests/test_auto_verify.py` | `.claude/hooks/tests/test_proc.py` | partial | 115 `posix_only` tests in `tests/test_auto_verify.py` skip on Windows (they need a stub `claude` and a POSIX session). Start, timeout and kill are not tested end to end on Windows. To close: a portable stub `claude` (follow-up T-W2b in `docs/windows-support-plan.md`). |
| `stop_auto_mode_check.py`, `auto_mode.py`, `session_work.py` | `.claude/hooks/tests/test_t250_session_ownership.py` | `.claude/hooks/tests/test_t252_marked_ownership.py` | partial | Part of the ownership tests are `posix_only`. To close: same stub as the row above. |
| `pre_tool_sensitive_path.py` | `.claude/hooks/tests/test_vital_slice.py` | `.github/workflows/windows.yml` | covered | Already normalises `\` to `/`; its tests run in the Windows job. |
| `post_agent_move_to_review.py`, `post_bash_memory_update.py`, `post_write_register_task.py`, `pre_agent_step_limit.py`, `pre_agent_validate_guide.py`, `stop_review_reminder.py` | `.claude/hooks/tests/` | `.github/workflows/windows.yml` | covered | Pure Python; the hook tests run in the Windows job. |
| `project_root.py`, `task_context.py`, `guide_sections.py` | `tests/test_hooks_from_plugin.py` | `tests/test_windows_hooks.py` | covered | Pure Python shared by the hooks. T275 added `python_launcher()` to `project_root.py`: hook messages say `py -3` on Windows. Skill text keeps `python3`; the rule in `AGENTS.md` (Permanent Rules) tells the agent to read it as `py -3`. |
| `board_sync.py`, `pull_moment.py` | `tests/test_pull_moments.py` | `.github/workflows/windows.yml` | covered | Pure Python. |
| `lane_check.py`, `verify_trace.py`, `ci_verify_done_tasks.py` | `tests/test_ci_verify_done_tasks.py` | `.github/workflows/windows.yml` | covered | Pure Python. `verify_trace.py` uses the portable lock. |
| `memory_usage_report.py`, `token_audit.py`, `token_meter.py` | `tests/test_token_meter.py` | `.github/workflows/windows.yml` | covered | Pure Python. |
| `gen_sandbox_profile.py` | `tests/test_subagent_sandbox_profile.py` | `.github/workflows/windows.yml` | partial | The profile it writes is for `claude --settings`. Nothing shows the sandbox works on Windows. To close: decide in an ADR whether sandboxed spawns are in scope on Windows. |
| `measure_agent_guide_tokens.py` | none | none | gap | No test references this script. To close: add a test that runs on both systems. |
| `plugin_init.py` | `tests/test_plugin_init.py` | `tests/test_plugin_init.py` | partial | One test is `posix_only` (it checks permission bits). Windows has no such bits, so this one stays skipped. |
| `check_companions.py` | `tests/test_companion_setup.py` | `tests/test_companion_setup.py` | covered | Pure Python. |
| `memory_slice.py`, `memory_sections.py`, `dirty_worktrees.py` | `tests/test_wake_memory_sections.py`, `tests/test_dirty_worktrees.py` | `tests/test_dirty_worktrees.py` | covered | Pure Python; run by `wake` and `craft-spawn-prompt`. |
| `self_review.py` | `tests/test_self_review_skill.py` | `tests/test_self_review_skill.py` | covered | Pure Python. |
| `dotfiles.py` | `tests/test_dotfiles.py` | `tests/test_dotfiles.py` | partial | Three tests are `posix_only` (permission bits). Windows ignores those bits. |
| `apply_profile.py` | `tests/test_settings_setup.py` | `tests/test_settings_setup.py` | partial | One test is `posix_only` (permission bits). |
| `tap_probe.py` | `tests/test_t248_tap_probe.py` | `tests/test_t248_tap_probe.py` | partial | Runs a probe through a shell; one related test is `posix_only`. Nothing shows it on Windows. |
| `block-dangerous-git.sh`, `block-dangerous-git.py` | `tests/test_git_guardrails_py.py` | `tests/test_git_guardrails_py.py` | covered | T277 added the Python twin and the Windows registration (exec form, matcher for both the Bash and the PowerShell tool). The `.sh` parity half is `posix_only`. Both files share these gaps: `git  push` (two spaces), `git -C d push` and `git checkout -- .` are not blocked; quoted text is. A follow-up can tighten both. |
| `validate.sh`, `test-agent-template.sh`, `test-claude-md-refs.sh`, `token-audit.sh` | `scripts/validate.sh` | `.github/workflows/windows.yml` | partial | T277 added the job `Repo gate (Git Bash)`, which runs `validate.sh` on `windows-latest`. Its result is unseen, and it may be red if the checkout has no symlinks. The other three scripts have no Windows run. To close: read the job result, then add the three scripts to it or port them to pytest. |
| `test_setup.sh`, `test_install_backups.sh`, `test_install_update_smoke.sh`, `test_one_command_menu.sh`, `test_cli_and_project_menus.sh`, `test_t098_harness_presence.sh` | the files themselves | `tests/test_setup_ps1_pwsh.py` | partial | Install and reinstall scenarios have PowerShell tests, but not one for one. To close: list each shell scenario with its PowerShell twin, then add the missing ones. |
| `test_update.sh`, `test_update_auto_approve.sh`, `test_update_claude_md.sh`, `test_update_removals.sh`, `test_manifest_exclusions.sh`, `test_harness_fetch.sh`, `test_settings_merge.sh` | the files themselves | `tests/test_update_ps1_pwsh.py` | partial | Update scenarios have PowerShell tests, but not one for one. To close: same list as the row above. |
| `pty.sh` | `tests/test_board_init.py` | `tests/test_board_init.py` | n/a | A helper that gives a shell test a pseudo-terminal. Windows has none. The pytest that needs a terminal is `posix_only` (see Skip inventory). |
| `test_harness_projection.sh` | the file itself | `tasks/TASK_GUIDE_T268.md` | n/a | Codex and Cursor projection is cut from the Windows installer (Claude Code only; T268 cut list). |
| `test_shellcheck_clean.sh` | the file itself | `.github/workflows/windows.yml` | n/a | Lints shell scripts, which Windows does not run. Stays on Linux CI. |
| `test_pack_catalog.sh`, `test_tech_lead_pack.sh`, `test_tech_lead_pipeline_pointer.sh`, `test_readme_current.sh` | the files themselves | none | gap | Checks of repo content, run by bash. To close: port them to pytest so one version runs on both systems. |

## Skip inventory

Lines that contain `posix_only` in each test file. Each mark carries its reason in the test file.
Counted by the test, so this table cannot go stale.

| File | Lines |
|---|---|
| `tests/test_auto_verify.py` | 115 |
| `tests/test_windows_ci_workflow.py` | 13 |
| `tests/test_plugin_source.py` | 1 |
| `tests/test_board_init.py` | 7 |
| `.claude/hooks/tests/test_t250_session_ownership.py` | 6 |
| `tests/test_repo_name.py` | 5 |
| `tests/test_dotfiles.py` | 4 |
| `tests/test_plugin_names.py` | 3 |
| `tests/test_self_review.py` | 1 |
| `tests/test_git_guardrails_py.py` | 3 |
| `tests/test_t245_ux_evaluate.py` | 1 |
| `tests/test_plugin_init.py` | 1 |
| `tests/test_hooks_from_plugin.py` | 1 |
| `tests/test_agents_md_primary.py` | 1 |
| `tests/test_companion_scoring_skills.py` | 1 |
| `tests/test_update_ps1_pwsh.py` | 1 |
| `tests/test_setup_ps1_preflight_pwsh.py` | 1 |
| `tests/test_setup_ps1_pwsh.py` | 1 |
| `tests/test_settings_setup.py` | 1 |
| `.claude/hooks/tests/test_merge_gate_t095.py` | 1 |
| `.claude/hooks/tests/test_merge_gate_companion_rows.py` | 1 |
| `.claude/hooks/tests/test_vital_slice.py` | 1 |
| `.claude/hooks/tests/test_t252_marked_ownership.py` | 1 |

## Next steps, by value

1. Push, open the PR, read the job `Python tests (Windows)` and the job `Repo gate (Git Bash)`, set the `Windows CI run seen` line, fix what they show.
2. Run `docs/windows-manual-checklist.md` on a real machine (10 steps; step 9 checks the deny rule, step 10 the plugin).
3. Find the test that hangs on Windows: `py -3 -m pytest tests .claude\hooks\tests -q --timeout=60`.
4. Portable stub `claude`: unblocks the 115 skipped auto-verify tests (the largest single gap).
5. Tighten the git guardrail patterns in both twins.
