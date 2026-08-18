---
name: write-better-skill
description: Use when writing, reviewing, or refactoring any SKILL.md in this framework — or when another skill (e.g. teach) needs the craft vocabulary and principles for producing a well-structured skill. Provides the authoritative reference for invocation choice, leading words, information hierarchy, completion criteria, and failure modes.
---

## Role: Skill Craft Reference

The authoritative vocabulary and principles for writing predictable Claude Code skills in this framework. Consumed by the `teach` skill during draft generation and invoked directly when auditing or refactoring an existing SKILL.md. All reference — no sequential steps.

**Predictability** — the agent taking the same *process* every run, not producing the same output — is the root virtue every rule below serves.

---

## Invocation

Two choices, trading different loads:

- **Model-invoked**: keep a `description` with rich trigger phrasing. Other skills can reach it. Contributes **context load** every turn. Use when the agent must fire it autonomously or another skill must call it.
- **User-invoked**: set `disable-model-invocation: true`. Only the user (typing the name) can invoke it — no other skill can reach it. Zero context load; costs **cognitive load** (you must remember it exists). Description becomes human-facing; strip trigger phrasing.

Pick model-invocation only when autonomous reach is required. When user-invoked skills multiply past memory, a **router skill** (one user-invoked skill that names the rest) cures the cognitive load.

### Writing the description

A model-invoked description does two jobs: state what the skill is, and list the **branches** that trigger it. Every word is context load — prune harder than the body.

- **Front-load the leading word** — the description is where it does its invocation work.
- **One trigger per branch.** Synonyms that rename a single branch are duplication — collapse them.
- **Cut identity already in the body.** Keep triggers plus any "when another skill needs…" reach clause.

Read [`references/descriptions.md`](references/descriptions.md) when writing or revising a model-invoked `description` — it carries the rules that decide whether the skill fires at all (imperative phrasing, user intent, pushiness) and the trigger-eval method for testing one.

---

## Agent Skills Spec Conformance

This framework's skills implement the open [Agent Skills specification](https://agentskills.io/specification). The rules below are **normative** — a skill that breaks one is malformed, not merely unpolished. Checked automatically by `.claude/hooks/tests/test_skill_spec_conformance.py` over every directory in `.claude/skills/`.

**`name`** (required):
- 1–64 characters
- unicode lowercase alphanumeric (`a-z`, `0-9`) and hyphens (`-`) only — uppercase is invalid
- must not start or end with a hyphen
- must not contain consecutive hyphens (`--`)
- must match the parent directory name

**`description`** (required): non-empty, max 1024 characters. Craft guidance is in *Writing the description* above; this is the hard limit.

**Optional fields:**
- `license` — the licence applied to the skill. Add only when the skill ships under terms different from the repo's; keep it to a licence name or a bundled file name.
- `compatibility` — max 500 characters. Add only when the skill has real environment requirements (intended product, required system packages, network access). Most skills do not need it.
- `metadata` — a map from string keys to string values, for properties the spec does not define. Use unique-ish key names to avoid collisions.
- `allowed-tools` — **out of scope in this framework.** The spec marks it Experimental and states support varies by implementation; no skill here uses it.

**Progressive-disclosure budgets** (spec numbers, not prose):
- metadata (`name` + `description`) ≈ **100 tokens**, loaded at startup for **every** skill — this is why description pruning pays repo-wide
- `SKILL.md` body: **≤ 500 lines** and **≤ 5,000 tokens** once the skill activates
- resources (`scripts/`, `references/`, `assets/`) load **on demand only**

**Bundled directories** — the spec's conventional layout beside `SKILL.md`:
- `scripts/` — executable code the agent runs; self-contained or with documented dependencies
- `references/` — documentation loaded on demand; keep each file focused
- `assets/` — templates, images, data files

**File references** use relative paths from the skill root (`references/REFERENCE.md`, `scripts/extract.py`) and stay **one level deep**. Avoid deeply nested reference chains.

---

## Leading Words

A **leading word** is a compact concept from the model's pretraining that the agent thinks with while running the skill (e.g. *wake*, *learn*, *ship*, *tdd*, *diagnose*). Repeated in the body, it accumulates a distributed definition — anchoring a whole region of behaviour in fewer tokens by recruiting priors the model already holds.

