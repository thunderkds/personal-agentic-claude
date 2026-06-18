# PACK.md — Data
**Pack**: `data`
**Domain**: Data pipelines, ETL, notebooks, dbt, Spark, Pandas, Polars, feature engineering
**Core framework version tested**: 1.14+

---

## When to use this pack

Select when the project's primary output is data movement, transformation, or analysis — not a user-facing application. The core `backend-developer` can write Python services; this pack adds the data-specific mindset: pipeline idempotency, schema evolution, data quality, and notebook reproducibility.

**Select this pack when your project involves:**
- ETL / ELT pipelines (Airflow, Prefect, dbt, Spark, Beam)
- Jupyter / Marimo notebooks as deliverables
- Data warehousing or lakehouse patterns (BigQuery, Snowflake, Delta Lake)
- Feature engineering pipelines for ML models
- Data quality frameworks (Great Expectations, dbt tests)

**Do NOT select if:** the project uses a database purely as a persistence layer for a web/mobile app — the core `backend-developer` + `migration-safety` skill is sufficient.

---

## What this pack adds

| Resource | Type | Purpose |
|----------|------|---------|
| `data-engineer` | Agent | Pipeline-first implementer: idempotency, schema evolution, data quality |
| `notebook-review` | Skill | Reproducibility, cell ordering, secrets, output size audit for notebooks |
| `pipeline-safety` | Skill | Data-loss prevention gate for pipeline changes (mirrors migration-safety for data) |

**Boundary from core agents:**
- Core `backend-developer` handles: application services, ORM/query layer, REST APIs over data
- This pack's `data-engineer` handles: pipeline orchestration, transformation logic, data quality checks, schema evolution strategy, partitioning, incremental vs full-refresh patterns

---

## Install

```sh
sh ~/.supervisor/setup.sh --pack data
```

---

## Agents installed

### `data-engineer`
**File**: `packs/data/agents/data-engineer.md`
Implements data pipeline slices with idempotency and observability as defaults. Flags schema evolution risks and data-loss vectors before implementation. Integrates `pipeline-safety` as a mandatory gate for any task that changes how data is written or deleted.

---

## Skills installed

### `notebook-review`
**File**: `packs/data/skills/notebook-review/SKILL.md`
Audits Jupyter/Marimo notebooks for reproducibility (cell ordering, hidden state), hardcoded secrets, excessive output size, and missing environment pinning. Invoke before Stage 4 review of any notebook task.

### `pipeline-safety`
**File**: `packs/data/skills/pipeline-safety/SKILL.md`
Go/no-go gate for pipeline changes: checks idempotency, data-loss vectors, backfill strategy, and monitoring coverage. Mandatory for any task that changes write/delete logic or schema.
