---
name: companion-setup
description: "Stage 1 step: show the user the optional companion MCP servers (easy-verifier, easy-ui, easy-memory, easy-personal): which are already installed, what each adds, what it needs and which tools are missing. The user can pick any or skip; skip is the default and changes nothing. The kit never installs, starts or runs anything: a pick only shows the install link and the missing tools. In [auto] mode it asks nothing and puts one line under Not done:. Invoke at Stage 1 checklist item 1, or via /companion-setup."
---

## Role: Companion Setup

You are the Supervisor. You show the user which companion MCP servers exist. You use the data in
`companions.json` and the read-only script `scripts/check_companions.py`. The normal flow runs
without any of them.

### Rules

- The kit never installs a server. Never run `docker`, `uv`, `npm`, `pip` or `claude mcp add`
  for the user. Never start a server.
- The easy-verifier install also uses `sudo`. The user runs it, never the kit.
- Skip is the default. A skip, or no answer, changes nothing and is not an error.
- Show a link only for a server the script marks `choice:`. Never show a repository link for a
  private server, and never guess one.
- Needs only `python3`. The script makes no network call and writes no file. Run it from the
  project root.

### Step 1 — Detect

List the companion servers you can see in this session (for example MCP tools named
`mcp__easy-memory__...`). Pass their ids, comma separated. If you are not sure, pass none.

```
python3 ${CLAUDE_SKILL_DIR}/scripts/check_companions.py --installed <ids>
```

### Step 2 — Show the offer

Show the script output as it is. It has one line per server:

- `choice:` — a public server you can install. It says what the server adds, what it needs and
  which tools are missing on this machine.
- `already installed:` — nothing to do.
- `needs repo access:` — a private server. It is not a choice. Say that the user needs access to
  its repository to install it.

Ask: "Do you want any of these? Pick by name, or skip." Skip is the default.

### Step 3 — On a pick

Show only two things: the install link from the `choice:` line, and the tools it names as missing.
The user installs it. Do not run any install step, and do not check the result for the user.

If the pick is easy-verifier, warn: its server listens on `127.0.0.1:8766` with no authentication,
so any process on this machine can call it. The user decides whether to run it.

### Auto mode (`[auto]`)

Ask no question. Run Step 1 only. Change nothing. In the final report, under `Not done:`, put one
line: `companion-setup: nothing installed, offer not asked — yours to choose (/companion-setup)`.

### Done when

- The user picked and you showed the link and the missing tools, or
- The user skipped, or gave no answer, and you changed nothing, or
- In auto mode, the `Not done:` line is in the final report.
