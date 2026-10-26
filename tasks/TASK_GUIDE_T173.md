# TASK_GUIDE — T173: AGENTS.md is the primary doctrine file; CLAUDE.md imports it
**Date**: 2026-10-26
**Complexity Level**: C2
**Risk Level**: High
**Priority**: P1
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

> C2 floor: Hard-Stop Gate 2 ("restructure"). Risk High: `setup.sh` / `update.sh` rewrite the
> `CLAUDE.md` and `AGENTS.md` of every installed project.

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth) from the Complexity matrix in your role guide (`agents/common-infrastructure.md`)
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` for directory layout, entry points, and blast-radius hotspots — skip if the task is C0/C1 and touches a single known file

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-26: "seem like CLAUDE ready to support the AGENT.md, so update the content from
CLAUDE.md to AGENT.md and the CLAUDE.md will refer to AGENT.md only".

Supervisor-confirmed facts (2026-10-26, `https://code.claude.com/docs/en/memory`, section "AGENTS.md"):
- "Claude Code can read `AGENTS.md` as your project instructions" — "Reading `AGENTS.md` directly requires Claude Code v2.1.277 or later". Installed: `claude --version` → `2.1.310 (Claude Code)`.
- "By default, Claude reads `AGENTS.md` only when you have no `CLAUDE.md` in your working directory or above it."
- "Share one file with other coding tools": "putting an `@AGENTS.md` import in a `CLAUDE.md` next to it" — the doc's recommended form; a symlink is the alternative but "the Edit and Write tools refuse to write through a symlink" and breaks on Windows clones.
- The file name is `AGENTS.md` (plural, the existing file and the one Claude Code auto-reads). The user wrote "AGENT.md"; read it as `AGENTS.md`.

User decisions (AskUserQuestion, 2026-10-26):
- D1 — `CLAUDE_LEGACY.md` stays a full file, unchanged. Only `CLAUDE.md` moves. ("Leave legacy as is (Recommended)")
- D2 — Tests that pin `CLAUDE.md` content, line count or baseline commit are repointed to `AGENTS.md` / the new commit, keeping each assertion's meaning; every repoint is listed in `tasks/TASK_REVIEW_T173.md`. No assertion is deleted. ("Yes, repoint them (Recommended)")
- D3 (Supervisor, from the doc) — `CLAUDE.md` is the `@AGENTS.md` import, not a symlink.

**Restated intent** (Supervisor's interpretation, in the project's domain language):
> The kit's Supervisor doctrine lives in one file, `AGENTS.md`, which every CLI reads. `CLAUDE.md`
> holds only the line `@AGENTS.md`, so Claude Code loads the same doctrine through the import, and
> new installs and updates deliver that pair without losing a customized `CLAUDE.md`.

