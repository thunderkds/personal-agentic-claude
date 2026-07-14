# TASK_GUIDE — T005: CLI Wiring — Typer Entrypoint
**Date**: 2026-06-11
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P0
**Assigned agent**: Backend-Implementer
**Agent guide**: `.claude/agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/backend.md`
5. Apply C1 process from the Complexity matrix in `.claude/agents/general-agent-template.md`

**Depends on**: T002, T003, T004 (all core modules must exist before wiring)

---

## Requirement (Pillar 1 — Adapt the requirement)

Wire all CLI commands in `src/supervisor_viz/cli.py` using Typer so that the `supervisor-viz` entry point is fully functional. Each command must call the correct underlying module with the correct arguments and configuration loaded from `~/.config/supervisor-viz/config.toml` (with defaults if the file is absent).

**Commands to implement:**
- `supervisor-viz live` — start `SupervisorVizApp` in live mode watching the configured log directory
- `supervisor-viz trace <file>` — start `SupervisorVizApp` in trace mode with the given JSONL file
- `supervisor-viz export <session> --format mermaid` — call `mermaid.py` (stub OK if T006 not done)
- `supervisor-viz status` — list `.jsonl` files in the log directory with their last-modified times
- `supervisor-viz config` — print the active configuration (resolved defaults + overrides)

**Restated intent**: A developer runs `supervisor-viz live` and the TUI starts immediately; `supervisor-viz trace ~/path/to/session.jsonl` replays that file. All commands are discoverable via `--help`.

**Out of scope**:
- Mermaid export implementation (T006 — stub call is fine)
- Config file editing (just read and print)
- Authentication or network

**Requirement Refs**:
- FR-001: `live` command tails log directory
- FR-005: `trace` command loads JSONL file
- FR-006: `export` command (stub call)
- FR-007: `status` command lists active sessions
- FR-008: Single `supervisor-viz` CLI entry point via Typer
- FR-009: Read config from `~/.config/supervisor-viz/config.toml` with defaults
- NFR-004: Graceful degradation when no session found
- NFR-005: Type-hinted, mypy --strict passes

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request
- [x] Domain terms align with `PROJECT_SPEC.md` glossary
- [x] Every Acceptance Criterion below traces to a line in the Requirement
- [x] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `supervisor-viz --help` lists all 5 subcommands | FR-008 |
| 2 | `supervisor-viz live --help` shows `--log-dir` option with default | FR-001, FR-009 |
| 3 | `supervisor-viz trace <nonexistent-file>` prints a clear error and exits non-zero | NFR-004 |
| 4 | `supervisor-viz status` with no JSONL files in log dir prints "No active sessions found." and exits 0 | FR-007, NFR-004 |
| 5 | `supervisor-viz config` prints the resolved config as TOML or JSON without error | FR-009 |
| 6 | `supervisor-viz live` calls `SupervisorVizApp` in live mode (integration — testable via mock) | FR-001 |
| 7 | `mypy --strict src/supervisor_viz/cli.py src/supervisor_viz/utils/config.py` exits 0 | NFR-005 |

---

## Evaluation & Acceptance

### Success Criteria

| # | Given | Expect | How it's checked |
|---|-------|--------|-----------------|
| 1 | `supervisor-viz --help` | Lists live, trace, export, status, config | CLI invocation |
| 2 | `supervisor-viz trace /nonexistent.jsonl` | Error message + exit 1 | CLI invocation |
| 3 | `supervisor-viz status` on empty dir | "No active sessions found." + exit 0 | CLI invocation |

### Verification Command

```bash
supervisor-viz --help && \
supervisor-viz status && \
supervisor-viz config && \
mypy --strict src/supervisor_viz/cli.py src/supervisor_viz/utils/config.py
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| Verification command run | ☐ pass / ☐ fail | |
| Negative cases hold | ☐ pass / ☐ fail | |
| `verify` skill — works in running app | ☐ pass / ☐ fail | |
| Review scope bounded to cli.py + config.py | ☐ pass / ☐ fail | |
| Full smoke suite still green | ☐ pass / ☐ fail | |

---

## Approach

1. Implement `src/supervisor_viz/utils/config.py`:
   - `AppConfig` dataclass with defaults: `log_dir = Path("~/.claude/logs").expanduser()`, `hitl_patterns = ["AskUserQuestion"]`
   - `load_config() -> AppConfig`: reads `~/.config/supervisor-viz/config.toml` if it exists; merges with defaults; returns `AppConfig`

2. Wire `cli.py`:
   - `app = typer.Typer(name="supervisor-viz", help="...")`
   - `@app.command()` for each of `live`, `trace`, `export`, `status`, `config`
   - `live`: load config → call `SupervisorVizApp(mode="live", log_dir=...).run()`
   - `trace`: validate file exists → call `SupervisorVizApp(mode="trace", file=...).run()`
   - `export`: load sessions → call `mermaid.export(...)` (stub OK)
   - `status`: list `*.jsonl` files in log_dir → print table or "No active sessions found."
   - `config`: print `load_config()` as formatted output

3. Use `typer.Exit(code=1)` for error exits. Never `sys.exit()` directly.

---

## Edge Case Checklist

- [ ] Config file missing: fall back to all defaults silently (not an error)
- [ ] Config file malformed (invalid TOML): print clear error + fall back to defaults
- [ ] `trace` given a file path that is not a `.jsonl` file: warn but proceed (user might rename files)
- [ ] `live` log directory does not exist: pass to TUI which handles it gracefully (NFR-004)
- [ ] `status` log directory does not exist: print "Log directory not found: <path>" + exit 0

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `src/supervisor_viz/cli.py` | Implement all 5 commands fully |
| `src/supervisor_viz/utils/config.py` | Implement `AppConfig` + `load_config()` |
| `tests/test_cli.py` | Create — CLI invocation tests (via `typer.testing.CliRunner`) |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `src/supervisor_viz/viz/textual_ui.py` | T004's domain |
| `src/supervisor_viz/core/` | Core modules are owned by T002/T003 |

---

## Test Plan

- Unit: `tests/test_cli.py` using `typer.testing.CliRunner` — all 7 ACs
- Manual: invoke each command from the terminal

---

## Completion Checklist

- [ ] Implementation done
- [ ] `pytest tests/test_cli.py -v` all pass
- [ ] `mypy --strict src/supervisor_viz/cli.py src/supervisor_viz/utils/config.py` exits 0
- [ ] All 5 commands work from the terminal
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Supervisor notified: T005 ready for Stage 4 review
