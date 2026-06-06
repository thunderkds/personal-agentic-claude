# RUNBOOK — [Service / Component Name]
**Last updated**: [YYYY-MM-DD]

> Operational runbook: how to deploy, verify, and recover this service. Written/appended by the `ship` skill after Stage 5 verification, and kept current by whoever last touched the deploy path. This is the document an operator opens at 3am — every command must be copy-pasteable and every check must have a pass condition.

---

## Service Identity

- **Name**: [service / component]
- **Repo**: [repo URL or local path]
- **Deployment target**: [exact environment / URL — mirrors PROJECT_SPEC.md]
- **Tech**: [language / framework / runtime]
- **Owner / on-call**: [name or rotation]

---

## Deploy Procedure

Ordered steps to ship a release. Migrations before app. Commands copy-pasteable.

1. **Pre-deploy checks**: clean working tree, correct branch, Stage 5 evidence green, smoke suite passing.
2. [ordered deploy step + exact command]
3. [next step …]
4. **Post-deploy health check**: `[exact command / URL probe]` → pass condition: `[concrete expected result]`.

> If the deploy command is unknown, leave `TODO: confirm with operator` — never invent it.

---

## Rollback Procedure

- **Trigger conditions**: [health check fails / error-rate spike / failed migration / …]
- **Reverse steps** (in order):
  1. [exact command to restore previous known-good state]
  2. [down-migration / revert tag-image / …]
- **Verify rollback**: [health check command] → [expected result].

---

## Health Checks & Dashboards

| Check | Command / URL | Pass condition |
|-------|---------------|----------------|
| [liveness] | `[command]` | [expected] |
| [readiness] | `[url]` | [expected] |

- **Dashboards**: [links to logs / metrics / monitoring]

---

## Common Failure Modes & Remediation

| Symptom | Likely cause | Remediation |
|---------|-------------|-------------|
| [observed symptom] | [root cause] | [exact fix steps] |

---

## On-Call / Escalation

1. **First responder**: [name / rotation / channel]
2. **Escalate to**: [next tier] if [condition / time threshold]
3. **Comms**: [where to post incident status]

---

## Release Log

| Version / Tag | Date | Scope (Task IDs) | Deployer | Outcome |
|---------------|------|------------------|----------|---------|
| [v / tag] | [YYYY-MM-DD] | [T001, T002 …] | [name] | Success / Rolled back / Partial |
