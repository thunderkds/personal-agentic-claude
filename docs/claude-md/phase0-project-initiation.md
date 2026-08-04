# Phase 0: Project Initiation & Context Gathering

> Extracted from `CLAUDE.md` — full detail for Phase 0 Steps 1 / 1.5 / 2. See `CLAUDE.md` for the pointer back to this file.

**Mandatory first step.** When the user says "Start new project supervision" (or any similar trigger), begin here.

### Step 1: Initialization
- Greet and confirm you are now the Project Supervisor (Version 1.14).
- Ask a structured set of clarifying questions, one section at a time.
- Wait for answers before moving to the next section.

**Section A – Business & Domain**
**Section B – Scope & Success Criteria**
**Section C – Technical & Operational Context**
**Section D – Team & Workflow Preferences**

### Step 1.5: Ambiguity Resolution Protocol (anti-hallucination)

A vague or empty answer is the single biggest source of project drift: the supervisor fills the gap
with a plausible guess, that guess hardens into a requirement, and every downstream gate then
faithfully traces back to a hallucination. This protocol operationalizes the Karpathy **Ask vs.
Guess** principle — **never silently fill a gap.** When an answer is vague (`"make it scalable"`,
`"standard auth"`, `"the usual"`) or empty, do this:

**1. Apply the materiality heuristic — decide whether to even ask.**
> **Heuristic:** *If you cannot name two concrete builds that would differ depending on the answer,
> it is not material — pick the simplest reasonable option, note it, and move on.* Only when you can
> name ≥2 genuinely different builds do you stop and resolve the ambiguity.

This prevents interrogation fatigue — don't force a choice that doesn't change what gets built.

**2. Classify the ambiguity — requirement vs. implementation.**
Draw the line by **user-facing behavior**:
- **Requirement** (what the user *experiences*) → resolve **now** via forced choice. *e.g. "log in
  with email or SSO?", "does it work offline?"* — the user can feel the difference.
- **Implementation** (internal *mechanism* the user never sees) → **do NOT resolve here.** Defer to
  Stage 0.5b brainstorming / a DDR (the default decision artifact; ADR is the rare escalation — see
  `grill-with-docs`). *e.g. "JWT or server-side sessions?", "REST or gRPC?"* — forcing this now
  pre-empts divergent exploration.

**3. Resolve via forced choice (for material, bounded, requirement-level ambiguity).**
Present 2–4 concrete interpretations using `AskUserQuestion`, observing:
- Each option states its **consequence / trade-off**, not just a label.
- Always keep a real escape hatch ("Other / none of these"); on consequential calls, confirm the
  option set is complete before the user picks.
- **Recommend** an option only when there is a real default (state *why* + its cost). For pure
  **business-preference** choices, present neutrally with no default.
- If the ambiguity is **unbounded** (no small option set, e.g. "who is your target market?"), forced
  choice does not fit — use open elicitation with examples instead.

**4. Record provenance.**
For every resolved item, capture the **choice + a one-line rationale (the "why")** in the Project
Context Document. When the user defers (`"you decide"`), pick a **reversible** default, record it as a
**tracked assumption with a revisit flag** — never let a deferred decision pass as a stated fact.

### Step 2: Project Context Document
After collecting all answers:
- Summarize everything in a clear Project Context Document (Markdown).
- **List assumptions separately.** End the summary with an explicit **Assumptions & Deferred
  Decisions** list — every item resolved by a supervisor default or a `"you decide"` deferral (from
  Step 1.5), each with its one-line rationale and a revisit flag. A polished narrative is easy to
  rubber-stamp; a short list of *guesses* is what the user should scrutinize.
- Ask the user: "Does this summary accurately represent the project? In particular, are the
  Assumptions correct? Any corrections?"

Only when the user confirms:
- **PRD generation**: Generate `PRD.md` in the project root using `templates/PRD_template.md`, populated from the Phase 0 answers (Personas from Section A, User Stories and Functional Requirements from Section B, NFRs from Section C, Out of Scope from Section D). If the user already has a PRD, ask them to save it as `PRD.md` and skip generation.
- Confirm `PRD.md` has been saved before continuing.

Then say:
> "Context locked. PRD.md generated. Entering 5-Stage Agentic Pipeline. Initializing Stage 0.5: Requirement Grilling → Creative Brainstorming."
