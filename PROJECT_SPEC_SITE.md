# PROJECT_SPEC — Kit Landing Site (v1)

**Scope boundary:** this document governs the public static site only. It is a separate scope from
the harness itself (Hard-Stop Gate 4: different deployment target — Vercel). Harness work stays on
`PROJECT_KANBAN.md` / `PROJECT_SPEC.md`; site work stays on `PROJECT_KANBAN_SITE.md` / this file.

---

## Purpose

A single public page that answers, for someone who has never seen this repo:

1. **What is this?** — a multi-agent supervisor framework for Claude Code that enforces a 5-stage
   pipeline with deterministic hooks, installed into any git repo with one command.
2. **What do I get?** — the agent roster, the skill roster, the enforcement hooks.
3. **How do I install it?** — the copy-pasteable install and update commands.

It is a **reference surface, not a project surface.** It never shows task boards, KANBAN rows,
task IDs, memory contents, or in-flight work. That is an explicit product decision from the user
("I don't want to sync the KANBAN"), not an omission to be corrected later.

## Audience

Developers evaluating the kit from a GitHub link. Assume they know git and Claude Code exists;
assume they know nothing about this repo's pipeline, agents, or vocabulary.

## Non-goals (v1)

- No search, no client-side routing, no framework, no build step, no package.json.
- No per-skill detail pages — one line per skill on one page.
- No analytics, no cookies, no forms, no external asset hosts. **One exception (2026-10-27, user-requested): the Settings tool** — see "Settings tool" below.
- No CI workflow in this repo deploys the site. Deploy is Vercel's Git integration: a push to `main` deploys production. The CLI steps in `RUNBOOK.md` are the manual/rollback route.

## Stack decision

Plain HTML + CSS, no build. Rationale: the repo has **no node toolchain today** and the content is
one page of lists; a docs framework would add a dependency tree and a build step to serve static
text. Vercel serves the output directory as-is.

## The drift constraint (the load-bearing one)

A hand-maintained page listing 30 skills, 5 agents, and 8 hooks goes stale the first time any of
those change. This repo has already been bitten by exactly that failure: `README.md` has documented
two hook facts wrongly since T044/T056 (tracked as T081) and nobody noticed for months.

Therefore the site's roster content is **asserted against the source of truth by an automated test**
(`tests/test_site_content.py`), which is the task's Gate 5 test:

| Site content | Source of truth |
|---|---|
| Agent list | `name:` frontmatter in `.claude/agents/*.md` (every file is a spawnable role; the base template lives in `templates/`) |
| Skill list | directory names under `.claude/skills/` |
| Hook list | `.claude/settings.json` `hooks` wiring |
| Step-limit default | `STEP_LIMIT` literal in `.claude/hooks/pre_agent_step_limit.py` |
| Settings tool catalog | inline `#settings-catalog` JSON, version-stamped against the official settings reference (see "Settings tool") |

Adding a skill without updating the page must fail the suite. A page that merely *looks* right is
not accepted.

## Settings tool (T185, T187)

User request 2026-10-27: "design a section that user can click on the settings and we can generate the settings for users, by the way support they paste their current settings and we check the settings following, it will looks like the support for the pick/format/visualize the settings". Context: the kit does **not** install settings defaults ("the config should go by the taste" — T184 closed); the site helps each developer build their own.

One section, `#settings-tool`, two modes:

- **Build** (T185) — pick settings from a catalog, set values, choose the target file (user / project / local), copy the generated JSON.
- **Check** (T187) — paste an existing `settings.json`, get it formatted, validated against the catalog and the chosen target file, and shown as a grouped visual tree; load it into Build to edit.

Hard rules for the tool:

1. **Pasted text never leaves the browser.** No `fetch`/XHR/beacon, no `localStorage`/`sessionStorage`/IndexedDB/cookies of pasted or generated content. Asserted by test.
2. **No forms that submit.** Inputs are page UI only (`<form>` absent, or `submit` handled with `preventDefault`).
3. **Inline only.** Script and the settings catalog are inline in `site/index.html` (catalog in `<script type="application/json" id="settings-catalog">`); the existing no-external-assets and inline-script tests stay green.
4. **No build, no package.json.** Logic tests use Node's built-in test runner (`node --test`), zero dependencies — the one exception to "no node toolchain".
5. **The page works without the tool.** With script disabled, the section shows a short static explanation and a link to the official settings reference.

Source of truth: the settings catalog is hand-curated from https://code.claude.com/docs/en/settings-reference and stamped with the CLI version it was checked against (first stamp: 2.1.311). The drift test checks the catalog's shape and stamp; content currency is re-checked by hand when the stamp is bumped.

## Glossary (site-facing terms)

- **Supervisor** — the orchestrating Claude session; single source of truth for the lifecycle.
- **Sub-agent** — an isolated Claude process spawned for exactly one TASK_GUIDE.
- **Skill** — an inline instruction set loaded into the current conversation.
- **Hook** — a deterministic shell/python guardrail the harness runs, not the model.
- **Pack** — an optional domain extension adding agents + skills on top of the core four.
