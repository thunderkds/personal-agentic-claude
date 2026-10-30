# BRAINSTORMING_LOG — Multi-Provider Doctrine Delivery

**Date:** 2026-08-24
**Tier:** Standard (direction converged in `grill-with-docs mode=requirement`; open question is *how*, not *what*)
**Requested by:** user — "this kit can work with codex, cursor, ... not only claude code"
**Locked before this session (grill output):**
- Goal is **additive**: all providers welcome, Claude Code loses nothing. Not a replacement of `CLAUDE.md`.
- Shape: **one primary (the existing `CLAUDE.md` + `docs/claude-md/`), other providers refer to it.**
- Amendment accepted: **split by mandate** (T069 precedent) — non-negotiables are *inlined* into each
  provider's auto-injected file; deep reference stays behind a *pointer*.

---

## The Problem Space

The kit's doctrine is delivered through channels that are **provider-specific and not interchangeable**:

| Channel | Auto-injected by | Not read by |
|---|---|---|
| `CLAUDE.md` (200 lines) | Claude Code | Codex, Cursor |
| `AGENTS.md` (12 lines) | Codex (and increasingly others) | Claude Code |
| `.cursor/rules/*.mdc` (does not exist) | Cursor | everyone else |

Verified against the repo on 2026-08-24:
- `docs/claude-md/` holds **402 lines** across 6 files; provider-coupled references (`Skill(`, `Agent(`,
  `Claude Code`, `.claude/`) number **38 total** and are concentrated in `pipeline-stages.md` (27 of 38).
  `phase0-project-initiation.md` (71L) and `code-naming-conventions.md` (30L) are **already fully neutral**.
- `AGENTS.md` is 12 lines and **deliberately carries no Karpathy table and no Hard-Stop Gates** (T051,
  2026-08-04) to avoid becoming a second source of truth.
- `MANIFEST` already deploys `AGENTS.md` and `docs/claude-md` downstream. `CLAUDE.md`/`CLAUDE_LEGACY.md`
  are handled separately by `setup.sh` (greenfield/brownfield choice, installed as a real copy).
- `.cursor/` **does not exist** in this repo.
- Enforcement is Claude-only: **9 hooks** in `.claude/hooks/`, **30 skills** in `.claude/skills/`.
  `docs/MULTI_AGENT.md` already states review / `verify` / `migration-safety` / `ship` / git-guardrails
  **do not port**.

**The core challenge is not file layout — it is that a pointer is not a guarantee.**
Measured precedent (T069): `general-agent-template.md` was reachable only via a pointer that all four
role guides carried, and the event trace showed **9 `Read` records across 66 task buckets**. The kit has
now hit this failure class three times (T041 → T066 → T069), plus T085's "link that looks live and isn't".

**Second challenge: mirrors drift.** `CLAUDE_LEGACY.md` is **629 lines**, hand-synced against `CLAUDE.md`
by written policy. That policy is the standing proof that discipline alone does not hold a mirror in sync.

---

## The Alternatives

### Path A — Static hand-written adapters (The Simple Path)
Write `AGENTS.md` (~40 lines) and `.cursor/rules/agent-base.mdc` by hand. Each inlines the
non-negotiables block and points at `docs/claude-md/` for depth. `CLAUDE.md` unchanged.
Drift caught by a conformance test asserting the non-negotiables appear in every adapter.

- **Pros:** smallest diff; no new machinery; matches T051's shipped decision for `AGENTS.md`;
  ships in one C1 task. Every adapter is auto-injected in full by its own provider.
- **Cons:** N copies of the non-negotiables text. Adding a 7th Hard-Stop Gate means editing N files.
  The test tells you they drifted; it does not stop them drifting.

### Path B — Generated adapters from a neutral core (The Scalable Path)
Extract the non-negotiables into `docs/core/non-negotiables.md`. A generator script
(`scripts/gen-provider-adapters.sh`) renders each provider file from it. CI asserts
`git diff --exit-code` after regeneration.

- **Pros:** one edit point; drift becomes structurally impossible, not merely detected; adding a
  provider is a template, not a rewrite.
- **Cons:** new machinery this repo has previously rejected at this size — T051's own brainstorm
  converged **static over generated** on the reasoning that "a ~15-line file doesn't justify generator
  machinery". Generated files must be committed (providers read the repo, not a build), so the
  generator is a *second* thing that can be stale. Adds a CI entry point — the exact gap T036 found
  when `smoke-install.sh` was silently red for 3 days across 5+ merged PRs.

### Path C — Full doctrine duplication into every adapter (The Maximal Path)
Every provider file carries the complete doctrine (~200 lines each). No pointers at all.

- **Pros:** zero reachability risk; every provider is genuinely first-class with nothing behind a read.
- **Cons:** three near-identical 200-line files — a second, third, and fourth source of truth, which is
  precisely what T051 refused. `CLAUDE_LEGACY.md` already demonstrates the outcome at 629 lines.
  Directly violates Simplicity First. **Rejected before adversarial review.**

### The 50% Rule — same goal, half the code
`AGENTS.md` need not restate the non-negotiables in prose. The Karpathy table measured **622 chars**
(T069); Hard-Stop Gates are the larger half. A ~40-line adapter can carry the four principle *names* +
the six gate *titles* as one-liners, with the full text one pointer away — the mandate reaches the
context, the elaboration does not need to. This roughly halves each adapter versus a full inline and is
compatible with Path A or B.

