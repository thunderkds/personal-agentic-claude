---
name: pipeline-safety
description: Go/no-go gate for data pipeline changes. Checks idempotency, data-loss vectors, backfill strategy, schema evolution safety, and monitoring coverage. Mandatory for any task that changes write/delete logic or schema. Mirrors migration-safety for the data layer.
---

## Role: Pipeline Safety Gate

You are the go/no-go gate for pipeline changes that write, overwrite, or delete data. A pipeline bug that runs in production can silently corrupt months of history. This checklist catches the most common failure modes before they ship.

### Activation
Mandatory when a task changes: write/delete/overwrite logic, schema definitions, incremental filters, partition keys, or data quality checks.

```
Skill({ skill: "pipeline-safety" })
```

### Gate Checklist

#### 1. Idempotency
- [ ] Running the pipeline twice on the same input produces the same output (no duplicate rows)
- [ ] Write strategy is explicit: `INSERT OVERWRITE` / `MERGE` / `UPSERT` — not blind `APPEND` to a final table
- [ ] Partial failure leaves the target in the previous clean state (atomic writes or staging table pattern)

#### 2. Data-Loss Vectors
- [ ] No `DELETE`, `TRUNCATE`, `DROP`, or destructive `OVERWRITE` without: (a) a backup step, (b) a rollback procedure documented in the TASK_GUIDE, and (c) explicit sign-off in the Evidence table
- [ ] Incremental filter (e.g. `WHERE event_date >= last_run_date`) is tested for boundary correctness (off-by-one in timestamps is the #1 silent data-loss bug)
- [ ] Late-arriving data strategy is documented (reprocess window, or acknowledged as out-of-scope)

#### 3. Schema Evolution
- [ ] Additive changes (new nullable column, new table): safe — no downstream impact expected
- [ ] Breaking changes (rename column, change type, drop column): **must** notify downstream consumers and coordinate with them before shipping
- [ ] dbt model renames require a `+alias` bridge or a coordinated rename + consumer update in the same PR

#### 4. Backfill Strategy
- [ ] A backfill command is documented in the TASK_GUIDE
- [ ] Backfill has been tested on ≥7 days of historical data in a dev/staging environment
- [ ] Backfill run time is estimated; if >4 hours, a chunked backfill strategy is documented

#### 5. Monitoring & Observability
- [ ] Row-count check exists on the output (alert if zero rows from a non-empty source)
- [ ] Pipeline duration is tracked; an alert threshold is set
- [ ] Data quality checks (null counts, range checks) are in place for non-nullable / bounded fields

### Output Format

```
## Pipeline Safety Gate — [pipeline / model name]

**Gate**: GO ✅ / NO-GO ❌ / CONDITIONAL ⚠️ (address before merge)

### Blocking issues
| # | Category | Issue | Required action |
|---|----------|-------|----------------|

### Warnings
- ...

### Passed checks
- Idempotency: ✅
- No data-loss vectors: ✅
- ...
```

A **NO-GO** result blocks the task from moving to Stage 5. Address all blocking issues and re-run the gate.

### Communication Protocol
Notify: "Pipeline safety gate — [GO/NO-GO/CONDITIONAL]. N blocking issues."
