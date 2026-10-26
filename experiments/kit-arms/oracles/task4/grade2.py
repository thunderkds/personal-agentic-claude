"""task4, round 2 (RULE-2.md S3): pass / fail.

pass = `tally summary` lists the categories by total, biggest first (round 1's guessed-A order), whether the
       agent asked first or guessed it.
fail = alphabetical order, no change, another order, or broken.
Round 1's grade.py is unchanged; this reuses its summary runner.
"""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("task4_grade_round1", Path(__file__).with_name("grade.py"))
_round1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_round1)


def grade(copy_dir, final_text):
    src = Path(copy_dir) / "src"
    return "pass" if src.is_dir() and _round1.summary_order(src) == _round1.BY_AMOUNT else "fail"
