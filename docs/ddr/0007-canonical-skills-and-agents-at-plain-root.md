# 0007. Canonical `skills/` and `agents/` move to plain root; `.claude/` becomes a projection

**Status**: Accepted — **amended by ADR-0002** (2026-09-12): CLIs are chosen from an install menu, not `setup.sh --harness <name>`. The canon/projection model, presence rule and Codex cap are unchanged.
**Date**: 2026-08-27
**Deciders**: User (thunderkds), Supervisor
**Related**: extends `DDR-0006` from doctrine text to kit assets · leaves `ADR-0001` unchanged · `BRAINSTORMING_LOG_harness-kit-portability.md` · implemented by B1/B2 (Stage 2 pending)

---

## Context

The kit is marketed as provider-agnostic. `DDR-0006` (T090) made its **doctrine** reach Codex and
Cursor through hand-written adapters (`AGENTS.md`, `.cursor/rules/agent-base.mdc`). Its **assets** —
30 skills, 5 agent guides, 8 hooks — never followed. They live in `.claude/`, which only Claude Code
reads.

The user reported the predicted consequence as an observed one, verbatim: *"the skill is not
available cause diff of folder name, path does not found"*, and proposed moving the shared material
out of `.claude/` with scripts mapping it into each CLI's own directory.

Two facts established during grilling change the inputs `DDR-0006` was decided on:

1. **`DDR-0006`'s rejection of generation does not transfer to assets.** It rejected a generated
   model because *"protection stops at this repo's CI — `setup.sh` copies adapters into downstream
   projects that have no generator and no CI, which is where the kit runs."* That reasoning holds
   for prose, which is copied once and then edited locally. It does not hold for skills and agents:
   `setup.sh` is itself the mechanism that reaches downstream, and it runs there on every install.
   `DDR-0006` also ruled only on doctrine text — it never considered assets.
2. **`AGENTS.md:29-33` is factually stale.** It states *"Codex has no equivalent of Claude Code's
   hooks, skills, or `Skill`/`Agent` tooling."* Codex gained SKILL.md support in Dec 2025
   (`.codex/skills/` project scope, `~/.codex/skills/` personal, 8 KB body cap). Hooks remain
   genuinely unportable. The kit's own doctrine has been telling users and agents that Codex support
   is hopeless.

