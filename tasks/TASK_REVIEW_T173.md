# TASK_REVIEW — T173: AGENTS.md is the primary doctrine file; CLAUDE.md imports it

> Sibling of `tasks/TASK_GUIDE_T173.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_agents_md_primary.py` (AC 1, 2, 6, 7, 9, 10 — committed RED at `e0b79f4`: `5 failed, 5 passed`; now `10 passed`). `tests/test_update_claude_md.sh` T173a–e + M4 (AC 5a/b/c, own `AGENTS.md`, mutation control — committed RED at `bd25479`: `FAIL: T173c` ×4, `summary: 47 passed, 5 failed`; now `52 passed, 0 failed`). `tests/test_setup.sh` test5 (AC 4, real kit, new-project + legacy; `21 passed, 0 failed`). `scripts/smoke-install.sh` asserts the import pair (`smoke-install.sh: PASS`). AC 8 negative (`validate.sh` with one referenced path removed) is NOT automated yet — see agent report. AC 3 is the Stage 5 live check. |
| Verification command run | ☑ pass | Full guide command, run by common-infrastructure 2026-10-26 at `4a4484c`: `1445 passed, 25 subtests passed in 29.25s` · `validate.sh: PASS` · `smoke-install.sh: PASS` · test_setup `----- summary: 21 passed, 0 failed -----` · test_update `----- summary: 38 passed, 0 failed -----` · test_update_claude_md `----- summary: 52 passed, 0 failed -----` · `test_harness_projection.sh: 41 passed, 0 failed` · shellcheck clean · `VERIFY_EXIT=0` |
| Negative cases hold | ☑ pass | T173b customized `CLAUDE.md` → exit 2, edit kept; T173e project's own `AGENTS.md` (no lock entry) → exit 2, kept; T173d legacy old lock → `CLAUDE_LEGACY.md`, never the import; M4 mutant (heading recognition removed) → T173c fails; `test_ac10_*` (`CLAUDE_LEGACY.md` byte-identical to `c573bbf`; T173 commits touch no historical record); `test_ac2_agents_md_holds_no_bare_import`. · Supervisor mutants 2026-10-26 on `5fd1472`, each reverted (`git status` clean after): M5 `validate.sh` `[ ! -s "$MISSFILE" ] || FAIL=1` → `true` → `1 failed, 10 passed`; M6 `CLAUDE.md` line 1 → `# CLAUDE.md doctrine` → `1 failed, 10 passed`; restored `11 passed`. AC 8 negative automated at `5fd1472` (`test_ac8_validate_fails_when_agents_md_references_a_missing_path`, with an unmodified-copy control that exits 0). |
| verify | ☑ pass | User ran `/verify` 2026-10-26; Supervisor drove the real installer and headless `claude -p --model sonnet` (all tools disallowed) in scratch installs — pass. New install from T173 kit: `CLAUDE.md` = `@AGENTS.md\n` (`od -c`), `AGENTS.md` 196 lines / 18226 bytes. Legacy install (mode 2): `CLAUDE.md` byte-identical to `CLAUDE_LEGACY.md`. Old install from `main` (`claude_md_source: "CLAUDE.md"`) + T173 `update.sh`, no terminal: rc=0, `CLAUDE.md` → `@AGENTS.md\n`, `AGENTS.md` 55 → 196 lines. Customized old `CLAUDE.md` + update: rc=2, "You edited these; with no terminal they are kept as they are: CLAUDE.md", file byte-identical. AC 3 agent runs, 0 tool calls each: new → "1. No tests = not done and not shippable. 2. Non-Claude CLIs (Codex, Cursor): what they cannot enforce 3. CLAUDE.md, AGENTS.md"; updated-old → same; control (`CLAUDE.md` = backticked `` `@AGENTS.md` ``) → "UNKNOWN … the contents of AGENTS.md weren't loaded" / "NONE"; no `CLAUDE.md` → same answers, "3. AGENTS.md" (native read). |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Supervisor Stage 4 2026-10-26 over `c573bbf..5fd1472` (43 files). Read in full: `lib/harness-update.sh`, `scripts/validate.sh`, `scripts/smoke-install.sh` diffs; `diff c573bbf:CLAUDE.md AGENTS.md` = 4 allowed edits only (H1, line 5, `AGENTS.md's Writing Principles`, 8-line non-Claude CLI section); `CLAUDE.md` = `@AGENTS.md\n` (`od -c`, 11 bytes); `CLAUDE_LEGACY.md` unchanged; no Files-Must-NOT-Touch path in the diff; remaining `CLAUDE.md` mentions in shipped files are all about the file itself. Pointer-only edits in `skills/`, `docs/claude-md/` sampled, not read line by line. `lane_check.py`: `EXCEEDS (files 42 > 14; lines 1020 > 500)` — mechanical pointer and pin repoints; kept C2. code-review: 0 P0, 0 P1, 1 P2 (`skills/compound/SKILL.md:128`), 1 P3. security-review (High): no findings — one quoted string compare in `resolve_claude_md_source`, one grep target swap in `validate.sh`; no new input path. |
| Full smoke suite still green (no regression) | ☑ pass | Supervisor 2026-10-26: `python3 -m pytest -q tests .claude/hooks/tests` → `1446 passed, 25 subtests passed` (agent 2, `5fd1472`); suites the first agent skipped, all rc=0: test_settings_merge, test_install_backups `17 passed, 0 failed`, test_install_update_smoke `9 passed, 0 failed`, test_t098_harness_presence `20 passed, 0 failed`, test_pack_catalog `16 passed, 0 failed`, test_harness_fetch `9 passed, 0 failed`, test_readme_current `ALL PASS`, test_update_removals `30 passed, 0 failed`, test_one_command_menu `22 passed, 0 failed`, test_cli_and_project_menus `24 passed, 0 failed`, test_manifest_exclusions `8 passed, 0 failed`; `tests/test_ci_wires_shell_suites.py` `5 passed`. Pre-existing, unchanged: `scripts/test-claude-md-refs.sh` AC5/AC6 fail identically on `main` (T039 one-shot guard, not in CI). |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | /verify 2026-10-26: headless Chrome 1280px crop of Providers (`site-providers.png` in the Supervisor scratchpad): lead text "`AGENTS.md` plus `docs/claude-md/` stay the one primary source of truth. Codex reads it directly; Claude Code reads it through the one-line `CLAUDE.md` import." and the File/Auto-read-by/What-it-carries table render in the existing styles; no overlap or overflow. Copy-only change, no markup structure change. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | Diff adds no CSS, class or token; changed cells reuse the existing `<code>` and table cell styles (seen in the 1280px crop). |
| **UI: Responsiveness at target viewports** | ☐ N/A | Copy-only edit inside the existing Providers table, which T167 already stacks as cards on phones (`data-label` cells unchanged). No layout change to test; site word-cap tests pass. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured by common-infrastructure at the branch base, before any T173 commit; HEAD `4d32f76` = `c573bbf` + the plan commit, which touches only `tasks/TASK_GUIDE_T173.md`):

