# Folder Structure Requirements (Mandatory)

> Extracted from `CLAUDE.md` — full detail for the mandatory root-level folder structure. See `CLAUDE.md` for the pointer back to this file.

The project root **must** contain these folders:

1. `agents/` folder containing:
   - agents/general-agent-template.md
   - agents/common-infrastructure.md
   - agents/backend.md
   - agents/frontend.md
   - agents/qa.md

2. `skills/` folder containing custom project skills (Claude Code discovers them through the `.claude/skills` symlink — see *Canon and the `.claude/` symlinks* below):
   - skills/brainstorming/SKILL.md
   - *(pack skills are symlinked here when a pack is installed)*

3. `tasks/` folder
   Contains one TASK_GUIDE_Txxx.md file for **every** task after Stage 2 is approved.

4. `templates/` folder containing:
   - templates/PRD_template.md
   - templates/PROJECT_SPEC_template.md
   - templates/PROJECT_KANBAN_template.md
   - templates/TASK_GUIDE_template.md
   - templates/BRAINSTORMING_LOG_template.md
   - templates/SKILL_template.md
   - templates/ADR_template.md
   - templates/DDR_template.md
   - templates/RUNBOOK_template.md
   - templates/report_template.html
   - templates/thinking_report_template.html
   - templates/PACK_template.md

5. `packs/` folder (in the central clone) containing optional domain packs:
   - packs/mobile/ — Flutter, React Native, Swift, Kotlin
   - packs/data/ — Pipelines, notebooks, ETL, dbt
   - packs/devops/ — Terraform, K8s, CI/CD
   - packs/ai-agent/ — LLM apps, RAG, MCP servers
   - packs/api/ — REST/gRPC, OpenAPI, auth flows
   *(Each pack contains agents/ + skills/ + PACK.md. Installed via `setup.sh --pack=<name>`.)*

6. `memory/` folder containing:
   - memory/MEMORY.md (hot-tier index — ≤50,000 characters, referenced by path in every sub-agent spawn prompt and read by the agent)
   - memory/decisions.md (cold tier — architectural/infra decisions)
   - memory/glossary.md (cold tier — domain terms & domain models)
   - memory/learnings.md (cold tier — requirement clarifications, patterns, gotchas)

---

## Canon and the `.claude/` symlinks

`skills/` and `agents/` are the **canon**: the real directories, tracked in git, sitting at plain
root so that no harness is structurally privileged over another.

Claude Code only discovers skills and agent guides beneath `.claude/`. Two committed symlinks
bridge that gap:

```
.claude/skills -> ../skills
.claude/agents -> ../agents
```

Three properties matter, and each is enforced by a test:

1. **They are symlinks, not copies.** A copy would satisfy every path lookup while drifting out of
   sync with the canon from the moment it was made.
2. **Their targets are relative.** Every sub-agent works inside a `git worktree`. An absolute
   target either does not exist in that worktree or points back at the main checkout, letting an
   agent read canon from outside its isolation boundary.
3. **They are committed.** Git stores symlinks natively, so a fresh `git clone` and a
   `git worktree add` both reproduce them without any setup step.

They are load-bearing. Deleting `.claude/skills` because `skills/` "already has everything" stops
this repo from running its own skills. `scripts/validate.sh` and
`.claude/hooks/tests/test_canon_symlinks.py` fail loudly if either link goes missing, becomes a
real directory, or acquires an absolute target.

Downstream installs get the same shape, but only for projects that actually use Claude Code.
`setup.sh` copies the canon to plain root from `MANIFEST` and then re-creates both links via
`harness_install_canon_symlinks` in `lib/harness-fetch.sh` — unless Claude Code was not picked in the
installer's CLI menu, in which case it says so and skips them.

Update and Reinstall call the same function, gated on the rule every harness shares (T098): install
for `claude` when it was **picked this run** (Reinstall, Claude Code in the CLI menu) or is **already
present** (Update picks nothing: it keeps what is there). Presence is checked at the two link
destinations rather than at a `MANIFEST` destination column, because `claude` alone ships as symlinks rather than as a projected copy — and it tests
`-e` *or* `-L`, since `-e` follows a symlink and would read a broken link as absent instead of as
something to repair.

The practical consequences:

- An existing Claude install whose link is missing, stale, absolute, or a leftover real directory is
  still repaired on every Update, so an upgrade from a pre-relocation install cannot leave Claude
  Code reading a stale `.claude/skills`.
- A Codex-only project no longer acquires `.claude/{skills,agents}` it never asked for the next time
  someone runs Update.
- If **both** links are deleted outright, Update leaves them absent — fully-absent is
  indistinguishable from "never had claude". Restore them with Reinstall, picking Claude Code, which
  installs on explicit request regardless of presence.

A real directory found at either path is moved aside to `<link>.bak`; if that fails, the installer
exits non-zero rather than reporting success over content Claude Code cannot see.
