# Description Triggering

Reached from `SKILL.md`'s *Writing the description*. That section prunes; this one decides whether
the skill **fires at all**. A description the agent never matches is a skill that does not exist.

At startup the agent holds only `name` + `description` for every skill. The description therefore
carries the entire triggering burden — the body is unreachable until it fires.

---

## The four rules

- **Imperative phrasing.** "Use this skill when…", never "This skill does…". The agent is deciding
  whether to *act*; tell it when to act.
- **User intent over implementation.** Describe what the user is trying to achieve, not the skill's
  internal mechanics. The agent matches against the request, not the machinery.
- **Err on the side of pushy.** List the contexts where the skill applies, explicitly including the
  ones where the user does **not** say the domain word — "…even when the user does not mention
  'skill' or 'SKILL.md'". A description that only matches its own vocabulary misses every
  paraphrase.
- **Stay under 1024 characters.** The spec's hard limit, enforced by
  `test_skill_spec_conformance.py`. Descriptions grow during optimization — re-check after each
  revision, not once at the end.

One nuance that looks like a rule failure but is not: agents consult skills for work they cannot
already do alone. A one-step request may skip a perfectly-matching description. Judge a description
on tasks that need what the skill knows.

---

## Testing a description

Taste is not a method. A **trigger eval** is: a fixed set of realistic user prompts, each labelled
with whether it *should* fire the skill, run against the agent with the skill installed.

**Query set** — about 20 queries, roughly 8–10 should-trigger and 8–10 should-not-trigger.

*Should-trigger* queries vary along four axes: phrasing (formal, casual, typo'd), explicitness (some
name the domain, some only describe the need), detail (terse alongside context-heavy), and
complexity (single-step alongside multi-step, where the relevant part is buried in a longer chain).
The queries that earn their keep are the ones where the skill helps but the connection is not
obvious from the query — if the prompt already asks for exactly what the skill does, any description
triggers.

*Should-not-trigger* queries must be **near-misses**: they share keywords or concepts but need
something else. For a skill about writing SKILL.md files, "write a fibonacci function" tests
nothing. "Draft a sub-agent definition for `.claude/agents/`" is a real negative — same repo, same
authoring verb, different artifact and a different skill (`craft-agent`) owns it.

Write queries the way users actually type: real paths, personal context ("my supervisor asked
me to…"), specific names, abbreviations, the occasional typo.

**Scoring** — model behaviour is nondeterministic, so run each query 3 times and compute a **trigger
rate**: the fraction of runs that loaded the skill. A should-trigger query passes above 0.5; a
should-not-trigger query passes below it.

**Split** — fix a ~60/40 **train/validation** split before iterating, with a proportional mix of
positive and negative labels in each half. Shuffle once, then keep the split fixed so iterations
compare against each other. Only train failures may guide a revision; validation results stay out of
the loop entirely.

**Loop** — evaluate on both sets; read the train failures; revise; repeat. Should-trigger failures
mean the description is too narrow (broaden the scope, add context on when the skill helps).
Should-not-trigger failures mean it is too broad (add specificity about what the skill does *not*
do, or name the boundary with the adjacent skill). Five iterations is usually enough; if nothing
improves, try a structurally different description rather than another tweak, and suspect the
queries before the description.

**Selection** — pick the iteration with the highest **validation** pass rate. That may not be the
last one you produced: a later iteration that scores better on train and worse on validation has
overfitted, and shipping it is the failure the split exists to catch.

---

## Anti-overfitting

**Never paste keywords from a failed query into the description.** That buys the one query and
generalizes nothing. Find the category the query represents and address *that*.

A failed query "help me tidy up this SKILL.md, it's gotten long" should not add the word "tidy".
The category is *revising an existing skill* — so the description covers reviewing and refactoring,
which also catches "prune", "trim", "clean up", and the phrasings nobody wrote down.

---

## Applying the result

1. Update `description` in the frontmatter.
2. Re-check the 1024-character limit — `python3 -m pytest .claude/hooks/tests/test_skill_spec_conformance.py -q`.
3. Sanity-check with 5–10 **fresh** queries that were never in either split. Queries used during
   optimization cannot tell you whether the description generalized.

**Not built here**: the eval runner (`eval_queries.json` + a bash loop over `claude -p`) is a
documented method, not a script in this repo. Running it for all 30 skills is its own task; running
it by hand for one skill you are actively revising is cheap and works today.