```
$ date -u; git rev-parse --short HEAD
2026-10-26T03:02:08Z
4d32f76
$ head -3 CLAUDE.md AGENTS.md
==> CLAUDE.md <==
# Claude Project Supervisor Guidelines
**Version:** 1.17 (Unified Agentic Operating System) <br>
**Role:** Project Supervisor AI

==> AGENTS.md <==
# AGENTS.md

This is a thin adapter for non-Claude agentic CLIs (Codex, etc.) — auto-read at the repo root.
$ wc -l CLAUDE.md AGENTS.md
  186 CLAUDE.md
   55 AGENTS.md
  241 total
$ cd $(mktemp -d) && git init -q && SUPERVISOR_REPO=file:///home/hungnguyenhuu/workspace/pets/wt-t173 sh /home/hungnguyenhuu/workspace/pets/wt-t173/setup.sh </dev/null   # no terminal -> new-project default
exit=0
[info]  Installed .claude/settings.json (copy). Restart Claude Code to activate hooks.
[info]  Wrote ./.claude/harness-lock.json (117 file hashes).
[info]  CLAUDE source: CLAUDE.md | lock: .claude/harness-lock.json
[info]  CLIs: Claude Code, Codex
$ head -1 CLAUDE.md; wc -lc CLAUDE.md AGENTS.md; grep claude_md_source .claude/harness-lock.json
# Claude Project Supervisor Guidelines
  186 16898 CLAUDE.md
   55  2994 AGENTS.md
  241 19892 total
  "claude_md_source": "CLAUDE.md",
```

The installed project gets the full doctrine in `CLAUDE.md` (186 lines) and the 55-line thin adapter in `AGENTS.md`.

**AC 11/12 amendment BEFORE** (verbatim `site/index.html` lines at HEAD before the amendment commits):

```
497:  <li><code>1) New project</code> (<code>CLAUDE.md</code>) — the default with no terminal.</li>
541:<h2>Skills (30)</h2>
733:<tr><td data-label="Path"><code>AGENTS.md</code></td><td data-label="What it contains">Provider adapter for Codex — see Providers below</td></tr>
```

**AFTER**: Supervisor, 2026-10-26, T173 kit `5e67e0c`, scratch new-project install:

```
$ od -c CLAUDE.md
0000000   @   A   G   E   N   T   S   .   m   d  \n
0000013
$ wc -l -c AGENTS.md; head -1 AGENTS.md
  196 18226 AGENTS.md
# AGENTS.md — Project Supervisor Guidelines
```