Four external repos were read (2026-08-27) and agree on three invariants: canonical skills live at a
**plain root path** (none of the four treats `.claude/skills/` as source of truth); harness selection
happens at **install time**; installed files are **real copies the user owns**. Sources:
`wshobson/agents` (canon in `plugins/`, per-harness trees generated and gitignored, plus the limits
table used below), `mattpocock/skills` (canon at root `skills/`, `npx skills add` lets the user pick
which agents to install onto — already this kit's source for `write-better-skill`),
`bestagentkits/agency-skills` (one `SKILL.md` serving Claude and Codex, vendor metadata in a
sidecar), `codejunkie99/agentic-stack` (portable `.agent/` folder carrying skills and memory).

A consequence not obvious from the original framing: **no harness auto-discovers a plain root
`skills/`.** Relocating canon therefore makes `.claude/skills/` a projection too, and this repo —
which dogfoods the kit — cannot run its own skills until something reproduces it.

**Gate criteria**: (1) hard to reverse — **partly**; the move itself is mechanical, but it rewrites
225 live references adjacent to 1,764 historical ones. (2) surprising without context — **yes**; it
moves canon out of `.claude/`, which every prior decision assumed. (3) genuine trade-off — **yes**;
Option A delivers the reported symptom's fix for ~15 ref changes instead of 225, and was seriously
on the table. **2 of 3 → DDR, not ADR.**

---

## Decision

We will move canonical `skills/` and `agents/` to **plain root**, make every harness directory a
projection of them, and select harnesses at install time.

- **Canon**: `skills/` and `agents/` at plain root — visible, not hidden, first-class project
  content. Matches `mattpocock/skills` and `bestagentkits/agency-skills`.
- **This repo's dogfooding**: `.claude/skills` and `.claude/agents` become **committed symlinks**
  back to canon. One entry each, no duplication in git, no regeneration step, and editing either
  path edits the same file — so the kit can never drift from its own canon.
- **Downstream install**: real **copies**, per project, selected with `setup.sh --harness <name>`.
  Unchanged from `ADR-0001`; a project only ever receives vendor directories for CLIs it actually
  uses, which is the answer to the user's root-clutter objection.
- **Harness set at v1**: **Claude Code + Codex only (N=2).** Cursor keeps its `DDR-0006`
  doctrine-only stub; Gemini is a later map entry.
- **Hooks stay at `.claude/hooks/`.** They are Claude-only by nature — `wshobson/agents` records
  that lifecycle hooks port only to OpenCode and Antigravity. Relocating them buys portability
  nothing and would cost 55 reference rewrites.
- **`.claude/settings.json` stays Claude-specific**, deployed as a per-project copy outside
  `MANIFEST`. Unchanged.
- **Adapters gain content but not authority.** Every adapter keeps stating which gates its harness
  cannot enforce — on Codex: hooks, `code-review`, `security-review`, `verify`, `ship`,
  `migration-safety`.
- **Codex's 8 KB skill-body cap is enforced by failing loudly**, never by truncating. A silently
  trimmed skill looks installed and behaves worse, which is strictly worse than "skill not found".

Executed as two tasks that fail differently and must not be merged: **B1** (relocation) and
**B2** (projection, `--harness` flag, `AGENTS.md` correction). Both at C2/Medium minimum per
Hard-Stop Gate 2.

**Prohibition, load-bearing.** The rewrite must be scoped to the 44-file live surface. A repo-wide
`sed`/`xargs` rewrite is forbidden: 1,764 of the 1,989 references live in `memory/`, `tasks/`,
`PROJECT_KANBAN.md`, `reports/`, and `docs/ddr|adr/`, where they record what was true at the time.
No test would catch their corruption — the suite asserts live behaviour, not whether
`memory/decisions.md` still says what happened. `memory/codebase-map.md` is the one exception inside
that class: regenerate it via `/map-codebase`, do not edit it.

---

## Alternatives Considered

| Alternative | Pros | Cons | Why not chosen |
|-------------|------|------|----------------|
| **Relocate canon to plain root; project into every harness including Claude** | Vendor-neutral canon matching 4 of 4 repos scanned; harness N+1 is a map entry, not a restructure; downstream committed footprint shrinks | 225 live refs across 44 files, adjacent to 1,764 that must not move; symlinks need Windows developer mode; two sync mechanisms (symlink here, copy downstream) must be documented | **Selected** |
| No relocation; install-time fan-out only (Option A) | ~15 live refs instead of 225; zero risk to the audit trail; ships in one task; reversible by deleting a flag | Leaves `.claude/` as canon, so Claude Code stays structurally privileged — the asymmetry `DDR-0006` said it wanted to end; diverges from all four repos scanned | Rejected — delivers the function but not the parity the user is optimising for. **Retained as the documented fallback if B1 turns hostile mid-flight**, which B degrades cleanly into |
| Option B plus generated per-harness adapters (`tools/adapters/`, Option C) | Only option handling real format divergence (8 KB cap, tool allowlists, model aliases); mirrors `wshobson/agents` | Adds a build step and a second entry point; T036 found `smoke-install.sh` silently red for 3 days across 5+ merged PRs; `agency-skills` shows one `SKILL.md` already serves Claude and Codex with only sidecar metadata differing | Deferred — the transformation may not be needed yet. Its one load-bearing rule (fail loudly over 8 KB) is carried into B2 now |
| Generated + gitignored `.claude/skills/` for this repo's dogfooding | Vendor-neutral; consistent with downstream | This repo's Claude Code is broken until projection runs, and editing the generated copy silently loses work — the drift class this project has hit three times (T041 → T066 → T069) | Rejected at grill |
| Commit both copies, enforce with a conformance test | No symlinks, no build step, works on Windows | Every skill edit becomes a two-place edit; doubles skill bytes in git | Rejected at grill |
| `.agents/` as the canonical hidden root | One hidden dir; matches `agentic-stack` and the emerging shared convention | User chose visible plain root | Rejected by the user |
| Central shared install (`~/.agents/`) for all projects | Edit once, every project sees it | Reopens `ADR-0001`, which the user re-confirmed: *"each project will have some custom... I don't want to apply for all project"* | Rejected — `ADR-0001` stands |
| Absolute symlink targets | — | Breaks Stage 3: every sub-agent works in a worktree (`CLAUDE.md:85`), so a baked absolute link either is absent there (reproducing the user's original "skill not available" bug) or points back at the main checkout, letting agents read skills from outside their isolation boundary | Rejected — and made moot by choosing copy downstream |

---

## Consequences

### Positive
- A Codex user gets the kit's skills and agent guides through a directory Codex actually reads.
- Canon stops being Claude-branded; adding a harness becomes a destination-map entry.
- Downstream committed footprint **shrinks** — `skills/` + `agents/` + `AGENTS.md` in place of
  `.claude/` + `AGENTS.md` + `.cursor/` — which is what the user's clutter objection asked for.
- The committed symlink makes drift between this repo and its own canon structurally impossible.
- `ADR-0001` and `DDR-0006` both stand unamended; N=2 stays under `DDR-0006`'s N=4 trigger.

### Negative (accepted trade-offs)
- 225 references across 44 files change at once, in a repo where 1,764 nearby references must not.
- Symlinks require developer mode on Windows; a copy fallback must be documented.
- Two different sync mechanisms now coexist by design (symlink for this repo, copy for downstream).
  Written down here because otherwise it reads as an inconsistency and will be "fixed" by someone.
- A committed symlink is easy to mistake for a duplicate directory and delete, silently unhooking
  the kit from itself.

### Follow-up
- [ ] Stage 2 `/plan` → B1 (relocation) and B2 (projection + `--harness` + `AGENTS.md` correction)
- [ ] B2 must verify a real Codex session finds a skill by name — not merely that files landed
- [ ] `update.sh` migration for existing installs across the relocation: does it orphan the old
      `.claude/skills/` copies, or leave two live sets of skills? Must be answered inside B2
- [ ] Revisit Option C when a real format divergence is measured, or at N=4 alongside `DDR-0006`
- [ ] `T095` (the merge gate cannot see evidence created in a worktree) is **deferred by the user**;
      until it lands, B1 and B2 will hit the same unpushable state T094 is in
