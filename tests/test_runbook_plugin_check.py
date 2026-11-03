"""T241 — the RUNBOOK's post-deploy check also installs the plugin from GitHub.

Before T241 the check ran only `setup.sh`, so a release that broke the plugin install (T236's path)
passed the runbook unnoticed. The plugin check runs in a throwaway Claude config, so the operator's
own setup is never touched.

Run with: python3 -m pytest tests/test_runbook_plugin_check.py -q
"""
from pathlib import Path

RUNBOOK = Path(__file__).resolve().parents[1] / "RUNBOOK.md"


def deploy_steps():
    text = RUNBOOK.read_text(encoding="utf-8")
    start = text.index("**Post-deploy health check**")
    return text[start:text.index("## Rollback Procedure")]


def rollback_section():
    text = RUNBOOK.read_text(encoding="utf-8")
    start = text.index("## Rollback Procedure")
    return text[start:text.index("\n## ", start + 1)]


def test_post_deploy_check_installs_the_plugin_from_github():
    steps = deploy_steps()
    for command in ("claude plugin marketplace add thunderkds/easy-kit",
                    "claude plugin install easy-kit@easy-kit"):
        assert command in steps, f"post-deploy check lacks {command!r}"


def test_plugin_check_uses_a_throwaway_claude_config():
    steps = deploy_steps()
    plugin = steps[steps.index("**Plugin health check**"):]
    assert 'export CLAUDE_CONFIG_DIR="$P"' in plugin, "the plugin check must not install into the operator's config"
    assert 'rm -rf "$P"' in plugin


def test_plugin_check_states_its_pass_condition():
    steps = deploy_steps()
    plugin = steps[steps.index("**Plugin health check**"):]
    assert "Successfully installed plugin: easy-kit@easy-kit" in plugin


def test_a_failed_plugin_check_triggers_rollback():
    assert "plugin health check fails" in rollback_section()