**Out of scope** (what this task explicitly does NOT do):
- `CLAUDE_LEGACY.md` (D1) — byte-identical after this task.
- Renaming `docs/claude-md/` or any other path.
- Rewriting Claude-specific calls (`Skill({...})`, `Agent({...})`, hook names) into tool-neutral prose. They move verbatim.
- Historical records: `docs/ddr/`, `docs/adr/`, `tasks/` (other than T173's own files), `memory/event-trace/`, `BRAINSTORMING_LOG*.md`, `RUNBOOK.md`. They describe past states and keep the name `CLAUDE.md`.
- A new DDR file — the user parks ADR/DDR docs until the separate MCP task lands (memory: "ADR/DDR docs via future MCP"). Record the decision in `memory/decisions.md` and note "DDR owed (supersedes DDR-0006's 'CLAUDE.md stays primary')".

**Requirement Refs**:
- User request 2026-10-26 (above); DDR-0006 premise "`AGENTS.md` is auto-read by Codex and not by Claude Code" is no longer true.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (Supervisor, 2026-10-26; D1/D2 answered by the user)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary (no new term; "doctrine file" = the file Claude Code loads as project instructions)
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist and are covered by the Acceptance Criteria

---

## Dependencies & Reachability

**Depends on**: T170 — its branch `docs/t170-resolve-question` edits `CLAUDE.md:65` (cross-cutting skills line). The Supervisor merged that branch into this one at `c573bbf` (2026-10-26; T170's PR is not in `main` yet because `gh` is not logged in). The branch base for AC 1 is `c573bbf`. T170's PR must reach `main` before T173's does.

**Entry point**: `@AGENTS.md` (the whole content of `CLAUDE.md`)

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `AGENTS.md` holds the full doctrine: every heading and every non-blank line of `CLAUDE.md` at the branch base (after merging `main` per Depends on) is present in `AGENTS.md`, in the same order. Allowed edits only: (a) the H1 and the opening lines name `AGENTS.md` as this file; (b) a sentence that means "this doctrine file" says `AGENTS.md`, not `CLAUDE.md`; (c) AC 6's section. Each allowed edit is listed in the review file. | "update the content from CLAUDE.md to AGENT.md" |
| 2 | `CLAUDE.md` is exactly `@AGENTS.md\n` — one line, nothing else. | "the CLAUDE.md will refer to AGENT.md only" |
| 3 | A Claude Code session in the repo loads the doctrine through the import: a headless `claude -p` run in a scratch install answers a question only `AGENTS.md` answers (e.g. the title of Hard-Stop Gate 5) with the right text, and makes no Read of `AGENTS.md` to do it. | Claude reads the content through `CLAUDE.md` |
| 4 | `setup.sh`, new-project mode: the project gets `CLAUDE.md` = `@AGENTS.md\n` and `AGENTS.md` = the full doctrine. Legacy mode: `CLAUDE.md` = `CLAUDE_LEGACY.md` byte-for-byte, as today. | install delivers the pair; D1 |
| 5 | `update.sh` on a project installed before T173: (a) unmodified `CLAUDE.md` + lock with `claude_md_source: CLAUDE.md` → `CLAUDE.md` becomes the one-liner and `AGENTS.md` the full doctrine, no prompt; (b) a customized `CLAUDE.md` → the existing edit-safe ask, never a silent overwrite; (c) an old lock without `claude_md_source` whose `CLAUDE.md` first line is the pre-T173 heading `# Claude Project Supervisor Guidelines` → resolves to source `CLAUDE.md`, not `conflict` (`lib/harness-update.sh` `resolve_claude_md_source` compares first lines today, and the new upstream first line is `@AGENTS.md`). | updates must not lose user edits |
| 6 | `AGENTS.md` keeps one short section for non-Claude CLIs that names what they cannot enforce (the hooks do not run there) — the content today's adapter carries and `tests/test_provider_adapters.py::test_every_adapter_names_what_it_cannot_enforce` checks. | Codex keeps reading `AGENTS.md`; nothing it relied on is lost |
| 7 | `.cursor/rules/agent-base.mdc` names `AGENTS.md` (not `CLAUDE.md`) as canonical and stays ≤60 lines. The ≤60-line adapter cap no longer applies to `AGENTS.md`; the ≤200-line cap from `tests/test_claude_md_slim.py` applies to `AGENTS.md` instead. `AGENTS.md` ≤ 32768 bytes (Codex `project_doc_max_bytes` default — confirm against the Codex docs and cite them in the review file). | adapters stay consistent with the new canon |
| 8 | Tooling reads the doctrine where it now lives: `scripts/validate.sh` check 3 (path references resolve) and check 4 (mandatory folders) and `scripts/test-claude-md-refs.sh` read `AGENTS.md`. A missing path referenced in `AGENTS.md` fails `validate.sh`. | the content moved |
| 9 | Shipped pointers to a doctrine section say `AGENTS.md`: in `agents/`, `skills/`, `templates/`, `docs/claude-md/`, `site/`, `README.md`, every text that sends the reader to a section of the doctrine (e.g. "CLAUDE.md's Response Standard", "see CLAUDE.md for the operational commands") names `AGENTS.md`. A text about the file `CLAUDE.md` itself (installer, the import) keeps the name. | a pointer into a one-line file looks live and is not (T085 failure class) |
| 10 | Negative: `CLAUDE_LEGACY.md` is byte-identical to the branch base; no files in the Out-of-scope list change; no test assertion is deleted (each repoint listed before → after). | D1, D2 |
| 11 | Amendment 2026-10-26 (user: "did you update the README and guide page for this update" → "go ahead"): `site/index.html` describes the new layout everywhere. (a) Repository layout: the `AGENTS.md` row says it is the full doctrine (not "Provider adapter for Codex"), and a `CLAUDE.md` row says it holds only the import `@AGENTS.md`. (b) Install variants: `1) New project` names `CLAUDE.md` = `@AGENTS.md` + the full `AGENTS.md`, not `CLAUDE.md` alone. No layout, CSS or markup-structure change. | AC 9 — the site is a shipped pointer surface |
| 12 | The `<h2>Skills (N)</h2>` heading and the quick-reference `N skills` link both equal the number of `skills/*/` folders (31 today; T170 updated only the quick reference). A new test in `tests/test_site_content.py` fails if either count disagrees with the folder count. | found at T173 review; same page |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Branch base `CLAUDE.md` vs new `AGENTS.md` | every base line present in order, except the listed allowed edits | automated test (new `tests/test_agents_md_primary.py`) |
| 2 | New `CLAUDE.md` | bytes == `b"@AGENTS.md\n"` | automated test |
| 3 | Fresh `setup.sh` install into a temp dir, new-project and legacy mode | AC 4 file contents | automated (`tests/test_setup.sh` / `scripts/smoke-install.sh` extended) |
| 4 | Pre-T173 install fixture, then `update.sh` — unmodified / customized / old-lock cases | AC 5 (a)/(b)/(c) | automated (`tests/test_update_claude_md.sh` extended) |
| 5 | `AGENTS.md` with one referenced path removed | `validate.sh` exits non-zero naming the path | automated |
| 6 | Grep of shipped dirs for a doctrine-section pointer to `CLAUDE.md` | zero hits | automated test |
| 7 | Headless `claude -p` in a scratch install | correct Gate 5 title, no Read of `AGENTS.md` in the tool log | Stage 5 `/verify` (live agent run) |
| 8 | Built site, headless Chrome 1280px and 390px | AC 11/12 text visible, no overflow; heading reads `Skills (31)` | Supervisor screenshot + `tests/test_site_content.py` |

### Verification Command (exact, runnable)

```bash
python3 -m pytest -q tests .claude/hooks/tests && sh scripts/validate.sh && sh scripts/smoke-install.sh && bash tests/test_setup.sh && bash tests/test_update.sh && bash tests/test_update_claude_md.sh && bash tests/test_harness_projection.sh && shellcheck -x setup.sh update.sh lib/harness-update.sh scripts/validate.sh scripts/smoke-install.sh tests/test_harness_projection.sh
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T173.md`.

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_T173.md`.

---

## Approach

**Pattern reference**: `lib/harness-update.sh` `resolve_claude_md_source` / `process_claude_md` (T110) — the edit-safe delivery and first-line inference to extend for AC 5(c); `tests/test_claude_md_slim.py` — the shape of a doctrine-content test.

**Vital slice**: the move itself (AC 1, 2), the installer/update pair (AC 4, 5) and the tooling that reads the doctrine (AC 8). These carry the value: without them an install ships a one-line `CLAUDE.md` that points at a thin adapter.
**Cut list**:
- `CLAUDE_LEGACY.md` → `AGENTS.md` (D1). Consequence, accepted: a legacy install also receives the new-project `AGENTS.md` through `MANIFEST`, so Codex in a legacy project reads new-project doctrine. Claude Code there still reads the legacy `CLAUDE.md` only (the default `claude-md-or-agents-md` mode).
- Tool-neutral rewrite of `Skill()` / `Agent()` calls.
- `docs/claude-md/` rename.
- DDR file (parked, see Out of scope).

Steps:
1. Record BEFORE (branch base `c573bbf`) (verbatim prior `CLAUDE.md` head + `AGENTS.md` head) in the review file.
2. Write the RED tests for AC 1, 2, 6, 7, 9, 10 first.
3. Move: `AGENTS.md` ← base `CLAUDE.md` content + AC 6 section; `CLAUDE.md` ← `@AGENTS.md\n`.
4. Installer/update (AC 4, 5), validate/refs scripts (AC 8), adapters (AC 7), shipped pointers (AC 9).
5. Repoint pinned tests (D2), listing each before → after in the review file.
6. Append the decision to `memory/decisions.md` (D1–D3, DDR owed).

---

## Edge Case Checklist

- [ ] `@AGENTS.md` written inside backticks or a code block is NOT an import — the doc: "Import parsing skips Markdown code spans and fenced code blocks". `CLAUDE.md` must hold it bare.
- [ ] `AGENTS.md` itself must not contain a bare `@AGENTS.md` or `@CLAUDE.md` (self/loop import). Any `@path` text inside `AGENTS.md` that is not meant as an import must be in backticks.
- [ ] Imports resolve relative to the importing file, max depth 4 — `CLAUDE.md` and `AGENTS.md` sit side by side at the root, depth 1.
- [ ] Old lock + old heading (AC 5c): the new upstream first line is `@AGENTS.md`, so today's inference returns `conflict`. Recognize the pre-T173 heading as `CLAUDE.md`'s source without matching `CLAUDE_LEGACY.md`'s heading.
- [ ] User's project already has its own `AGENTS.md` (from another tool) and no lock entry for it → the edit-safe rule asks / backs up; it is never silently replaced.
- [ ] Hooks or scripts that read `CLAUDE.md` text (`scripts/validate.sh`, `scripts/test-claude-md-refs.sh`, `.claude/hooks/pre_bash_block_unsafe_merge.py:258` comment, `scripts/token_audit.py:31` comment) — content readers move to `AGENTS.md`; comments that name the file stay correct.
- [ ] `tests/test_t098_harness_presence.sh` writes a fixture `CLAUDE.md` — confirm presence detection still works when the doctrine is in `AGENTS.md`.
- [ ] `InstructionsLoaded` hooks: none in `.claude/settings.json` today; the doc says they fire for an `AGENTS.md` imported from `CLAUDE.md`, so no change.
- [ ] Byte-identity baselines (`.claude/hooks/tests/test_agent_guide_dedup.py` `T070_BASELINE_REF`, `T133_BASELINE_REF`, and others) compare `CLAUDE.md` at a commit — repoint to `AGENTS.md` at T173's edit commit (D2), keeping the comment-history style used there.

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `AGENTS.md` | full doctrine (AC 1, 6) |
| `CLAUDE.md` | `@AGENTS.md` only (AC 2) |
| `setup.sh`, `lib/harness-update.sh` | AC 4, 5 |
| `scripts/validate.sh`, `scripts/test-claude-md-refs.sh` | AC 8 |
| `.cursor/rules/agent-base.mdc` | AC 7 |
| `agents/*.md`, `skills/*/SKILL.md`, `templates/*`, `docs/claude-md/*`, `site/index.html`, `README.md` | AC 9 pointers only |
| `tests/test_agents_md_primary.py` (new), `tests/test_provider_adapters.py`, `tests/test_claude_md_slim.py`, `tests/test_update_claude_md.sh`, `tests/test_setup.sh`, `scripts/smoke-install.sh`, `.claude/hooks/tests/*` pins | new tests + D2 repoints |
| `memory/decisions.md`, `PROJECT_KANBAN.md` | decision + board row |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `CLAUDE_LEGACY.md` | D1 |
| `docs/ddr/*`, `docs/adr/*`, `RUNBOOK.md`, `BRAINSTORMING_LOG*.md`, other tasks' guides | historical records |
| `.claude/skills`, `.claude/agents` symlinks | load-bearing relative symlinks (CLAUDE.md "Folder Structure") |

---

## Test Plan

New `tests/test_agents_md_primary.py` for AC 1, 2, 6, 7, 9, 10 (written first, RED against the base). Shell fixtures in `tests/test_setup.sh` / `tests/test_update_claude_md.sh` for AC 4, 5 (three update cases). Negative check for AC 8 (remove one referenced path in a temp copy → `validate.sh` fails). Live agent check for AC 3 at Stage 5.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (High risk)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T173.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run (user-only)
- [ ] `memory/decisions.md` updated (D1–D3, DDR owed)
- [ ] Supervisor notified: task ready for Stage 4 review

---

## Questions Log
- 2026-10-26 Is the guide page (`site/index.html`) fully updated for T173? → No: Repository layout `AGENTS.md` row, Install variants line 497, and `Skills (30)` heading (T170 leftover) were stale; added AC 11/12, user: "go ahead".
