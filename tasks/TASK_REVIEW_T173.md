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
| Negative cases hold | ☑ pass | T173b customized `CLAUDE.md` → exit 2, edit kept; T173e project's own `AGENTS.md` (no lock entry) → exit 2, kept; T173d legacy old lock → `CLAUDE_LEGACY.md`, never the import; M4 mutant (heading recognition removed) → T173c fails; `test_ac10_*` (`CLAUDE_LEGACY.md` byte-identical to `c573bbf`; T173 commits touch no historical record); `test_ac2_agents_md_holds_no_bare_import`. |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

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

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]

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