**DELTA**: Claude Code and Codex now read one doctrine file, `AGENTS.md`; Claude gets it through the one-line `CLAUDE.md` import, and a pre-T173 install updates to that pair without losing a customized `CLAUDE.md`.

**WITNESS**: Supervisor, 2026-10-26, during the user's `/verify` — real `setup.sh` / `update.sh` runs and 4 headless `claude -p` sessions in scratch installs, `active_task` = T173 (`memory/event-trace/T173.jsonl`).

---

## T173 record (filled by common-infrastructure)

**AC 1 allowed edits** (base `c573bbf:CLAUDE.md` → `AGENTS.md`; enforced by `REPLACED_SPANS` in `tests/test_agents_md_primary.py`):
- (a) H1 `# Claude Project Supervisor Guidelines` → `# AGENTS.md — Project Supervisor Guidelines`; one opening line added after `**Role:**`: "This file is the kit's doctrine. Codex reads `AGENTS.md` directly; Claude Code loads it through the `@AGENTS.md` import that `CLAUDE.md` holds."
- (b) Response Standard bullet: `CLAUDE.md's Writing Principles` → `AGENTS.md's Writing Principles` (mirrored byte-identical in `agents/general-agent-template.md`, per `tests/test_response_standard.py`).
- (c) AC 6 section appended: `## Non-Claude CLIs (Codex, Cursor): what they cannot enforce` (5 lines; carries `.codex/skills/`, 8 KB cap, Codex-only Update/Reinstall, the cannot-enforce list).
- Result: `AGENTS.md` 196 lines / 18,226 bytes; `CLAUDE.md` = `@AGENTS.md\n` (11 bytes).

**AC 7 Codex cap citation**: `codex-cli 0.163.0` (installed) embeds its default config: `strings ~/.codex/packages/standalone/releases/0.163.0-x86_64-unknown-linux-musl/bin/codex | grep project_doc_max_bytes` → `project_doc_max_bytes = 32768`. The online Codex docs were not fetched (no web tool in this run).

**D2 repoints** (before → after; no assertion deleted):
- `tests/test_claude_md_slim.py`: `TEXT` reads `CLAUDE.md` → `AGENTS.md` (≤200 cap + kept rules).
- `tests/test_provider_adapters.py`: source `CLAUDE_MD` `CLAUDE.md` → `AGENTS.md`; `ADAPTERS` {AGENTS.md, cursor} → {cursor}; new `CLI_FILES` {AGENTS.md, cursor} keeps the principle/gate/untrusted/no-TASK_GUIDE/docs-pointer/cannot-enforce checks on both; canonical-pointer check `"CLAUDE.md" in text` → `"AGENTS.md" in text` (cursor); 60-line cap → cursor only, plus `AGENTS.md` ≤200 (AC 7); cannot-enforce terms now checked inside the section (tightened, so the full doctrine cannot pass by accident); Staleness Guard `"CLAUDE.md" in section` → `"AGENTS.md" in section`.
- `tests/test_writing_principles.py`, `tests/test_response_standard.py`, `tests/test_token_economy_docs.py`: `CLAUDE_MD` → `AGENTS.md` (variable name kept).
- `tests/test_resolve_question.py::test_ac9_*`: reads `CLAUDE.md` → `AGENTS.md`.
- `tests/test_memory_slice.py` `AC6_DOCS`: `"CLAUDE.md"` → `"AGENTS.md"`.
- `.claude/hooks/tests/test_agent_guide_dedup.py`: pin `("CLAUDE.md", "a830bb8")` → `("AGENTS.md", "8080fdb")` (T173's edit commit; comment-history style kept).
- `.claude/hooks/tests/test_complexity_matrix_pointers.py` `POINTER_FILES`, `.claude/hooks/tests/test_untrusted_content_boundary.py` `WIRING_FILES`, `.claude/hooks/tests/test_memory_channel_and_budget.py` `SHIPPING_FILES`: `CLAUDE.md` → `AGENTS.md`.
- `.claude/hooks/tests/test_vital_slice.py`: `LINE_CAPS["CLAUDE.md"]=186` → `LINE_CAPS["AGENTS.md"]=196`; AC5 / AC8 / anti-vacuity targets read `AGENTS.md`.
- `scripts/test-claude-md-refs.sh`: `CLAUDE_MD="$ROOT/AGENTS.md"`; baseline still read as `99940b8:CLAUDE.md`. Its AC5 Permanent Rules + AC6 line-count checks FAIL identically before and after T173 (pre-existing one-shot T039 guard; not in the Verification Command).
- `scripts/smoke-install.sh`: `grep "Project Supervisor" CLAUDE.md` → `CLAUDE.md` == `@AGENTS.md` (1 line) and `grep "Project Supervisor" AGENTS.md`; `assert_exists AGENTS.md` added.
