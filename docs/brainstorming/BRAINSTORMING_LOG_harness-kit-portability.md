# BRAINSTORMING_LOG — Multi-harness kit portability

**Date**: 2026-08-27
**Tier**: Deep (architectural; reverses part of DDR-0006's scope; touches the install path every downstream project runs)
**Supersedes in scope**: nothing. Extends `BRAINSTORMING_LOG_multi-provider.md` (T090) from doctrine text to kit assets.
**Grilling input**: `memory/decisions.md`, entry dated 2026-08-27.

---

## The Problem Space

The kit is marketed as provider-agnostic. T090/DDR-0006 made its *doctrine* reach Codex and Cursor
via hand-written adapters (`AGENTS.md`, `.cursor/rules/agent-base.mdc`). Its **assets** — 30 skills,
5 agent guides, 8 hooks — never followed. They live in `.claude/`, which only Claude Code reads.

The user's reported symptom, verbatim: *"the skill is not available cause diff of folder name, path
does not found"*. That is the predicted consequence, observed.

Two aggravating facts found during grilling:

1. `AGENTS.md:29-33` states *"Codex has no equivalent of Claude Code's hooks, skills, or
   `Skill`/`Agent` tooling."* Half of that is now false — Codex gained SKILL.md support in Dec 2025
   (`.codex/skills/` project scope, `~/.codex/skills/` personal, 8 KB body cap). The kit's own
   doctrine therefore tells both the user and any agent that Codex support is hopeless. Hooks
   remain genuinely unportable.
2. No harness auto-discovers a plain root `skills/`. Claude Code reads `.claude/skills/`, Codex
   reads `.codex/skills/` (or the emerging shared `.agents/skills/`). So relocating canon to plain
   root makes `.claude/skills/` a *projection too* — this repo cannot run its own skills until
   something reproduces it. That consequence is the hinge of this whole design and was not obvious
   from the user's original framing.

### What is already locked (grilling, 2026-08-27 — not reopened here)

| Decision | Value | Why it is not an option below |
|---|---|---|
| Canonical location | `skills/` + `agents/` at plain root | User selected; matches 4 of 4 repos scanned |
| Scope of install | Per-project, never a shared central clone | ADR-0001; user re-confirmed ("each project will have some custom") |
| Downstream install mechanism | **Copy** real user-owned files | ADR-0001 + external consensus |
| This repo's own dogfooding | **Committed symlink** `.claude/skills -> ../skills` | User selected; deliberately differs from the line above |
| Hooks | Stay Claude-only; every adapter must say so | wshobson's limits table; verified unportable |

The open question this log addresses is therefore **not** "where does canon live" but **how the
relocation is executed without destroying the audit trail, and how far the projection reaches**.

### The measurement that dominates every option

Refs to `.claude/skills` or `.claude/agents`, counted 2026-08-27:

| Class | Refs | Files | Treatment |
|---|---|---|---|
| **Live surface** | **225** | **44** | must be rewritten |
| — `tests/` | 58 | 6 | |
| — `.claude/hooks` | 55 | 12 | |
| — `scripts/` | 33 | 5 | |
| — `.claude/skills` | 25 | 10 | |
| — `docs/claude-md` | 18 | 3 | |
| — `CLAUDE.md` | 15 | 1 | |
| — `MANIFEST`, `setup.sh`, `templates/`, `CLAUDE_LEGACY.md`, `AGENTS.md`, `.cursor` | 21 | 7 | |
| **Historical audit trail** | **1,764** | — | **must NOT be rewritten** |
| — `memory/` | 1013 | | describes what was true then |
| — `tasks/` | 707 | | ditto |
| — `PROJECT_KANBAN.md`, `reports/`, DDR/ADR | 44 | | ditto |

**The 8:1 ratio is the central risk of this task.** The danger is not the 225 refs that must change;
it is the 1,764 that a repo-wide `sed -i` would silently corrupt. `memory/codebase-map.md` (39 refs)
is the one exception inside the historical class — it is regenerable via `/map-codebase` and *should*
be refreshed rather than edited.

---

## Questions for the User

1. **Which harnesses ship in v1 of this change?** Codex is the stated pain point; Cursor already has
   a stub from T090; Gemini was named in passing. Each additional target is a destination-map entry
   plus a limits paragraph, not a redesign — but DDR-0006's own follow-up says *"Revisit if a 4th
   provider is added: at N=4 the generator's cost/benefit inverts."* Shipping Claude + Codex +
   Cursor + Gemini simultaneously crosses that line and re-opens DDR-0006 properly.
2. **Do `hooks/` and `templates/` relocate too, or only `skills/` + `agents/`?** Hooks are
   Claude-only by nature, so relocating them buys portability nothing and costs 55 ref rewrites.
   A defensible split is: relocate what is portable, leave `.claude/hooks/` exactly where it is.
3. **Does `.claude/settings.json` stay Claude-specific?** It is already deployed as a per-project
   copy outside `MANIFEST`. Nothing here needs to change it — confirming so it is written down.

---

## Alternative Paths

### Option A — The Minimalist Path: no relocation, install-time fan-out only

Leave every file where it is. Teach `setup.sh`/`update.sh` a per-harness destination map so
`MANIFEST` paths are copied into `.codex/skills/`, `.cursor/rules/`, etc. at install, gated by a
`--harness` flag. Correct `AGENTS.md`'s stale Codex claim.

- **Pros**: ~15 live refs touched instead of 225. Zero risk to the audit trail. No dogfooding
  problem — this repo is unchanged. Ships in one C1/C2 task. Reversible by deleting a flag.
- **Cons**: `.claude/` stays canon, so Claude Code remains structurally privileged — the asymmetry
  DDR-0006 said it wanted to end. Diverges from all four repos scanned. Every future harness reads
  from a Claude-branded directory, which is the thing that reads as lock-in.

### Option B — The Recommended Path: relocate canon, project everywhere including Claude

Move `skills/` + `agents/` to plain root. `.claude/skills`, `.claude/agents` become committed
symlinks back (this repo's dogfooding). `MANIFEST` gains a destination map; `setup.sh --harness`
copies canon into each selected vendor dir downstream. Hooks stay at `.claude/hooks/`.
`AGENTS.md` corrected and given a real Codex limits section.

- **Pros**: canon is vendor-neutral, matching all four repos scanned. Adding harness N+1 is a map
  entry, not a restructure. Committed footprint downstream *shrinks* (`skills/` + `AGENTS.md`
  instead of `.claude/` + `AGENTS.md` + `.cursor/`), which answers the user's clutter objection.
  The symlink means this repo can never drift from its own canon.
- **Cons**: 225 live refs across 44 files, adjacent to 1,764 that must not move. Symlinks need
  Windows developer mode. Two different sync mechanisms (symlink here, copy downstream) must be
  documented or they read as an inconsistency.

### Option C — The Scalable Path: Option B plus generated adapters per harness

Option B, plus a `tools/adapters/` step that transforms canon per harness — trimming Codex bodies to
its 8 KB cap, stripping per-agent tool allowlists Cursor ignores, rewriting model aliases.

- **Pros**: the only option that handles genuine format divergence rather than assuming
  SKILL.md is universal. Directly mirrors wshobson, the most mature repo scanned.
- **Cons**: adds a build step and a second entry point. DDR-0006 rejected generation on the ground
  that *"protection stops at this repo's CI"* — and T036 found `smoke-install.sh` silently red for
  three days across five merged PRs, which is that objection made concrete. `agency-skills`
  demonstrates one SKILL.md serving Claude and Codex with only sidecar metadata differing, so the
  transformation this option builds may not be needed at all yet.

---

## Adversarial Review — why each might fail

**Option A fails if** the user's real goal is parity rather than function. It makes Codex work while
permanently encoding that Claude is the real target — and the user's own framing ("we will have a
lot of folder in project? it is not good, right?") shows they are optimising for the *shape* of the
repo, not only for Codex finding a file. A works and still feels wrong.

**Option B fails in exactly one way, and it is severe**: an implementer reaches for
`grep -rl '\.claude/skills' | xargs sed -i` and rewrites 1,764 historical references. Nothing in
the test suite would catch it — the tests assert on live behaviour, not on whether
`memory/decisions.md` still says what happened. The corruption would be discovered months later, by
which point the audit trail is unrecoverable without archaeology. **This is the single highest-risk
action in the task and must be an explicit prohibition in the TASK_GUIDE, not a note.**
Secondary failure: the committed symlink is invisible to a reader who only sees `skills/` in a diff,
so someone "cleans up" `.claude/skills` as a duplicate and silently unhooks the kit from itself.

**Option C fails if** the 8 KB Codex cap turns out to bite immediately. Several skills in this repo
are well over 8 KB, so the adapter would have to *truncate a skill body* — silently producing a
degraded skill on Codex that looks installed and behaves worse. That is a strictly worse failure
than "skill not found", because it is invisible. Any adapter must **fail loudly** on an oversize
skill rather than trim it.

**All three fail if** the limits are not stated in the adapters. T085's defect was a link that
"looks live and is not"; shipping `.codex/skills/` without saying that hooks, `code-review`,
`security-review`, `verify`, `ship`, and `migration-safety` do not run there recreates exactly that
class — a Codex user believing they are running the pipeline when they are running a third of it.

---

## 50% Rule Check

Same business goal, half the code: **ship Option A's destination map without the relocation, and
correct `AGENTS.md`.** That alone makes Codex find the skills — the user's actual reported symptom —
for roughly 15 ref changes instead of 225.

What the other 210 buy is *not* function; it is the removal of Claude-privilege from the layout, and
the property that harness N+1 costs a map entry rather than a restructure. That is real, and it is
what the user selected. But it should be bought knowingly, and it is a legitimate fallback if the
relocation proves hostile mid-flight — Option B degrades cleanly to Option A, which is a reason to
prefer it over C.

---

## Recommended Path

**Option B**, split into two tasks that fail differently and must not be merged into one:

- **B1 — Relocation.** Move `skills/` + `agents/` to plain root; add committed symlinks at
  `.claude/skills`, `.claude/agents`; rewrite the 225 live refs; leave all 1,764 historical refs
  untouched; regenerate `memory/codebase-map.md` via `/map-codebase` rather than editing it.
  Success = the full suite green and this repo still able to run its own skills.
- **B2 — Projection + adapters.** `MANIFEST` destination map, `setup.sh --harness <name>`,
  `AGENTS.md` corrected with a real Codex limits section, `.gitignore` entries for generated vendor
  dirs. Success = a fresh install with `--harness codex` produces a working `.codex/skills/` and a
  Codex session that finds a skill by name.

Hooks stay at `.claude/hooks/`. Option C's adapters are explicitly deferred until a real format
divergence is measured — with one exception carried forward now: **B2 must fail loudly on any skill
body over Codex's 8 KB cap**, rather than silently shipping a truncated skill.

Both tasks hit Hard-Stop Gate 2's C2/Medium floor ("restructure", "migrate to pattern").

---

## Surgical Scope

**Must be touched (B1)**: `.claude/skills/*` → `skills/*`, `.claude/agents/*` → `agents/*`,
`.claude/hooks/` (12 files, 55 refs), `tests/` (6 files, 58 refs), `scripts/` (5 files, 33 refs),
`docs/claude-md/` (3 files, 18 refs), `CLAUDE.md` (15 refs), `CLAUDE_LEGACY.md` (4 refs),
`templates/` (2 files, 4 refs), `MANIFEST`, `.gitignore`.

**Must be touched (B2)**: `setup.sh`, `update.sh`, `lib/harness-fetch.sh`, `MANIFEST`, `AGENTS.md`,
`.cursor/rules/agent-base.mdc`, `tests/test_setup.sh`, `tests/test_update.sh`.

**Must NOT be touched — prohibition, not preference**: `memory/decisions.md`, `memory/learnings.md`,
`memory/glossary.md`, `memory/learning-records/`, all of `tasks/`, `PROJECT_KANBAN.md`, `reports/`,
`docs/ddr/`, `docs/adr/`, and every `BRAINSTORMING_LOG_*.md`. These record what was true at the time
and are the project's audit trail. 1,764 refs live here.

**Regenerate, do not edit**: `memory/codebase-map.md` (39 refs) — via `/map-codebase` after B1.

---

## Edge Case Checklist for TASK_GUIDE

- [ ] A repo-wide `sed`/`xargs` rewrite is **prohibited**; the rewrite must be scoped to the live
      file list and the historical ref count re-counted afterwards as proof (expect 1,764, unchanged)
- [ ] Symlink survives `git clone` fresh (git stores symlinks; verify on a clean clone, not in place)
- [ ] Symlink survives `git worktree add` — every Stage 3 agent depends on this
- [ ] Windows / no-developer-mode: document the copy fallback; do not assume symlink support
- [ ] `setup.sh --copy` mode still works (it already refuses to overwrite a symlink — check the
      interaction with a canon that is now itself symlinked)
- [ ] `update.sh`'s `.claude/harness-lock.json` hash comparison against relocated paths — a stale
      lock must be detected, not silently mismatched on every file
- [ ] An existing downstream install upgrading across the relocation: does `update.sh` orphan the
      old `.claude/skills/` copies, or leave two live sets of skills?
- [ ] A skill body over Codex's 8 KB cap → **fail loudly**, never truncate
- [ ] `--harness` with an unknown name → clear error, not a silently empty install
- [ ] `--harness` run twice → idempotent, no duplicate or half-written vendor dir
- [ ] Vendor dirs gitignored downstream but canon committed — confirm a fresh clone of a downstream
      project still installs cleanly
- [ ] Every adapter states which gates that harness cannot enforce (T085 defect class)

---

## Next Actions

1. User selects a path below.
2. Answer the three Questions for the User — especially Q1 (harness count), which determines whether
   DDR-0006 must be formally reopened at N=4.
3. Write the DDR (`docs/ddr/NNNN-canonical-skills-at-plain-root.md`), stating its relationship to
   DDR-0006 (different scope: assets, not doctrine) and ADR-0001 (unchanged: per-project, copy).
4. Stage 2 `/plan` → `to-issues` for B1 and B2, both C2/Medium minimum.
5. **T095 deferred by the user 2026-08-27.** Consequence, recorded so it is not rediscovered: T094
   stays unpushable (the gate cannot see its worktree evidence), and every task whose row reaches
   Ready for Review before its push hits the same block — including B1 and B2. Work proceeds; the
   integration step is what is deferred. Original note: blocked until `T094` lands, itself blocked by `T095` (the merge gate cannot see evidence
   created in a worktree).

---

## User Selection

> **Selected path**: **Option B** — relocate canon to plain root, project everywhere including
> Claude, split into B1 (relocation) and B2 (projection + adapters). Option C's per-harness
> adapters deferred; Option A retained as the documented fallback if B1 turns hostile mid-flight.
> **Date**: 2026-08-27 (user)
> **Notes**: Canon location, per-project scope, copy-downstream, and symlink-for-dogfooding were
> locked during grilling on 2026-08-27 and are inputs to this log, not open options within it.
