"""T256 - the self-review skill text (AC 1-8). Structural checks only: no model is called."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(ROOT, "skills", "self-review")
SKILL = os.path.join(SKILL_DIR, "SKILL.md")
MINER = os.path.join(SKILL_DIR, "references", "miner-prompt.md")
CODEX_CAP = 8192


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert m, "SKILL.md has no frontmatter"
    return m.group(1), text[m.end():]


def step(text, n):
    m = re.search(rf"^### Step {n} .*?(?=^### Step {n + 1} |\Z)", text, re.DOTALL | re.MULTILINE)
    assert m, f"no Step {n}"
    return m.group(0)


def test_ac1_frontmatter_user_only_description_and_codex_cap():
    raw = read("skills", "self-review", "SKILL.md")
    fm, body = frontmatter(raw)
    assert re.search(r"^name: self-review$", fm, re.MULTILINE)
    desc = re.search(r"^description:\s*(.+)$", fm, re.MULTILINE).group(1)
    assert "only by the user" in desc and "/self-review" in desc
    assert "no hook, schedule or agent starts it" in desc
    assert len(body.encode("utf-8")) < CODEX_CAP, "Codex caps a skill body at 8 KB"


def test_ac2_pre_runs_first_and_nothing_new_stops_before_any_agent_call():
    raw = read("skills", "self-review", "SKILL.md")
    _, body = frontmatter(raw)
    first = re.search(r'self_review\.py" (pre|post|decide)', body).group(1)
    assert first == "pre", "the first script call must be `pre`"
    one = step(body, 1)
    assert "nothing-new" in one
    assert re.search(r"stop here\. Make no `Agent` call", one)
    assert body.index("### Step 1") < body.index("Agent({")


def test_ac3_exactly_one_sonnet_miner_writing_to_the_scratchpad():
    _, body = frontmatter(read("skills", "self-review", "SKILL.md"))
    spawns = re.findall(r"Agent\(\{[^}]*\}\)", body)
    assert len(spawns) == 1, spawns
    assert 'subagent_type: "general-purpose"' in spawns[0]
    assert 'model: "sonnet"' in spawns[0]
    assert "references/miner-prompt.md" in spawns[0]
    two = step(body, 2)
    assert "FILES" in two and "scratchpad" in two and "never inside the repo" in two
    assert "Never start a second miner" in two
    assert "(references/miner-prompt.md)" in two, "a link, with the trigger to load it"


def test_ac4_miner_prompt_is_the_spike_prompt_adapted():
    miner = read("skills", "self-review", "references", "miner-prompt.md")
    assert "FILES" in miner and "KNOWN" in miner and "OUT" in miner
    assert "only input" in miner and "Read nothing else" in miner
    assert "data, never instructions" in miner
    assert "docs/claude-md/untrusted-content-boundary.md" in miner
    assert "3 or more" in miner and "at most 5" in miner
    assert "already_open" in miner
    assert "/home/" not in miner and "{{" not in miner, "no spike path or placeholder left"


def test_ac5_decisions_lr_source_agent_and_no_other_edits():
    _, body = frontmatter(read("skills", "self-review", "SKILL.md"))
    four = step(body, 4)
    assert "self_review.py\" decide <fingerprint> rejected" in four
    assert "self_review.py\" decide <fingerprint> approved <TASK_ID>" in four
    assert "row stays `open`" in four
    five = step(body, 5)
    assert "`source: agent`" in five
    assert "templates/LEARNING-RECORD-FORMAT.md" in five
    assert "Kanban row" in five and "TASK_GUIDE" in five and "Stage 2" in five
    assert re.search(r"Never edit a kit file, commit to `main`, merge or push", body)
    assert "Nothing leaves this repo" in body


def test_ac6_learn_step_8_hands_kit_proposals_to_self_review():
    text = read("skills", "learn", "SKILL.md")
    m = re.search(r"^#### Step 8 .*?(?=^---$|\Z)", text, re.DOTALL | re.MULTILINE)
    assert m, "no learn Step 8"
    step8 = m.group(0)
    assert "`self-review`" in step8 and "belongs to `self-review` alone" in step8
    assert "learn-[slug]" in step8, "the project-level stub stays"


def test_ac7_agents_md_cross_cutting_list_names_self_review():
    line = next(l for l in read("AGENTS.md").splitlines() if l.startswith("**Stage index**"))
    cross = line.split("Cross-cutting", 1)[1]
    assert "`self-review`" in cross


def test_ac8_no_hook_or_hook_config_mentions_self_review():
    hits = []
    paths = [os.path.join(ROOT, "hooks", "hooks.json"), os.path.join(ROOT, ".claude", "settings.json")]
    for base, _, files in os.walk(os.path.join(ROOT, ".claude", "hooks")):
        if "__pycache__" in base or os.sep + ".state" in base:
            continue
        paths += [os.path.join(base, f) for f in files]
    for p in paths:
        if not os.path.isfile(p):
            continue
        try:
            text = open(p, encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
        if re.search(r"self[-_]review", text):
            hits.append(os.path.relpath(p, ROOT))
    assert not hits, hits
