#!/usr/bin/env python3
"""T058 — `diagnose` Phase 4 is an evidence-driven instrumentation loop, not a preference sentence.

Before this task, `.claude/skills/diagnose/SKILL.md`'s `### Phase 4 — Instrument` was a single
line ranking instrument types by preference (`debugger/REPL > targeted boundary logs > ...`,
`Tag logs [DEBUG-xxxx]`). It never said what to log, in what format, how many probes, how a probe
ties back to a Phase 3 hypothesis, or when instrumentation may be removed.

These tests assert the shipped skill file structurally, following
`test_bugfix_evidence_parity.py`'s shape (extract a section by heading, then assert on the
*extracted block* — never file-wide, since a file-wide substring passes on a mere prose mention
elsewhere in the document).

  SC1  — Phase 4 extracts with >= 5 enumerated steps
  SC2  — Phase 4 carries NDJSON + payload fields, hypothesisId, the five placement categories,
         the 1/10 budget bounds, `#region debug log`, and a secrets/PII prohibition
  SC3  — Stuck-Loop Checkpoint carries CONFIRMED / REJECTED / INCONCLUSIVE and the
         INCONCLUSIVE-does-not-increment rule
  SC4  — Phase 5 retains instrumentation until post-fix verification, and reverts REJECTED changes
  SC5  — Phase 6 cleanup is marker-driven, then re-grep, then `git diff` review
  SC6  — line 8 byte-identical (negative: the dropped Complexity-gating direction did not re-enter)
  SC7  — the ordered `### Phase` heading list is unchanged (negative: scope lock)
  SC8  — Phase 1/2/3 bodies byte-identical to their pre-change form (negative: out of scope)

Run with: python3 -m pytest .claude/hooks/tests/test_diagnose_evidence_loop.py -v
"""
import hashlib
import os
import re

HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_PATH = os.path.join(
    os.path.dirname(HOOKS_DIR), "skills", "diagnose", "SKILL.md"
)


def read_skill():
    with open(SKILL_PATH) as f:
        return f.read()