It serves predictability twice: in the body it anchors *execution*; in the description it anchors *invocation* (shared language links to the skill and fires it more reliably).

Hunt for restatements that a leading word can retire. A triad restated at three sites, a sentence gesturing at one idea — each is a passage that collapses into a single token:

- "fast, deterministic, low-overhead" → *tight*
- "a loop you believe in" → *red*

You win twice: fewer tokens, sharper hook for the agent.

---

## Information Hierarchy

A skill is built from **steps** (ordered actions) and **reference** (rules, definitions, facts). The hierarchy ranks by how immediately the agent needs the material:

1. **In-skill step** — an ordered action in SKILL.md. Each step ends on a **completion criterion**: checkable (can the agent tell done from not-done?) and exhaustive ("every modified file accounted for", not "produce a change list"). Vague criteria invite **premature completion**.
2. **In-skill reference** — definitions and rules consulted on demand. A legitimately flat peer-set is fine (not a smell). This skill is all reference.
3. **External reference** — pushed out of SKILL.md into a sibling file (e.g. `GLOSSARY.md`), reached via a **context pointer**. Loaded only when the pointer fires.

**Progressive disclosure** is the move down the ladder — out of SKILL.md into a linked file — so the top stays legible. A **context pointer** must name the *trigger condition* for loading the file, not just its existence, and must be written as a **Markdown link** — the two pointers in this file are the worked examples: each names when to load its target, and each is a link. Never a bare "see `references/` for details", and never a path in plain backticks: `.claude/hooks/tests/test_skill_reference_pointers.py` resolves links only, so a backticked path is a pointer nothing checks — it can rot to a missing file and the suite stays green. A pointer without a trigger condition is a pointer the agent cannot decide to follow; a pointer without link syntax is one nothing can verify.

**Co-location**: keep a concept's definition, rules, and caveats under one heading so reading one part brings its neighbours.

Split signal: inline what every branch needs; push behind a pointer what only some branches reach.

Read [`references/instruction-patterns.md`](references/instruction-patterns.md) when drafting or restructuring a skill *body* — six reusable structures (gotchas, output templates, checklists, validation loops, plan-validate-execute, bundled scripts) and the rules for calibrating how tightly each part instructs.

---

## Completion Criteria

Every step must end on a criterion that is **checkable** and **exhaustive**:

- Checkable: the agent can binary-test done vs. not-done.
- Exhaustive: the criterion names every item that must be accounted for, not just "produce something."

A demanding criterion drives thorough **legwork** — the digging within the work. Even flat reference binds this way: "every rule applied" is an exhaustive criterion over a peer-set.

Defence against premature completion, in order:
1. Sharpen the criterion first (cheap, local).
2. Only if irreducibly fuzzy *and* rushing is observed: hide post-completion steps by splitting the skill.

---

## When to Split

Each split spends one of the two loads — split only when the cut earns it:

- **By invocation**: split off a model-invoked skill when you have a distinct leading word that should trigger independently, or another skill must reach it. You pay context load for the new description.
- **By sequence**: split a run of steps when the steps still ahead tempt the agent to rush the current one. Keeping them out of view encourages legwork.

---

## Pruning

Keep each meaning in a **single source of truth**: one authoritative place, one-place edits.

Check every line for **relevance**: does it still bear on what the skill does?

Hunt **no-ops** sentence by sentence — not just line by line. Run the no-op test on each sentence in isolation: does removing it change agent behaviour versus the default? If not, delete the whole sentence rather than trim words. Be aggressive — most failing prose should go, not be rewritten.

A weak leading word (*be thorough*) is a no-op when the agent is already thorough by default. The fix is a stronger word (*relentless*), not a different technique.

---

## Sourcing

**Start from real expertise.** A skill drafted from the model's general training knowledge produces generic filler — "handle errors appropriately", "follow best practices" — instead of the specific conventions, edge cases, and commands that make a skill worth loading. The model already knows the generic version; the skill exists for what it does not know.

