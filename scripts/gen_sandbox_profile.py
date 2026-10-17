#!/usr/bin/env python3
"""Generate templates/subagent-sandbox.settings.json from .claude/sensitive-paths.txt (T147).

The profile a CLI-spawned sub-agent runs under (`claude --settings <profile>`). The
Supervisor's own `.claude/settings.json` is never touched.

    python3 scripts/gen_sandbox_profile.py           # rewrite the profile
    python3 scripts/gen_sandbox_profile.py --check   # exit 1 if the profile is stale

What the profile does, and why each piece is there:

* `defaultMode: dontAsk` — a spawned agent runs headless in a watch-only terminal, so
  nothing may ever wait on a human. Every call that would prompt is denied instead.
  That includes a T146 `ask`, so a sensitive path the guide did not predict is refused.
* `Edit(./**)` allow — writes inside the spawn's cwd (its worktree) run; anywhere else
  would prompt, so `dontAsk` denies it. Relative to the cwd on purpose: a `/path` rule
  would anchor at this file's own directory (`templates/`).
* One `Read(...)` and one `Edit(...)` deny per sensitive pattern, generated, never
  hand-copied. Patterns stay cwd-relative (gitignore depth rules); `{a,b}` is expanded
  because permission rules have no braces. A `!` negation cannot be expressed — an allow
  rule never carves an exception out of a deny — so the profile is stricter there
  (`.env.example` is denied too).
* `Edit(memory/**)` deny — memory is Supervisor-only (Memory Write Protocol).
* `WebFetch` / `WebSearch` denied as whole tools, plus an OS sandbox around Bash with
  no allowed domains, `strictAllowlist`, no unsandboxed retry and `failIfUnavailable`:
  no network, and no silent fallback to running unsandboxed.
* Bash allow rules for the test runners the role guides use, so a runner the sandbox
  does not auto-approve (e.g. `FOO=1 python3 -m pytest`) still runs without a prompt.
"""
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATTERNS_FILE = os.path.join(ROOT, ".claude", "sensitive-paths.txt")
PROFILE_FILE = os.path.join(ROOT, "templates", "subagent-sandbox.settings.json")
HOOK_FILE = os.path.join(ROOT, ".claude", "hooks", "pre_tool_sensitive_path.py")

TEST_RUNNER_ALLOW = [
    "Bash(python3 -m pytest *)",
    "Bash(python -m pytest *)",
    "Bash(pytest *)",
    "Bash(bash tests/*)",
    "Bash(sh tests/*)",
    "Bash(bash scripts/*)",
    "Bash(npm test *)",
    "Bash(npm run test *)",
]


def _expand_braces():
    """T146's brace expansion, so the hook and the profile read the list identically."""
    spec = importlib.util.spec_from_file_location("pre_tool_sensitive_path", HOOK_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.expand_braces


def sensitive_globs(text, expand_braces):
    """Every non-negated pattern in the list, brace-expanded and `/`-normalised."""
    globs = []
    for line in text.splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or raw.startswith("!"):
            continue
        body = raw.replace("\\", "/").lstrip("/")
        for glob in expand_braces(body):
            if glob not in globs:
                globs.append(glob)
    return globs


def build_profile(text, expand_braces):
    deny = []
    for glob in sensitive_globs(text, expand_braces):
        deny.append(f"Read({glob})")
        deny.append(f"Edit({glob})")
    deny += ["Edit(memory/**)", "WebFetch", "WebSearch"]
    return {
        "permissions": {
            "defaultMode": "dontAsk",
            "allow": ["Edit(./**)"] + TEST_RUNNER_ALLOW,
            "deny": deny,
        },
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": True,
            "autoAllowBashIfSandboxed": True,
            "allowUnsandboxedCommands": False,
            "network": {
                "allowedDomains": [],
                "strictAllowlist": True,
            },
        },
    }


def render(text, expand_braces):
    return json.dumps(build_profile(text, expand_braces), indent=2) + "\n"


def main(argv):
    with open(PATTERNS_FILE, encoding="utf-8") as f:
        rendered = render(f.read(), _expand_braces())
    if "--check" in argv:
        try:
            with open(PROFILE_FILE, encoding="utf-8") as f:
                current = f.read()
        except OSError:
            current = None
        if current != rendered:
            sys.stderr.write(
                "subagent-sandbox profile is stale — run: python3 scripts/gen_sandbox_profile.py\n"
            )
            return 1
        return 0
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        f.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
