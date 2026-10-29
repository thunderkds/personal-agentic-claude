"""T198 - memory_sections.py prints only the Decisions and Learning Records entries of MEMORY.md."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "skills", "wake", "scripts", "memory_sections.py")


def run(cwd):
    r = subprocess.run([sys.executable, SCRIPT], cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0  # AC 7: never non-zero
    assert r.stderr == ""
    return r.stdout


def write_memory(tmp_path, text, newline="\n"):
    (tmp_path / "memory").mkdir(exist_ok=True)
    with open(tmp_path / "memory" / "MEMORY.md", "w", encoding="utf-8", newline="") as f:
        f.write(text.replace("\n", newline))


def entries(prefix, n):
    return "".join(f"- [{prefix}{i}](x.md) - line {i}\n" for i in range(1, n + 1))


def doc(decisions, lrs, tail="### Glossary\n- [G](g.md) - glossary\n"):
    return ("# MEMORY\n\n## Index\n\n### Decisions\n" + decisions + "### Patterns & Gotchas\n"
            "- [P](p.md) - pattern\n### Learning Records\n<!-- comment -->\n" + lrs + "\n" + tail)


def test_few_entries_all_printed_and_nothing_else(tmp_path):
    write_memory(tmp_path, doc(entries("D", 3), entries("L", 2)))
    out = run(tmp_path).splitlines()
    assert out == [f"- [D{i}](x.md) - line {i}" for i in (1, 2, 3)] + \
                  [f"- [L{i}](x.md) - line {i}" for i in (1, 2)]


def test_exactly_twenty_prints_all(tmp_path):
    write_memory(tmp_path, doc(entries("D", 12), entries("L", 8)))
    assert len(run(tmp_path).splitlines()) == 20


def test_over_twenty_prints_first_five_of_each(tmp_path):
    write_memory(tmp_path, doc(entries("D", 30), entries("L", 9)))
    out = run(tmp_path).splitlines()
    assert [l.split("]")[0] for l in out] == \
        [f"- [D{i}" for i in range(1, 6)] + [f"- [L{i}" for i in range(1, 6)]


def test_missing_memory_file(tmp_path):
    assert run(tmp_path) == "No MEMORY.md found.\n"


def test_neither_section_prints_index_block(tmp_path):
    write_memory(tmp_path, "# M\n\n## Index\n\n### Glossary\n- [G](g.md) - one\n\n## Other\n- [O](o.md) - no\n")
    out = run(tmp_path)
    assert "### Glossary" in out and "- [G](g.md) - one" in out
    assert "Other" not in out and "[O]" not in out


def test_neither_section_and_no_index_prints_nothing(tmp_path):
    write_memory(tmp_path, "# M\n\n## Other\n- [O](o.md) - no\n")
    assert run(tmp_path) == ""


def test_only_one_section_present(tmp_path):
    write_memory(tmp_path, "# M\n## Index\n### Learning Records\n- [L1](l.md) - one\n")
    assert run(tmp_path).splitlines() == ["- [L1](l.md) - one"]


def test_windows_line_endings_and_trailing_space_heading(tmp_path):
    text = "# M\n## Index\n### Decisions  \n- [D1](x.md) - one\n### Learning Records \t\n- [L1](x.md) - two\n"
    write_memory(tmp_path, text, newline="\r\n")
    out = run(tmp_path)
    assert "\r" not in out
    assert out.splitlines() == ["- [D1](x.md) - one", "- [L1](x.md) - two"]


def test_wrapped_continuation_line_is_ignored(tmp_path):
    write_memory(tmp_path, "## Index\n### Decisions\n- [D1](x.md) - one\n  wrapped text\nplain text\n- [D2](x.md) - two\n")
    assert run(tmp_path).splitlines() == ["- [D1](x.md) - one", "- [D2](x.md) - two"]


def test_script_writes_nothing(tmp_path):
    write_memory(tmp_path, doc(entries("D", 3), entries("L", 2)))
    before = sorted(str(p) for p in tmp_path.rglob("*"))
    mtime = (tmp_path / "memory" / "MEMORY.md").stat().st_mtime_ns
    run(tmp_path)
    assert sorted(str(p) for p in tmp_path.rglob("*")) == before
    assert (tmp_path / "memory" / "MEMORY.md").stat().st_mtime_ns == mtime


def test_real_memory_file_is_small():
    out = run(ROOT)
    assert len(out) < 4000
    assert len(out.splitlines()) == 10
