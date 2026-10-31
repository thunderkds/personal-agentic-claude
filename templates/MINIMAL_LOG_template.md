# Minimal-track Decision records

> One Decision record per minimal-track task (`docs/claude-md/tracks.md`), **newest first**: insert each
> new record directly under this note. On first use, the Supervisor creates `tasks/MINIMAL_LOG.md` from
> this template and deletes the example comment. The same block is the Supervisor's final chat message.

<!-- Record shape. Copy it for each task; replace every <...>.

## <ID> — <title> · <track>
**Asked:** "<the request, verbatim>"
**Decisions:**
- <decision> — <reason>
- Assumed: <an assumption, stated as one> — <why it is safe to go on>
**Checked:**
- New test `<test name>` — <failed before the change, passes after>
- Suite: `<command>` — <its result line>
- Real run: `<command>` — printed `<what it printed>`
**Files:** `<path>`, `<path>`
**Not done:** merge (the user decides)<; anything else left undone>

<track> is `minimal`. When the user set the track against the rule, the first `Decisions:` line says
so: `- Track minimal — track set by the user; <the risk, in one line>`.

In auto mode (the user's `[auto]` tag, `docs/claude-md/tracks.md` `## Auto mode`) the record is the final
report. Write it to its file before the run ends; the chat message is a copy, not the report.
`Mode: auto` is the line right under the heading, exactly as written: T182's hook reads it. Each
decision says how it was made. A Debate, safer-option or taste decision ends with the flag. Write `DEBATED`
only when ≥2 Advocate `Agent` calls ran for that question, naming each Advocate's option. A decision with
no Advocates is labelled `RULE`, `FACT` or `SAFER OPTION`, never `DEBATED`. A decision flagged `⚠ decided for you` is a choice, and is never labelled `FACT`. A
safety action a rule requires (for example the backup before a delete) is `RULE` without the flag.
At Risk Medium or High, a `RULE:` counts only when it names a written rule (`path:line`,
`path § <heading>`, or `docs/claude-md/tracks.md` `### <section>`), and a `FACT:` needs a Citation
(`path:line "quoted text"`); without one it is a choice and must be `DEBATED`. Good: `2. backed up the CSV
— RULE: `docs/claude-md/tracks.md` `### Stops that stay``. Bad: `1. kept recurring.csv — RULE: Surgical Changes`.
`**Memory:**` records the diff-driven memory pass you run before you stop: each entry written, or `nothing
new`. After an auto verify pass the hook, never you, adds `Closed: row moved to Done <date> — …` and moves
the row, or adds `Paused: done not moved — <reason>`. It moves the row only when the record holds
`Mode: auto`, a numbered decision, `**Checked:**` with a `New test` line, `**Memory:**`, the `**Not done:**`
auto verify slot with its result, and `**Not done:**` naming the merge — no `<...>` left
(`docs/claude-md/tracks.md` `### Auto close-out`). The record:

## <ID> — <title> · minimal
Mode: auto
**Asked:** "<the request, verbatim, with its [auto] tag>"
**Decisions:**
1. <what was decided> — RULE: <the rule>
2. <what was decided> — FACT: <path>:<line> "<quoted text>"
3. <what was decided> — DEBATED: <option> (Advocate 1: <its proposal>; Advocate 2: <its proposal>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
**Checked:**
- New test `<test name>` — <failed before the change, passes after>
- Suite: `<command>` — <its result line>
- Real run: `<command>` — printed `<what it printed>` (auto-checked, not /verify)
**Files:** `<path>`, `<path>`
**Memory:** <each entry the memory pass wrote, as `file — entry` | nothing new>
**Not done:** merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>
-->
