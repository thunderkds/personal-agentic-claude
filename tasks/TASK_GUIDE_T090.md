# TASK_GUIDE — T090: Provider adapters — make "works with any provider" structurally true
**Date**: 2026-08-24
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: Common-Infrastructure-Agent
**Agent guide**: `.claude/agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. C1 multi-file task — also read `docs/ddr/0006-provider-adapters-inline-non-negotiables.md` and
   `docs/brainstorming/BRAINSTORMING_LOG_multi-provider.md`. Skip `memory/codebase-map.md`; every file you touch is named below.

---

## Requirement (Pillar 1 — Adapt the requirement)

User request, 2026-08-24, verbatim in substance:

> "following the requirement that, this kit can works with the codex, cursor, ... or another provider,
> not only claude code, so we should update the supervisor file. I saw some of repos using the AGENT.md
> as source of truth and the CLAUDE.md will refer to the AGENT by the path. is it good?"

and, after grilling:

> "for final, all of provider are welcome, not the way we remove to use the CLAUDE."
> "could we implement 1 primary (which are existed) and then if another provider need it, we should
> add the refer to the primary."

**Restated intent** (Supervisor's interpretation):
> `CLAUDE.md` + `docs/claude-md/` stay the one primary source of truth. Every other provider gets a thin
> adapter file in the channel that provider actually auto-reads, carrying the kit's non-negotiable rules
> inline and pointing at the primary for everything else — additive, with Claude Code behaviour unchanged.

**Out of scope** (explicitly NOT this task):
- Editing `CLAUDE.md`. It is the primary and this change is additive. Do not touch it.
- Neutralising `docs/claude-md/pipeline-stages.md` (27 provider-coupled refs) — its own task; trips the C2 floor.
- `CLAUDE_LEGACY.md` — separate sync policy, deliberately not folded in.
- Any generator script. DDR-0006 rejected generated adapters; do not build one.
- Making hooks or skills run on non-Claude providers. Impossible here and not attempted.

> **AMENDED 2026-08-24, after Stage 4, before merge.** The original guide listed `site/` as
> *"only if the site already carries a provider claim — check first"*. The implementer checked,
> correctly found none (`grep -c "AGENTS" site/index.html` → **0**), and left it alone. The guide
> was wrong, not the implementer: the site is the **designated full reference** (T083/T085), and
> `README.md` states directly below T090's own new line that the full reference *"lives on the
> project site"*. So the branch as it stands advertises multi-provider support and points at a
> reference silent on it — **T085's P1b defect recurring in the same place**. ACs 12–14 close it.
> Note the gap is older and wider than T090: the site has never mentioned `AGENTS.md` at all
> (since T051), and its opening line still reads *"A multi-agent supervisor framework for Claude
> Code"*. Fixing that line is **in** scope; rewriting the site's other sections is **not**.

**Requirement Refs**: None — this repo has no `PRD.md`. The requirement is the user request above,
converged through `grill-with-docs mode=requirement` and `brainstorming` on 2026-08-24, and recorded in
`docs/ddr/0006-provider-adapters-inline-non-negotiables.md`.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request — user replied "agree, let go" on 2026-08-24
- [x] Domain terms align with the project's language ("primary", "adapter", "non-negotiables", "split by mandate")
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] Requirement Refs: N/A (no `PRD.md`) — traced to the user request and DDR-0006 instead

---

## Dependencies & Reachability

**Depends on**: None — every file this task needs already exists.

**Entry point**: `AGENTS.md` — the adapter a non-Claude CLI auto-reads at the repo root.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `AGENTS.md` contains all four Karpathy principle names, byte-identical to their spelling in `CLAUDE.md` | "all providers are welcome" — the mandate must reach a Codex user |
| 2 | `AGENTS.md` contains all six Hard-Stop Gate titles, byte-identical to `CLAUDE.md` | same |
| 3 | `AGENTS.md` contains the untrusted-content boundary rule and the "no TASK_GUIDE = no work" rule | same |
| 4 | `.cursor/rules/agent-base.mdc` exists, carries the same inlined non-negotiables, and its frontmatter sets `alwaysApply: true` | "cursor, ... or another provider" — an optional rule reproduces T069 |
| 5 | Every adapter keeps a line stating `CLAUDE.md` / `.claude/agents/` remain canonical | "1 primary … others refer to the primary" |
| 6 | Every adapter has a section naming what that provider **cannot** enforce (hooks, skills, review, `verify`, `ship`, `migration-safety`, git-guardrails) | adversarial finding: overclaiming reproduces T085 |
| 7 | Each adapter points at `docs/claude-md/` for pipeline/Phase 0/folder/naming/memory detail rather than restating it | "refer to the primary"; Simplicity First |
| 8 | `CLAUDE.md` is byte-identical to its pre-task state | "not the way we remove to use the CLAUDE" |
| 9 | **Negative**: the conformance test goes RED when any single non-negotiable is mutated in any one adapter — proven by a mutation control, output pasted | this repo has 9 recorded vacuous-assertion incidents |
| 10 | `MANIFEST` deploys `.cursor/rules` downstream, and `AGENTS.md`'s existing line is unchanged | adapters must reach installed projects, not just this repo |
| 11 | Each adapter stays thin: ≤ 60 lines. Principle **names** and gate **titles** only — not their prose | the 50% cut agreed with the user |
| 12 | `site/index.html` carries a **Providers** section naming both adapters, what each provider auto-reads, and what a non-Claude provider cannot enforce | the README now claims multi-provider support and points at the site as the full reference; today that claim dead-ends |
| 13 | The site's **Repository layout** section lists `AGENTS.md` and `.cursor/rules/agent-base.mdc` | the layout section is factually incomplete without them |
| 14 | **Negative**: a test asserts the site's Providers section stays in sync with the adapter files that actually exist on disk, and goes RED when an adapter is renamed or removed | Hard-Stop Gate 5; `site/index.html` is hand-written HTML with no other guard |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | Repo at HEAD after implementation | Every non-negotiable string present in `CLAUDE.md` is present byte-identical in `AGENTS.md` and `.cursor/rules/agent-base.mdc` | automated test (`grep -qF`-equivalent, newline-safe) |
| 2 | A Karpathy principle name is renamed in `AGENTS.md` only | Test RED, naming the file and the missing string | automated test + mutation control, pasted |
| 3 | A Hard-Stop Gate title is deleted from `.cursor/rules/agent-base.mdc` only | Test RED, naming the file and the missing string | automated test + mutation control, pasted |
| 4 | A 7th gate title is added to `CLAUDE.md` but to no adapter | Test RED — the test reads `CLAUDE.md` as the source list, never a hardcoded copy | automated test + mutation control, pasted |
| 5 | `.cursor/rules/agent-base.mdc` frontmatter has `alwaysApply` removed or set false | Test RED | automated test |
| 6 | `CLAUDE.md` diffed against `main` | Zero changes | `git diff --exit-code main -- CLAUDE.md` |
| 7 | An adapter's "cannot enforce" section is deleted | Test RED | automated test |

> SC4 is the load-bearing one. A test holding its own copy of the gate titles asserts nothing about
> agreement between two files — it would pass on a repo where `CLAUDE.md` and the adapters had fully
> diverged. Derive the expected strings **from `CLAUDE.md` at test time** (the T088 M3 pattern, where
> deleting `setup.sh`'s parser case is what turned the test RED).

### Verification Command (exact, runnable)

```bash
python -m pytest tests/test_provider_adapters.py -q && \
python -m pytest tests/ -q && \
git diff --exit-code main -- CLAUDE.md && echo "CLAUDE.md untouched: OK"
```

### Evidence (filled by reviewer at Stage 4/5)

> Filled by the reviewer at Stage 4/5 in `tasks/TASK_REVIEW_T090.md`, copied from `templates/TASK_REVIEW_template.md`.

---

## UI / Design Acceptance Criteria

**N/A — deleted per Hard-Stop Gate 6.** This task ships Markdown documentation and one Python test.
It renders no UI component. All three design Evidence rows are ☐ N/A with this justification.

---

## Approach

**Pattern reference**: `AGENTS.md` — imitate its existing register exactly: terse imperative bullets,
an explicit "CLAUDE.md and .claude/agents/ remain canonical" line, and a closing pointer to
`docs/MULTI_AGENT.md`. The file is being extended, not rewritten. For the test, imitate
`tests/test_site_content.py` (asserts documentation content against the live `.claude/` tree rather
than against a hardcoded expectation).

**Vital slice**: `AGENTS.md` extended with the inlined non-negotiables + limits section, plus the
conformance test. That single pair delivers most of the value — Codex is the provider with a real
auto-read channel today, and the test is what stops the whole thing rotting.

**Cut list** (deliberately NOT built):
- No generator script — DDR-0006 rejected it; the protection would not reach downstream installs.
- No Windsurf / Aider / Continue / Gemini adapter. Two providers ship; the pattern is then copyable.
- No neutralisation of `pipeline-stages.md`'s 27 refs — separate task, C2 floor.
- No change to `setup.sh`'s greenfield/brownfield prompt.
- No runtime detection of which provider is running.

**Reasoning**: converged in `docs/brainstorming/BRAINSTORMING_LOG_multi-provider.md` (Path A + the 50% cut) and recorded in
DDR-0006. The split-by-mandate rule is T069's shipped design applied one level out: content that is a
Permanent Rule goes into every guaranteed channel; advisory content stays behind a pointer.

---

## Edge Case Checklist

- [ ] Cursor `.mdc` frontmatter sets `alwaysApply: true` — without it the rule is optional and this fix
      reproduces, inside itself, the exact T069 defect it exists to close
- [ ] `MANIFEST` insertion does not collide with the T051 race (`memory/learnings.md:409` — two agents
      inserted after the same `templates` line). Insert once, verify the final file by reading it back
- [ ] `setup.sh` actually deploys `.cursor/rules` downstream — **verify by reading the script**, do not
      assume `MANIFEST` membership is sufficient
- [ ] Conformance test asserts equivalence, not presence. `assert "Hard-Stop" in text` free-passes a
      drifted mirror — that is the T085 shape. Use fixed-string, newline-safe comparison
- [ ] Expected strings derived from `CLAUDE.md` at test time, never hardcoded in the test (SC4)
- [ ] Every adapter names what its provider cannot enforce — 9 hooks and 30 skills are Claude Code
      primitives, and `docs/MULTI_AGENT.md` is already honest that review / `verify` / `ship` /
      `migration-safety` / git-guardrails do not port. Do not let an adapter contradict it
- [ ] Adapters gain content but not authority — the canonical-pointer line must survive
- [ ] `docs/MULTI_AGENT.md` says `AGENTS.md` is "not required" and "a thin mirror". After this task the
      first half is stale. Update it; do not leave two documents disagreeing (that is what let T088 live)
- [ ] Do not exceed 60 lines per adapter — inline the names/titles, not their prose

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `AGENTS.md` | 12 → ≤60 lines: inline non-negotiables (names/titles only), add a "what Codex cannot enforce" section, keep the canonical line, point at `docs/claude-md/` |
| `.cursor/rules/agent-base.mdc` | New. Same content, Cursor frontmatter with `alwaysApply: true` |
| `MANIFEST` | Add `.cursor/rules` — one insertion |
| `docs/MULTI_AGENT.md` | Cursor section points at the real `.mdc`; correct the now-stale "not required / thin mirror" framing; keep the "what does NOT port" section authoritative |
| `tests/test_provider_adapters.py` | New. Conformance test per SC1–SC7 |
| `README.md` | One line: the multi-provider claim is now true and points at the adapters |
| `site/index.html` | **(amended)** Add a `Providers` section (adapters, what each provider auto-reads, what it cannot enforce); add both adapters to `Repository layout`; correct the opening "for Claude Code" line. Do not restyle or restructure anything else |
| `tests/test_site_content.py` | **(amended)** Add the AC14 sync assertion. Imitate this file's existing pattern: assert the page against the live filesystem, never a hardcoded copy |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `CLAUDE.md` | The primary. This change is additive — the user's explicit instruction. AC8 asserts it byte-identical |
| `CLAUDE_LEGACY.md` | Separate sync policy; out of scope |
| `docs/claude-md/pipeline-stages.md` | Its 27 refs are a separate task at the C2 floor |
| `.claude/hooks/`, `.claude/skills/`, `.claude/agents/` | No behaviour change in this task |
| `setup.sh` | Read it to verify deployment; do not modify it |

---

## Test Plan

1. `tests/test_provider_adapters.py` — parse `CLAUDE.md` for the four principle names, six gate titles,
   the untrusted-content rule and the "no TASK_GUIDE = no work" rule; assert each appears byte-identical
   in every adapter. Assert the `alwaysApply` frontmatter, the canonical-pointer line, the limits
   section, and the ≤60-line ceiling.
2. Run each of the five mutation controls in SC2–SC5 and SC7. Confirm the mutation actually landed with
   `git diff --stat` **before** recording the verdict, revert with `cp` not `git checkout`, and paste
   the RED output naming the exact break.
3. Full suite for regressions: `python -m pytest tests/ -q` (baseline is 702 passing as of T089).
4. `git diff --exit-code main -- CLAUDE.md` for AC8.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: N/A — Low risk, documentation + one read-only test, no runtime code path
- [ ] Lint passes
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T090.md` (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run by the **user** — the Supervisor cannot run this gate
- [ ] `memory/MEMORY.md` updated
- [ ] Supervisor notified: task ready for Stage 4 review