---

## Adversarial Review — "Why this might fail"

**Path A fails if** the non-negotiables text is edited in `CLAUDE.md` and the conformance test only
checks *presence*, not *equivalence*. This repo has recorded **9 vacuous-assertion incidents**; the
closest analogue is T085, where a step-limit assertion measured *passing against a README that still
said the wrong number* because `.` does not match a newline. An assertion like
`assert "Hard-Stop" in agents_md` is that same shape and would free-pass a drifted mirror. Mitigation:
assert byte-identical shared spans with `grep -qF`, plus a mutation control proving RED — the T069
pattern, not the T085 one.

**Path B fails if** the generator is not wired into CI, or is wired and goes silently red (T036, 3 days
/ 5+ PRs). It also fails at the downstream boundary: `setup.sh` copies files into *user projects* that
have no generator and no CI, so a downstream user editing their `AGENTS.md` gets no protection either
way — the generator protects this repo only, which is a narrower benefit than it first appears.

**Path C fails** on maintenance the first time a gate changes; `CLAUDE_LEGACY.md` is the counterexample
already in the tree.

**All paths fail if** they overclaim. `docs/MULTI_AGENT.md` is honest today that review, `verify`,
`ship`, `migration-safety` and the git-guardrails hook **do not port**. Nine hooks and thirty skills are
Claude Code primitives. Any adapter that reads as "run the 5-stage pipeline on Codex" ships the T085
defect in a new file: a promise that looks live and is not. **Every adapter must state its own limits.**

**Silent failures to watch:**
- A downstream project installs the kit with only Codex; hooks never fire, so the merge gate, step
  limit, and guide validation are all absent while the doctrine says they are mandatory.
- Cursor's `.mdc` files need frontmatter (`alwaysApply`) to be auto-attached — a plain copy of Markdown
  is an *optional* rule, silently reproducing the T069 failure inside the new file.
- `MANIFEST` gained a race in T051 when two agents inserted lines after the same `templates` line
  (`memory/learnings.md:409`). Adding `.cursor/rules` risks a repeat.

---

## Surgical Scope

**Should be touched:**
- `AGENTS.md` — expand 12 → ~40 lines (non-negotiables inline + pointers + explicit limits section)
- `.cursor/rules/agent-base.mdc` — new, with correct frontmatter
- `docs/MULTI_AGENT.md` — Cursor section updated; "what does NOT port" restated per-adapter
- `MANIFEST` — add `.cursor/rules` (single insertion, mind the T051 race)
- `tests/test_provider_adapters.py` — new conformance test + mutation control
- `README.md` / `site/` — one line each; the kit's multi-provider claim becomes true and should say so

**Must NOT be touched:**
- `CLAUDE.md` — the primary stays primary; **additive only** (user's explicit instruction)
- `.claude/hooks/`, `.claude/skills/` — no behaviour change in this work
- `CLAUDE_LEGACY.md` — separate sync policy; out of scope, do not fold in
- `docs/claude-md/pipeline-stages.md` — neutralising its 27 refs is a *separate* task, not this one

---

## Recommended Path

**Path A + the 50% Rule**, i.e. static hand-written adapters carrying a compact non-negotiables block,
guarded by an equivalence test with a mutation control.

Rationale, grounded rather than aesthetic:
1. It is the user's own stated shape (one primary, others refer) with the single T069-derived amendment.
2. T051 already ran this exact comparison for `AGENTS.md` (static / generated / skip) and converged on
   static; nothing measured since has changed the inputs.
3. Path B's protection stops at this repo's CI and does not reach installed downstream projects, which
   is where the kit actually runs.
4. The whole change is documentation + one test — Low risk, no runtime code path.

**Reversal to record:** this amends T051's deliberate exclusion of the Karpathy table and Hard-Stop
Gates from `AGENTS.md`. The reason is T069's measurement (a pointer is not a guarantee), and it must be
written down as a reversal with its reason, not slipped in silently.

---

## Next Actions for Stage 2

1. Register one task, C1 / Risk Low / P1 — or split adapters and test if the guide exceeds one slice.
2. Complexity check: this is documentation, not "refactor/restructure", so Hard-Stop Gate 2's C2 floor
   does **not** apply. If scope grows to neutralising `pipeline-stages.md`, it does — split instead.
3. Acceptance criteria must include a **negative**: no adapter claims a gate it cannot enforce.
4. Evidence: conformance test RED under mutation, pasted. Gate 5 applies — no test, not done.
5. UI/Design Evidence rows → N/A with justification (docs only; the `site/` line is a content edit).
6. DDR gate: hard to reverse? no. Surprising without context? **yes** (it reverses T051). Genuine
   trade-off? **yes** (A vs B). That is **2 of 3 → a DDR is warranted**, not just a `decisions.md` line.

## Edge Case Checklist (for the TASK_GUIDE)

- [ ] Cursor `.mdc` frontmatter set so the rule is **always applied**, not optional
- [ ] `MANIFEST` insertion does not collide with the T051 race pattern
- [ ] Downstream install path (`setup.sh`) actually deploys the new adapter — verify, don't assume
- [ ] Each adapter names what its provider **cannot** enforce (hooks, skills, review, verify, ship)
- [ ] Conformance test asserts equivalence, not presence — `grep -qF`, newline-safe, mutation-controlled
- [ ] `AGENTS.md` stays a mirror in *authority* even while gaining content: the canonical pointer line survives
