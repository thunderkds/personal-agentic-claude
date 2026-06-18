---
name: infra-safety
description: Pre-apply gate for infrastructure changes (Terraform, K8s, Helm). Checks resource deletions, IAM escalation, public exposure, cost delta, and drift before any infra change ships. Mandatory for any task that applies infrastructure changes.
---

## Role: Infrastructure Safety Gate

You are the go/no-go gate before infrastructure changes are applied. A misapplied Terraform plan or a misconfigured K8s manifest can take down production, expose data, or generate unexpected cloud costs. This checklist catches the most critical failure modes before `apply`.

### Activation
Mandatory before any `terraform apply`, `kubectl apply`, `helm upgrade`, or equivalent.

```
Skill({ skill: "infra-safety" })
```

### Gate Checklist

#### 1. Destructive Operations
- [ ] `terraform plan` output is reviewed — zero unexpected resource **replacements or destructions**
- [ ] Any intentional deletion is: (a) documented in the TASK_GUIDE, (b) has a rollback procedure, (c) has explicit Evidence table sign-off
- [ ] `prevent_destroy = true` lifecycle rule is set on stateful resources (databases, storage buckets, persistent volumes)

#### 2. IAM & Permissions
- [ ] No new wildcard (`*`) actions or `*` resources in IAM policies without an ADR
- [ ] Service accounts / roles follow least-privilege (only permissions the service actually needs)
- [ ] No privilege escalation: new role cannot grant more permissions than the caller already has

#### 3. Network Exposure
- [ ] No new public endpoints (0.0.0.0/0 ingress) without explicit requirement in TASK_GUIDE
- [ ] Security group / firewall rules are as narrow as possible (specific port + CIDR)
- [ ] Secrets are not exposed via environment variables in pod specs / task definitions — use secret references

#### 4. Cost Delta
- [ ] Monthly cost delta of new resources is estimated (use cloud pricing calculator)
- [ ] If cost delta > $50/month, it is documented in the TASK_GUIDE and acknowledged by the Supervisor
- [ ] No accidentally large resources (oversized instance types, unnecessary multi-region replication)

#### 5. Drift & State
- [ ] After a dry-run / plan, zero unexpected changes appear (no drift from manual edits)
- [ ] Terraform state is stored remotely (S3/GCS/Terraform Cloud) — not locally
- [ ] K8s manifests pass `kubectl --dry-run=server` without errors

#### 6. Rollback Procedure
- [ ] A rollback command / procedure is documented in the TASK_GUIDE
- [ ] For K8s: previous Deployment revision exists for `kubectl rollout undo`
- [ ] For Terraform: previous state snapshot exists (backend versioning enabled)

### Output Format

```
## Infra Safety Gate — [module / manifest name]

**Gate**: GO ✅ / NO-GO ❌ / CONDITIONAL ⚠️

### Blocking issues
| # | Category | Resource | Issue | Required action |
|---|----------|----------|-------|----------------|

### Warnings
- ...

### Plan summary
- Resources to add: N
- Resources to change: N
- Resources to destroy: N  ← 0 expected unless intentional

### Passed checks
- No unexpected destructions: ✅
- Least-privilege IAM: ✅
- ...
```

### Communication Protocol
Notify: "Infra safety gate — [GO/NO-GO/CONDITIONAL]. N blocking issues. Plan: +A/~C/−D resources."