Source material must be **project-specific**: execution traces (`memory/event-trace/`), corrections the user made mid-task, git history — especially fixes, which show what actually went wrong — review comments, and real failure cases (`memory/learnings.md`).

Two routes to it:
- **Extract from a completed hands-on task.** Run the real task with an agent, then lift the reusable pattern: the sequence that worked, each correction you made, the input/output shapes, and the project facts you had to supply.
- **Synthesize from existing project artifacts.** Feed the body of knowledge you already have — runbooks, specs, schemas, configs, incident write-ups — and draft from it. A skill built from this repo's own hook failures beats one built from an article about writing hooks.

Then refine against real execution: run the draft on real tasks and feed back *all* results, not just the failures. Read the traces, not only the final output — an agent trying several approaches signals instructions that are too vague; an agent following an instruction that does not apply signals one that should be conditional or cut.

---

## Fidelity Gate (Hallucination Check)

Consulted by `teach` and `craft-agent` immediately before they emit a draft — a drafted skill/agent is *durable*: unlike a bad code change caught by Stage 4 review for one task, a hallucinated or over-scoped draft lives in `.claude/skills/` or `.claude/agents/` and silently affects every future session until someone notices.

Check every claim in the draft against a source, not against plausibility:

1. **Traceability** — every capability the draft claims (each Workflow step, each Karpathy override, each "Required skills/expertise" line) must trace to `PRD.md`, `PROJECT_SPEC.md`, or the user's literal words in the current session. An untraceable claim is a hallucination — cut it, don't soften it.
2. **Reference resolution** — every `Skill({ skill: "..." })` or `Agent({ subagent_type: "..." })` call written inside the draft must resolve to a name that actually exists (check `.claude/skills/*/SKILL.md` and `.claude/agents/*.md` frontmatter). If it doesn't, don't drop the draft — flag the line inline as `[UNRESOLVED: references "<name>" — does not exist yet, draft separately]` and still emit.
3. **Scope containment** — the draft must not claim authority the Permanent Rules reserve elsewhere (e.g. an agent writing to `memory/` directly, when only the Supervisor writes memory). Flag any such overreach rather than emitting it silently.

**Completion criterion**: every claim traces to a source or is cut; every internal `Skill()`/`Agent()` reference resolves or is flagged `[UNRESOLVED: ...]`; no unflagged Permanent-Rules overreach. State "Fidelity gate: PASS" or list the cuts/flags immediately before the Registration checklist.

---

## Pipeline Integration (This Framework)

| Stage | Skills that belong here |
|---|---|
| 0.5 Brainstorming | `brainstorming`, `grill-with-docs` |
| 1 Setup | `git-guardrails-claude-code`, `update-config`, `fewer-permission-prompts` |
| 3 Execution | `tdd`, `diagnose`, `run`, `migration-safety` |
| 4 Review | `code-review`, `security-review`, `blast-radius`, `html-report` |
| 5 Integration | `verify`, `ship` |
| Cross-cutting | `learn`, `wake`, `compact-memory`, `thinking-report` |
| Meta | `teach`, `write-better-skill` |

Registration checklist for any new skill:
- [ ] Folder name matches `name:` frontmatter exactly
- [ ] Frontmatter satisfies *Agent Skills Spec Conformance* above — verified by `python3 -m pytest .claude/hooks/tests/test_skill_spec_conformance.py`, not by re-deriving the rules
- [ ] Added to the custom-skill table in `CLAUDE.md`
- [ ] One-liner added to `memory/MEMORY.md` hot tier
- [ ] `description` uses trigger phrasing (model-invoked) or human summary (user-invoked)

---

## Failure Modes

- **Premature completion** — ending a step before it's genuinely done, attention slipping to *being done*. Sharpen the completion criterion first; only split if that fails.
- **Duplication** — the same meaning in more than one place. Costs maintenance and tokens; inflates prominence past real rank.
- **Sediment** — stale layers that settle because adding feels safe and removing feels risky. The default fate of any skill without a pruning discipline.
- **Sprawl** — a skill simply too long, even when every line is live and unique. Cure: disclose reference behind pointers; split by branch or sequence.
- **No-op** — a line the model already obeys by default. Test: does it change behaviour versus the default? If not, delete.