def extract_section(text, heading_prefix):
    """Return the body of the `### <heading_prefix>...` section, exclusive of its heading.

    The terminator is anchored with `^###` under re.MULTILINE. This repo has six recorded
    defects in the unanchored-terminator family (T018/T022/T024/T042/T045 and the Kanban
    `###`-in-a-row case) — an unanchored `###` truncates the block at any inline occurrence.
    """
    pattern = re.compile(
        r"^### " + re.escape(heading_prefix) + r"[^\n]*\n(.*?)(?=^### |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    assert match is not None, f"section '### {heading_prefix}' not found in {SKILL_PATH}"
    body = match.group(1)
    # Guard against the vacuous-extraction failure mode (T039): an empty block compares
    # equal to an empty expectation and asserts nothing.
    assert body.strip(), f"section '### {heading_prefix}' extracted empty"
    return body


def phase4():
    return extract_section(read_skill(), "Phase 4 — Instrument")


def checkpoint():
    return extract_section(read_skill(), "Stuck-Loop Checkpoint")


# ---------------------------------------------------------------------------
# Pre-change fixtures (captured from c0b925f, before any implementation commit)
# ---------------------------------------------------------------------------

LINE_8_PRE_CHANGE = (
    "A discipline for hard bugs. Skip phases only when explicitly justified. When exploring, "
    "use the project's domain vocabulary to build a clear mental model and check ADRs in the "
    "area you touch."
)

PHASE_HEADINGS_PRE_CHANGE = [
    "### Phase 1 — Build a feedback loop *(this is the skill)*",
    "### Phase 2 — Reproduce",
    "### Phase 3 — Hypothesise",
    "### Phase 4 — Instrument",
    "### Phase 5 — Fix + regression test",
    "### Phase 6 — Cleanup + post-mortem",
]

# sha256 of each pre-change section body, exactly as extract_section() returns it.
PHASE_BODY_SHA256_PRE_CHANGE = {
    "Phase 1 — Build a feedback loop": (
        "40215079ad4721e0a9e548fd70d510f619907759e112cc5a84cfa875eccfe532"
    ),
    "Phase 2 — Reproduce": (
        "c7959c08af1e1b8dea0a9a2156e82683ccf88c4e41cb2c72b793ea6de03630b2"
    ),
    # T067 re-pin. T058/T060 held Phase 3 out of scope; T067's AC7 deliberately
    # changes it (the working-reference comparison is a hypothesis *source*, so it
    # belongs in Phase 3) and T067's AC11 narrows the byte-identical guarantee to
    # Phase 1 and Phase 2 only. The pin is re-captured, not deleted, so Phase 3
    # stays locked against unintended drift from here on; the 3–5 requirement is
    # separately pinned by test_t067_t058_and_t060_numbers_are_unchanged.
    "Phase 3 — Hypothesise": (
        "0a33b7ed9cd3ee381d8d65cbc11b592c4854f505371eefed13367c7244a23762"
    ),
}

# Minimum body lengths, so a truncated-but-same-shape extraction cannot slip past the hash
# check being the only guard (belt-and-braces against the T039 vacuity family).
PHASE_BODY_MIN_LEN = {
    "Phase 1 — Build a feedback loop": 900,
    "Phase 2 — Reproduce": 100,
    "Phase 3 — Hypothesise": 600,
}


# ---------------------------------------------------------------------------
# SC1 / AC1 — Phase 4 is a procedure of >= 5 enumerated steps
# ---------------------------------------------------------------------------

def test_sc1_phase4_is_an_enumerated_procedure():
    body = phase4()
    steps = re.findall(r"^\d+\.\s+\S", body, re.MULTILINE)
    assert len(steps) >= 5, (
        f"Phase 4 must be a procedure of at least 5 enumerated steps, found {len(steps)}:\n{body}"
    )


# ---------------------------------------------------------------------------
# SC2 / AC2 — NDJSON log format + payload field list
# ---------------------------------------------------------------------------

def test_sc2_phase4_specifies_ndjson_and_payload_fields():
    body = phase4()
    assert "NDJSON" in body, "Phase 4 must name NDJSON as the log format"
    assert re.search(r"one JSON object per line", body, re.IGNORECASE), (
        "Phase 4 must state one JSON object per line"
    )
    for field in ("hypothesisId", "location", "message", "data", "timestamp"):
        assert f"`{field}`" in body, f"Phase 4 payload field list is missing `{field}`"


# ---------------------------------------------------------------------------
# SC2 / AC3 — every probe carries a hypothesisId; unmapped probes not inserted
# ---------------------------------------------------------------------------

def test_sc2_phase4_requires_hypothesis_id_per_probe():
    body = phase4()
    assert "hypothesisId" in body
    assert re.search(r"maps to no hypothesis is not inserted", body), (
        "Phase 4 must forbid inserting a probe that maps to no hypothesis"
    )


# ---------------------------------------------------------------------------
# SC2 / AC4 — the five placement categories
# ---------------------------------------------------------------------------

def test_sc2_phase4_names_the_placement_categories():
    body = phase4()
    for category in (
        r"function entry with parameters",
        r"function exit with return values",
        r"before/after a critical operation",
        r"which branch executed",
        r"state mutations",
    ):
        assert re.search(category, body), (
            f"Phase 4 is missing placement category matching: {category}"
        )


# ---------------------------------------------------------------------------
# SC2 / AC5 — explicit log budget with numeric bounds
# ---------------------------------------------------------------------------

def test_sc2_phase4_states_the_log_budget():
    body = phase4()
    assert re.search(r"at least 1 probe", body), "Phase 4 must state a floor of 1 probe"
    assert re.search(r"never more than 10", body), "Phase 4 must state a ceiling of 10 probes"
    assert re.search(r"2\D{1,3}6", body), "Phase 4 must state the typical 2-6 range"
    assert re.search(r"narrow it", body), (
        "Phase 4 must instruct narrowing the hypothesis set rather than exceeding the ceiling"
    )


# ---------------------------------------------------------------------------
# SC2 / AC6 — region markers, language-appropriate comment syntax
# ---------------------------------------------------------------------------

def test_sc2_phase4_requires_region_debug_log_markers():
    body = phase4()
    assert "#region debug log" in body, "Phase 4 must require `#region debug log` markers"
    assert "#endregion" in body, "Phase 4 must require a matching `#endregion`"
    assert re.search(r"language-appropriate comment syntax", body), (
        "Phase 4 must not hardcode one language's comment syntax"
    )


# ---------------------------------------------------------------------------
# SC2 / AC7 — secrets/PII prohibition and clearing the log between runs
# ---------------------------------------------------------------------------

def test_sc2_phase4_forbids_secrets_and_requires_clearing_the_log():
    body = phase4()
    for secret in ("secrets", "tokens", "API keys", "PII"):
        assert secret in body, f"Phase 4's prohibition list is missing '{secret}'"
    assert re.search(r"[Nn]ever log", body), "Phase 4 must forbid, not merely discourage, logging these"
    assert re.search(r"clear the log file", body, re.IGNORECASE), (
        "Phase 4 must require clearing the log file before each run"
    )
    assert re.search(r"runs do not mix", body), (
        "Phase 4 must state why the log is cleared: runs must not mix"
    )


# ---------------------------------------------------------------------------
# Stage 4 P2 — constraints the guide's Approach lists as "must survive the rewrite".
# These are present in the shipped file but were unpinned: nothing failed if a future
# edit dropped them. Same class as the repo's recorded "an assertion never observed
# failing is not evidence" incidents, one step earlier — an assertion never written.
# ---------------------------------------------------------------------------

def test_p2_phase4_retains_the_perf_sub_case():
    body = phase4()
    assert re.search(r"measure a baseline first", body), (
        "Phase 4 must retain the perf sub-case: measure a baseline before bisecting"
    )
    assert re.search(r"profiler/timing/query\s+plan", body), (
        "Phase 4 must retain the named baseline instruments (profiler/timing/query plan)"
    )
    assert re.search(r"then bisect", body), "Phase 4 must retain 'then bisect' for the perf path"


def test_p2_phase4_has_a_no_seam_fallback():
    body = phase4()
    assert re.search(r"[Ii]f no seam exists", body), (
        "Phase 4 must not dead-end when no seam exists for a probe"
    )
    assert re.search(r"Phase 1", body), (
        "the no-seam fallback must route back to the Phase 1 ladder"
    )
    assert re.search(r"differential and bisection", body), (
        "the no-seam fallback must name the differential and bisection rungs"
    )


def test_p2_phase4_retains_one_variable_at_a_time():
    body = phase4()
    assert re.search(r"change one variable at a time", body, re.IGNORECASE), (
        "Phase 4 must retain the Surgical-Changes constraint: one variable at a time"
    )


# ---------------------------------------------------------------------------
# SC3 / AC8 — three-verdict vocabulary; only REJECTED increments the counter
# ---------------------------------------------------------------------------

def test_sc3_checkpoint_uses_three_verdicts():
    body = checkpoint()
    for verdict in ("CONFIRMED", "REJECTED", "INCONCLUSIVE"):
        assert verdict in body, f"Stuck-Loop Checkpoint is missing the {verdict} verdict"
    assert re.search(r"citing the specific log lines", body), (
        "each verdict must cite the specific log lines that decided it"
    )


def test_sc3_only_rejected_increments_the_counter():
    body = checkpoint()
    assert re.search(r"Only \*\*REJECTED\*\* increments", body), (
        "the checkpoint must state that only REJECTED increments the consecutive-disproof counter"
    )
    assert re.search(r"neither increments nor resets", body), (
        "the checkpoint must state INCONCLUSIVE neither increments nor resets the counter"
    )
    assert re.search(r"instrument the \*same\* hypothesis better", body), (
        "INCONCLUSIVE must route back to better instrumentation of the same hypothesis, "
        "not become an escape hatch"
    )
    assert re.search(r"2 consecutive hypotheses are REJECTED", body), (
        "T052's threshold must survive under the new vocabulary"
    )


# ---------------------------------------------------------------------------
# SC4 / AC9 + AC10 — Phase 5 retains instrumentation; reverts REJECTED changes
# ---------------------------------------------------------------------------

def test_sc4_phase5_retains_instrumentation_until_post_fix_verification():
    body = extract_section(read_skill(), "Phase 5 — Fix + regression test")
    assert re.search(r"active through the fix", body), (
        "Phase 5 must state instrumentation is kept active through the fix"
    )
    assert re.search(r"post-fix\s+verification run", body), (
        "Phase 5 must tie removal to a post-fix verification run"
    )
    assert re.search(r"logs show the expected values", body), (
        "Phase 5 must require the post-fix run's logs to prove success"
    )


def test_sc4_phase5_reverts_rejected_hypothesis_changes():
    body = extract_section(read_skill(), "Phase 5 — Fix + regression test")
    assert "REJECTED" in body, "Phase 5 must reference the REJECTED verdict"
    assert re.search(r"revert every code change", body), (
        "Phase 5 must require reverting code changes made for REJECTED hypotheses"
    )
    assert re.search(r"must not accumulate", body), (
        "Phase 5 must say speculative guards do not accumulate into the fix"
    )


# ---------------------------------------------------------------------------
# SC5 / AC11 — Phase 6 cleanup is marker-driven, re-grepped, git-diff reviewed
# ---------------------------------------------------------------------------

def test_sc5_phase6_cleanup_is_marker_driven():
    body = extract_section(read_skill(), "Phase 6 — Cleanup + post-mortem")
    assert "#region debug log" in body, (
        "Phase 6 cleanup must key off the `#region debug log` marker"
    )
    assert "#endregion" in body, "Phase 6 must say to delete through the matching `#endregion`"
    assert re.search(r"confirm zero remain", body), (
        "Phase 6 must require a re-grep confirming zero markers remain"
    )
    assert re.search(r"`git diff`", body), (
        "Phase 6 must require a `git diff` review confirming only the intended fix is left"
    )


def test_sc5_retired_debug_prefix_no_longer_referenced():
    """The `[DEBUG-xxxx]` prefix is superseded by the region markers. A dangling reference
    anywhere in the file would leave two competing cleanup contracts (AC11's edge case)."""
    text = read_skill()
    assert "[DEBUG-" not in text, (
        "the retired `[DEBUG-...]` prefix convention is still referenced in diagnose/SKILL.md"
    )


# ---------------------------------------------------------------------------
# SC6 / AC12 — line 8 byte-identical (negative)
# ---------------------------------------------------------------------------

def test_sc6_line_8_is_byte_identical():
    lines = read_skill().split("\n")
    assert lines[7] == LINE_8_PRE_CHANGE, (
        "diagnose/SKILL.md line 8 changed — the dropped Complexity-gating direction must not "
        f"re-enter.\n  expected: {LINE_8_PRE_CHANGE!r}\n  actual:   {lines[7]!r}"
    )


# ---------------------------------------------------------------------------
# SC7 / AC13 — the ordered `### Phase` heading list is unchanged (negative)
# ---------------------------------------------------------------------------

def test_sc7_phase_headings_unchanged_in_text_count_and_order():
    headings = re.findall(r"^### Phase .*$", read_skill(), re.MULTILINE)
    assert headings == PHASE_HEADINGS_PRE_CHANGE, (
        "the `### Phase` heading list changed — no phase may be added, removed, renamed, or "
        f"reordered.\n  expected: {PHASE_HEADINGS_PRE_CHANGE}\n  actual:   {headings}"
    )


# ---------------------------------------------------------------------------
# SC8 / AC14 — Phase 1/2/3 bodies byte-identical (negative)
# ---------------------------------------------------------------------------

def test_sc8_phase_1_2_3_bodies_are_byte_identical():
    text = read_skill()
    for heading, expected_sha in PHASE_BODY_SHA256_PRE_CHANGE.items():
        body = extract_section(text, heading)
        assert len(body) >= PHASE_BODY_MIN_LEN[heading], (
            f"'{heading}' body is {len(body)} chars, shorter than its pre-change minimum "
            f"{PHASE_BODY_MIN_LEN[heading]} — extraction truncated or content was removed"
        )
        actual_sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
        assert actual_sha == expected_sha, (
            f"'{heading}' body changed — Phase 1/2/3 are explicitly out of scope for T058.\n"
            f"  expected sha256: {expected_sha}\n  actual sha256:   {actual_sha}"
        )


# ===========================================================================
# T060 — cross-tier boundary instrumentation and correlated trace reporting.
#
# Phase 4 gains a discovery-only boundary inventory and a `traceparent`-shaped
# correlation field; the Stuck-Loop Checkpoint gains path reconstruction.
#
#   T060-SC1 — boundary inventory names all four artifact classes (AC1)
#   T060-SC1 — the inventory is discovery-only and does not authorise a probe (AC2)
#   T060-SC2 — `traceparent` correlation, trace-id/span-id roles, convention-not-SDK (AC3)
#   T060-SC2 — header-less hops carry the value in the payload (AC4)
#   T060-SC2 — a dropped value fragments the trace; mismatch judges the hop (AC5)
#   T060-SC3 — path reconstruction precedes verdicts (AC6) and reports
#              `path incomplete` rather than inferring a missing side (AC7)
#   T060      — event-trace read-vs-write split (AC8); global probe budget (AC9)
#   T060-SC6  — negative: no `daemon` / `ingest server` / `relay` re-enters (AC12)
#
# AC10/AC11 (Phase 1/2/3 bodies and the Phase heading list unchanged) are already
# enforced by test_sc7_* and test_sc8_* above. Their fixtures were re-captured from
# the pre-T060 tree at 1ac8cfa and are byte-identical to the pinned values, so the
# existing constants stand as this task's pre-change capture — no new pins needed.
# ===========================================================================


def test_t060_boundary_inventory_names_the_four_artifact_classes():
    body = phase4()
    assert re.search(r"\*\*Boundary inventory\*\*", body), (
        "Phase 4 must have a Boundary inventory step"
    )
    for artifact in (
        r"HTTP route/handler definitions",
        r"outbound HTTP client call sites",
        r"`fetch`/`axios`/`requests`",
        r"queue or job publish/consume points",
        r"sub-agent spawn sites",
    ):
        assert re.search(artifact, body), (
            f"the boundary inventory is missing the artifact class: {artifact}"
        )


def test_t060_boundary_inventory_is_discovery_only():
    """AC2 — the mitigation for the recorded TraceCoder risk. If discovery ever
    authorises a probe on its own, the 1-10 budget dies on first real use."""
    body = phase4()
    assert re.search(r"discovery-only", body), (
        "the inventory step must be labelled discovery-only"
    )
    assert re.search(r"does not authorise a probe", body), (
        "the inventory step must state that building it does not authorise a probe"
    )
    assert re.search(r"hypothesis gate still decides", body), (
        "the inventory step must defer to the existing hypothesis gate"
    )
    assert re.search(r"maps to no hypothesis is not inserted", body), (
        "the no-orphan-probe gate the inventory defers to must still be present"
    )


def test_t060_empty_inventory_does_not_stall_phase4():
    body = phase4()
    assert re.search(r"empty inventory", body, re.IGNORECASE), (
        "Phase 4 must handle a single-process project with zero boundaries"
    )


def test_t060_correlation_uses_a_traceparent_shaped_value():
    body = phase4()
    assert "traceparent" in body, "Phase 4 must name the `traceparent` header literally"
    assert re.search(r"W3C Trace Context", body), (
        "Phase 4 must name W3C Trace Context as the adopted convention"
    )
    assert re.search(r"trace-id\*\*? shared by every probe", body), (
        "Phase 4 must state the trace-id is shared across one request's probes"
    )
    assert re.search(r"span-id\*\*? unique to each probe", body), (
        "Phase 4 must state the span-id is unique per probe"
    )
    assert "`traceparent`" in body and re.search(
        r"`hypothesisId`, `location`, `message`, `data`, `timestamp`, `traceparent`", body
    ), "the NDJSON payload field list must carry the correlation field"


def test_t060_correlation_is_convention_not_dependency():
    """The guide's hardest constraint: shape and header name only, no SDK."""
    body = phase4()
    assert re.search(r"convention only", body), (
        "Phase 4 must state the correlation format is a convention only"
    )
    assert re.search(r"never an SDK, library, or dependency", body), (
        "Phase 4 must forbid adopting an implementation alongside the convention"
    )


def test_t060_traceparent_is_omitted_when_the_inventory_is_empty():
    """Stage 4 P2 (Supervisor): `traceparent` was added to the payload field list
    unconditionally, while step 4 tells the empty-inventory single-process case to
    proceed "unchanged" -- which would require a degenerate correlation field on
    every probe of a run that has no hop for it to join. The scoping sentence that
    resolves this had no assertion pinning it, the same gap T058's own Stage 4 P2
    found."""
    body = phase4()
    assert re.search(r"omit\s+it when the inventory is empty", body), (
        "Phase 4 must scope `traceparent` out of the empty-inventory case"
    )
    assert re.search(r"single-process run has no hop", body), (
        "Phase 4 must say why it is omitted, not just that it is"
    )


def test_t060_headerless_hops_carry_correlation_in_the_payload():
    body = phase4()
    assert re.search(r"ride \*\*in the payload\*\*", body), (
        "Phase 4 must state the correlation value rides in the payload when headers cannot carry it"
    )
    for case in (r"queue\s+message", r"background job", r"sub-agent spawn"):
        assert re.search(case, body), (
            f"Phase 4 must name the header-less hop case: {case}"
        )


def test_t060_dropped_correlation_is_a_fragmented_trace():
    body = phase4()
    assert re.search(r"fragmented trace", body), (
        "Phase 4 must name the fragmented-trace failure mode of a dropped correlation value"
    )
    assert re.search(r"mismatched trace-ids is evidence\s+about that hop, not about the hypothesis", body), (
        "a mismatched probe pair must be reported as evidence about the hop, not the hypothesis"
    )


def test_t060_event_trace_is_readable_but_never_writable():
    """AC8 — the deliberate amendment to T058. Both halves must be stated."""
    body = phase4()
    assert re.search(r"Never \*write\* debug output to `memory/event-trace/`", body), (
        "Phase 4 must keep T058's prohibition on writing debug output to memory/event-trace/"
    )
    assert re.search(
        r"\*Reading\* `memory/event-trace/\*\.jsonl`.*?is permitted", body, re.DOTALL
    ), "Phase 4 must permit reading memory/event-trace/*.jsonl as a correlation source"
    assert re.search(r"writing to it is not", body), (
        "the read permission must restate that writing remains forbidden"
    )


def test_t060_probe_budget_ceiling_is_global():
    """AC9 — the inventory must not smuggle in a per-boundary budget."""
    body = phase4()
    assert re.search(r"never more than 10", body), "the 10-probe ceiling must be unchanged"
    assert re.search(r"ceiling is global", body), (
        "Phase 4 must state the ceiling is global, not per-boundary"
    )
    assert re.search(r"no boundary,? and no inventory entry.*?earns a probe budget of its own", body), (
        "Phase 4 must forbid a per-boundary probe budget"
    )


def test_t060_checkpoint_reconstructs_the_path_before_verdicts():
    body = checkpoint()
    assert re.search(r"before assigning any verdict", body, re.IGNORECASE), (
        "path reconstruction must be ordered before verdict assignment"
    )
    assert re.search(r"[Gg]roup .*probes by trace-id", body), (
        "path reconstruction must group probes by trace-id"
    )
    assert re.search(r"order\s+each group by timestamp", body), (
        "path reconstruction must order each trace-id group by timestamp"
    )
    assert re.search(
        r"first boundary at which the observed value diverged from the\s+predicted value", body
    ), "path reconstruction must name the first boundary where observed diverged from predicted"
    assert re.search(r"never merge two trace-ids", body), (
        "concurrent requests must not be merged into one path"
    )
    # ordering: reconstruction precedes the CONFIRMED/REJECTED/INCONCLUSIVE resolution
    assert body.index("Path reconstruction") < body.index("CONFIRMED"), (
        "path reconstruction must appear before the verdict vocabulary in the Checkpoint"
    )


def test_t060_one_sided_probes_report_path_incomplete():
    """AC7 is load-bearing: absence must never be laundered into an inferred value."""
    body = checkpoint()
    assert "`path incomplete`" in body, (
        "the Checkpoint must define the `path incomplete` outcome"
    )
    assert re.search(r"probes on\s+only one side of a boundary", body), (
        "`path incomplete` must be triggered by one-sided probe sets"
    )
    assert re.search(r"never infer what the missing side saw", body), (
        "the Checkpoint must forbid inferring the missing side"
    )
    assert re.search(r"not licence to conclude", body), (
        "`path incomplete` must be a finding about instrumentation, like INCONCLUSIVE"
    )


def test_t060_rejected_transport_layer_did_not_re_enter():
    """AC12 — negative, file-wide by design (a stray mention anywhere reopens
    the transport T058 rejected outright). This assertion passes trivially on a
    file that never mentioned the tokens, so it was mutation-verified RED."""
    text = read_skill().lower()
    for token in ("daemon", "ingest server", "relay"):
        assert token not in text, (
            f"`{token}` appears in diagnose/SKILL.md — T058 rejected the daemon/ingest/relay "
            "transport outright and T060 does not reopen it"
        )


# ===========================================================================
# T067 — root-cause rule, backward tracing, red flags, working-reference
# comparison. Prior art (obra/superpowers systematic-debugging) consulted, not
# vendored; its defense-in-depth step was REJECTED outright (AC10).
#
#   T067-AC1  — root-cause rule in the Karpathy block
#   T067-AC2  — restated in Phase 5 at the point of action
#   T067-AC3/4 — backward tracing: five ordered steps, scoped, Placement intact
#   T067-AC5/6 — red flags: >=4 behaviours, route to Phase 1, sibling of the
#                Checkpoint rather than a replacement for it
#   T067-AC7  — Phase 3 working-reference comparison
#   T067-AC8  — Phase 4 payload: stack capture + test-visible output
#   T067-AC9  — Stuck-Loop "widen scope" names the architectural tell
#   T067-AC10 — negative, file-wide: defense-in-depth must not re-enter
#   T067-AC13/14 — T058/T060 numbers unchanged (1-10 budget, 2 consecutive
#                REJECTED, 3-5 hypotheses)
#   T067-AC15 — negative: the file stays <= 165 lines
#
# These assert *instruction text*, not runtime behaviour. AC10 and AC15 pass
# trivially on a compliant file, so both were mutation-verified RED by
# introducing the forbidden token and by padding the file past the cap.
# ===========================================================================

LINE_COUNT_CAP_T067 = 165


def karpathy():
    return extract_section(read_skill(), "Karpathy Operational Commands")


def phase3():
    return extract_section(read_skill(), "Phase 3 — Hypothesise")


def phase5():
    return extract_section(read_skill(), "Phase 5 — Fix + regression test")


def test_t067_karpathy_block_carries_the_root_cause_rule():
    body = karpathy()
    assert re.search(r"root cause", body, re.IGNORECASE), (
        "the Karpathy block must carry a root-cause rule"
    )
    assert re.search(r"originated", body), (
        "the rule must say the fix lands where the cause originated"
    )
    assert re.search(r"surfaced", body), (
        "the rule must contrast with where the error surfaced"
    )
    assert re.search(r"failure, not a partial success", body), (
        "a symptom fix must be framed as a failure, not a partial success"
    )
    assert re.search(r"CONFIRMED", body), (
        "'root cause' must be tied to the CONFIRMED verdict, not asserted freely"
    )


def test_t067_phase5_restates_the_rule_at_the_point_of_action():
    body = phase5()
    assert re.search(r"[Bb]efore writing the fix", body), (
        "Phase 5 must place the root-cause check before the fix is written"
    )
    assert re.search(r"root cause", body, re.IGNORECASE), (
        "Phase 5 must name the root cause at the point of action"
    )
    assert re.search(r"confirm the fix lands", body), (
        "Phase 5 must require confirming the fix lands at the root cause"
    )
    assert re.search(r"failure, not a partial success", body), (
        "Phase 5 must restate the symptom-fix verdict, not merely gesture at it"
    )
    # Edge case: the rule must not make the existing no-seam finding unreachable.
    assert re.search(r"no-seam finding.*reachable", body), (
        "Phase 5 must state the root-cause rule does not close off the no-seam path"
    )


def test_t067_phase4_backward_tracing_names_the_five_ordered_steps():
    body = phase4()
    assert re.search(r"\*\*Backward tracing\*\*", body), (
        "Phase 4 must name the backward tracing technique"
    )
    steps = [
        r"observe the symptom",
        r"identify the code that directly produced it",
        r"identify that code's caller",
        r"continue up the call chain recording the value passed at each\s+level",
        r"locate where the invalid\s+value originated",
    ]
    positions = []
    for step in steps:
        match = re.search(step, body)
        assert match is not None, f"backward tracing is missing the step: {step}"
        positions.append(match.start())
    assert positions == sorted(positions), (
        f"backward tracing's five steps are out of order: {positions}"
    )


def test_t067_backward_tracing_is_scoped_and_does_not_replace_placement():
    """AC4 — it fits a value-wrong-on-arrival bug, not every bug, and the
    existing Placement options keep their role."""
    body = phase4()
    assert re.search(r"invalid when it arrives", body), (
        "backward tracing must be scoped to the value-wrong-on-arrival shape"
    )
    assert re.search(r"does not apply to a perf regression or a flaky test", body), (
        "backward tracing must be excluded from the perf and flaky-test shapes"
    )
    assert re.search(r"replaces\s+none of step 5's Placement options", body), (
        "backward tracing must not replace or reorder the Placement options"
    )


def test_t067_red_flags_name_four_behaviours_and_route_to_phase_1():
    body = phase4()
    assert re.search(r"\*\*Red flags", body), "Phase 4 must carry a red-flag block"
    for behaviour in (
        r"proposing a fix before tracing",
        r"changing more than one variable at a time",
        r"asserting a\s+cause without evidence from the loop",
        r"reaching for a quick fix under time pressure",
    ):
        assert re.search(behaviour, body), (
            f"the red-flag block is missing the behaviour: {behaviour}"
        )
    assert re.search(r"returns you to \*\*Phase 1\*\*", body), (
        "any red flag must route the agent back to Phase 1"
    )


def test_t067_red_flags_are_the_checkpoints_sibling_not_its_replacement():
    """AC6 — the two mechanisms must stay distinguishable: the Checkpoint counts
    disproven hypotheses and offers three options; red flags fire earlier on
    behaviour and offer none."""
    body = phase4()
    assert re.search(r"\*before\* the Stuck-Loop Checkpoint", body), (
        "the red-flag block must state it fires before the Stuck-Loop Checkpoint"
    )
    assert re.search(r"do not replace it", body), (
        "the red-flag block must state it does not replace the Checkpoint"
    )
    assert re.search(r"counts disproven\s+hypotheses", body), (
        "the block must name what the Checkpoint does, so the two stay distinct"
    )
    assert re.search(r"offer no choice at all", body), (
        "red flags must not duplicate the Checkpoint's three named options"
    )
    # Ordering: the red flags sit before the Checkpoint section in the file.
    text = read_skill()
    assert text.index("**Red flags") < text.index("### Stuck-Loop Checkpoint"), (
        "the red-flag block must be placed before the Stuck-Loop Checkpoint heading"
    )


def test_t067_phase3_gains_the_working_reference_comparison():
    body = phase3()
    assert re.search(r"\*\*Working-reference comparison\*\*", body), (
        "Phase 3 must carry a working-reference comparison"
    )
    assert re.search(r"locate similar code that \*works\*", body), (
        "the comparison must start by locating similar code that works"
    )
    assert re.search(r"enumerate the differences", body), (
        "the comparison must enumerate differences against the broken path"
    )
    assert re.search(r"derive hypotheses from those differences", body), (
        "the comparison must derive hypotheses from the differences"
    )
    assert re.search(r"[Ii]f no working reference exists", body), (
        "the comparison must degrade gracefully when no reference exists"
    )


def test_t067_phase4_payload_notes_stack_capture_and_test_visible_output():
    body = phase4()
    assert re.search(r"capture a \*\*stack trace\*\* to\s+identify its caller", body), (
        "the payload guidance must allow capturing a stack trace to identify the caller"
    )
    assert re.search(r"secrets/PII rule above is unchanged", body), (
        "stack capture must not weaken the existing secrets/PII prohibition"
    )
    assert re.search(r"test\s+output actually surfaces", body), (
        "the payload guidance must require probe output to go where test output surfaces"
    )
    assert re.search(r"logger may be suppressed", body), (
        "the payload guidance must say why: a project logger may be suppressed under test"
    )


def test_t067_widen_scope_names_the_architectural_tell():
    body = checkpoint()
    assert re.search(r"architectural\s+tell", body), (
        "the 'widen scope' option must name the architectural tell"
    )
    assert re.search(
        r"each fix reveals new shared state or coupling in a \*different\* place", body
    ), "the tell must be: each fix revealing new coupling somewhere else"
    assert re.search(r"design\s+problem, not the next bug", body), (
        "the tell must classify this as a design problem rather than a next bug"
    )


def test_t067_defense_in_depth_did_not_re_enter():
    """AC10 — negative, file-wide by design: the rejected direction must not
    appear in any spelling anywhere in the document. This passes trivially on a
    file that never mentioned it, so it was mutation-verified RED by inserting
    the token."""
    text = read_skill().lower()
    for token in ("defense-in-depth", "defence-in-depth", "defense in depth", "defence in depth"):
        assert token not in text, (
            f"`{token}` appears in diagnose/SKILL.md — T067 rejected defense-in-depth "
            "outright; Phase 5's revert-REJECTED-changes rule already stops guards accumulating"
        )


def test_t067_t058_and_t060_numbers_are_unchanged():
    """AC13/AC14 — the prior art's weaker numbers must not displace ours."""
    body = phase4()
    assert re.search(r"at least 1 probe", body) and re.search(r"never more than 10", body), (
        "the 1-10 probe budget established by T058 must survive"
    )
    cp = checkpoint()
    assert re.search(r"2 consecutive hypotheses are REJECTED", cp), (
        "T052's 2-consecutive-REJECTED trigger must not be replaced by the prior art's "
        "3-failed-fix-attempts trigger"
    )
    assert "3 failed" not in read_skill(), (
        "the prior art's 3-failed-fix-attempts escalation must not have been imported"
    )
    assert re.search(r"\*\*3–5 ranked, falsifiable\*\* hypotheses", phase3()), (
        "Phase 3 must still require 3-5 ranked falsifiable hypotheses, not a single hypothesis"
    )


def test_t067_file_stays_within_the_line_cap():
    """AC15 — the cap is a hard constraint, not advice. Counts the whole file
    including frontmatter. Passes trivially under the cap, so it was
    mutation-verified RED by padding the file past 165 lines."""
    # Count exactly as `grep -c ''` does. `rstrip("\n")` would strip ALL
    # trailing newlines, so blank-line padding past the cap was invisible while
    # the docstring claimed the whole file was counted (Supervisor Stage 4 P3).
    text = read_skill()
    line_count = text.count("\n") + (0 if text.endswith("\n") else 1)
    assert line_count <= LINE_COUNT_CAP_T067, (
        f"diagnose/SKILL.md is {line_count} lines, over the {LINE_COUNT_CAP_T067}-line cap — "
        "tighten the prose rather than raising the cap"
    )


if __name__ == "__main__":
    import sys

    sys.exit(__import__("pytest").main([__file__, "-v"]))
