# Main flow — Easy Kit

How a request moves through the kit, from install to a pushed merge. Each box names the file that
does the work. Detail: `AGENTS.md`, `docs/claude-md/tracks.md`, `docs/claude-md/pipeline-stages.md`.

```mermaid
flowchart TD
    I["setup.sh — install / update<br/>copies MANIFEST paths, merges .claude/settings.json"] --> W
    W["Session start: wake skill<br/>git log, board, memory briefing"] --> R["User request"]
    R --> T{"Track rule<br/>docs/claude-md/tracks.md"}
    T -- "minimal: C0–C1, Risk Low, no UI" --> M["Supervisor codes on a task branch<br/>test first, Decision record in tasks/MINIMAL_LOG.md"]
    T -- "extended" --> P0["Phase 0 → Stage 0.5 → Stage 1<br/>requirements, direction, codebase map, tech stack"]
    P0 --> RD["PROJECT_SPEC.md ## Readiness<br/>filled; Approved by the user"]
    RD --> S2["Stage 2: PROJECT_SPEC.md, PROJECT_KANBAN.md,<br/>tasks/TASK_GUIDE_Txxx.md"]
    S2 --> SP["Stage 3: craft-spawn-prompt → Agent spawn"]
    SP --> H1{"pre_agent_validate_guide.py"}
    H1 -- "no or incomplete guide" --> X["spawn blocked"]
    H1 -- "readiness incomplete" --> WARN["⚠ HIGH RISK warning<br/>spawn goes ahead"]
    H1 -- "ok" --> AG
    WARN --> AG["Sub-agent in its own worktree<br/>post_tool_trace.py records calls; pre_agent_step_limit.py caps them"]
    AG --> S4["Stage 4: code-review, security-review (Risk Medium/High)<br/>Evidence in tasks/TASK_REVIEW_Txxx.md"]
    M --> RR
    S4 --> RR["Ready for Review"]
    RR --> V["stop_auto_verify.py --start ID<br/>headless /verify writes the verify row"]
    V --> U{"User approves merge?"}
    U -- "yes" --> G{"pre_bash_block_unsafe_merge.py<br/>merge gate: verify pass, no task In Progress"}
    G -- "pass" --> MG["git merge → post_bash_memory_update.py<br/>memory pass, row to Done"]
    MG --> PU["git push (user's approval)"]
```
