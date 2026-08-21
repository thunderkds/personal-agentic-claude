"""
T084 — vercel.json deploy config test.

AC1: vercel.json exists, is valid JSON, declares `site` as the output
directory, and carries no build command.
AC2: no framework preset / install command / node version keys — this is a
static-file deploy only.
AC6: the named output directory must actually exist on disk and contain
index.html — a config pointing at nothing must fail this suite.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERCEL_JSON = os.path.join(ROOT, "vercel.json")


def _load_config():
    with open(VERCEL_JSON, encoding="utf-8") as f:
        return json.load(f)


def test_vercel_json_exists_and_parses():
    assert os.path.isfile(VERCEL_JSON), "vercel.json must exist at the repo root"
    config = _load_config()
    assert isinstance(config, dict)


def test_output_directory_is_site():
    config = _load_config()
    assert config.get("outputDirectory") == "site", (
        "vercel.json must declare `site` as the output directory"
    )


def test_output_directory_exists_and_contains_index_html():
    config = _load_config()
    output_dir = config.get("outputDirectory")
    assert output_dir, "vercel.json has no outputDirectory to check"
    abs_dir = os.path.join(ROOT, output_dir)
    assert os.path.isdir(abs_dir), (
        f"outputDirectory '{output_dir}' named in vercel.json does not exist on disk"
    )
    assert os.path.isfile(os.path.join(abs_dir, "index.html")), (
        f"'{output_dir}' does not contain index.html"
    )


def test_no_build_command():
    config = _load_config()
    assert "buildCommand" not in config, "static site must not declare a build command"


def test_no_framework_install_or_node_version_keys():
    config = _load_config()
    for key in ("framework", "installCommand", "nodeVersion", "devCommand"):
        assert key not in config, f"static-file deploy must not set '{key}'"


VERCELIGNORE = os.path.join(ROOT, ".vercelignore")


def test_vercelignore_is_an_allowlist():
    """`outputDirectory` scopes what Vercel *serves*, not what the CLI *uploads* —
    the source tree is transmitted to Vercel's build infrastructure on every
    deploy. A denylist fails open the first time someone adds a directory, so
    require the deny-everything-then-admit form."""
    assert os.path.exists(VERCELIGNORE), (
        ".vercelignore missing — without it the whole repo source, including "
        "memory/ and tasks/, is uploaded to Vercel on every deploy"
    )
    with open(VERCELIGNORE, encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    assert lines and lines[0] == "*", (
        f".vercelignore must start with a bare `*` (deny all) before its "
        f"negations; first rule is {lines[0]!r}"
    )
    assert "!site/" in lines or "!site/**" in lines, (
        ".vercelignore denies everything but never re-admits site/ — the deploy "
        "would upload nothing"
    )


def test_sensitive_dirs_not_admitted_by_vercelignore():
    """memory/ and tasks/ must never appear as a negation."""
    with open(VERCELIGNORE, encoding="utf-8") as f:
        text = f.read()
    for leaked in ("!memory", "!tasks", "!docs", "!PROJECT_KANBAN"):
        assert leaked not in text, (
            f".vercelignore re-admits {leaked[1:]!r} — that path would be "
            f"uploaded to Vercel on every deploy"
        )
