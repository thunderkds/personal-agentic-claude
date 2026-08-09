#!/usr/bin/env python3
"""T066 — measure per-role loaded size of the agent guides.

Per-role load = the role guide (auto-loaded as the system prompt) + `general-agent-template.md`
(read via the role guide's startup step). Sizes are reported in **characters** (what the file
actually costs on disk) and a `chars / 4` token estimate, labelled as an estimate — no tokenizer
is available in this environment and the guide's own table is itself an estimate.

Usage:
    python3 scripts/measure_agent_guide_tokens.py            # working tree
    python3 scripts/measure_agent_guide_tokens.py <git-ref>   # e.g. HEAD
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ".claude/agents/general-agent-template.md"
ROLES = {
    "c-infra": ".claude/agents/common-infrastructure.md",
    "backend": ".claude/agents/backend.md",
    "frontend": ".claude/agents/frontend.md",
    "qa": ".claude/agents/qa.md",
}


def read(rel: str, ref: str | None) -> str:
    if ref is None:
        return (ROOT / rel).read_text(encoding="utf-8")
    return subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{ref}:{rel}"],
        check=True, capture_output=True, text=True,
    ).stdout


def main() -> int:
    ref = sys.argv[1] if len(sys.argv) > 1 else None
    label = ref or "working tree"
    tmpl = len(read(TEMPLATE, ref))
    print(f"# per-role loaded size — {label}")
    print(f"template `{TEMPLATE}`: {tmpl:,} chars (~{tmpl // 4:,} tok est.)\n")
    print("| role | role guide chars | template chars | total chars | total tok (est.) |")
    print("|---|---|---|---|---|")
    for role, rel in ROLES.items():
        n = len(read(rel, ref))
        total = n + tmpl
        print(f"| {role} | {n:,} | {tmpl:,} | {total:,} | {total // 4:,} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
