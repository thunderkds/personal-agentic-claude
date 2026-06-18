---
name: deployment-checklist
description: Zero-downtime deployment checklist for Stage 5. Verifies health checks, readiness probes, rollback trigger conditions, smoke test command, and post-deploy verification before a service goes live.
---

## Role: Deployment Readiness Verifier

You verify that a deployment is safe to execute and that the team knows exactly how to roll it back if something goes wrong. Invoke at Stage 5 before any service or infrastructure change goes to production.

### Activation
```
Skill({ skill: "deployment-checklist" })
```

### Checklist

#### 1. Pre-Deploy Verification
- [ ] All Stage 4 reviews (code-review, security-review, infra-safety) have PASS status
- [ ] All acceptance criteria in the TASK_GUIDE are met
- [ ] The deployment artifact (image tag / chart version / Terraform plan) is pinned — no `latest` tags
- [ ] Staging/preview environment has been tested with the same artifact

#### 2. Health & Readiness
- [ ] Service has a `/health` or `/readiness` endpoint (or equivalent probe)
- [ ] K8s Deployment has `readinessProbe` and `livenessProbe` configured
- [ ] Minimum ready replicas (`minAvailable` PodDisruptionBudget) is set for HA services
- [ ] Rolling update strategy is configured (not `Recreate`) for zero-downtime

#### 3. Rollback Plan
- [ ] Rollback command is documented: `kubectl rollout undo` / `terraform apply` previous state / previous image tag
- [ ] Rollback has been tested in staging (at least once per service lifetime)
- [ ] Rollback trigger conditions are defined: error rate %, latency p99, health check failure count

#### 4. Smoke Test
- [ ] A smoke test command is documented in the TASK_GUIDE (e.g. `curl -f https://api.example.com/health`)
- [ ] Smoke test covers the critical path changed by this deployment
- [ ] Smoke test result is pasted into the Evidence table

#### 5. Post-Deploy Monitoring
- [ ] Deployment is monitored for ≥15 minutes after go-live before marking Stage 5 complete
- [ ] Key metrics to watch are named (error rate, latency, queue depth, etc.)
- [ ] On-call / owner is identified and available during the deploy window

### Output Format

```
## Deployment Checklist — [service / component name]

**Gate**: READY ✅ / NOT READY ❌ / CONDITIONAL ⚠️

### Blocking issues
| # | Category | Issue | Required action |
|---|----------|-------|----------------|

### Rollback command
`[exact rollback command here]`

### Rollback trigger
Roll back if: [condition — e.g. "error rate > 1% for 5 minutes"]

### Smoke test
`[exact smoke test command]`

### Passed checks
- Pinned artifact: ✅
- Health probe configured: ✅
- ...
```

### Communication Protocol
Notify: "Deployment checklist — [READY/NOT READY/CONDITIONAL]. Rollback: `[command]`. Smoke test: `[command]`."
