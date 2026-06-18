# PACK.md — DevOps
**Pack**: `devops`
**Domain**: Infrastructure-as-code, containers, orchestration, CI/CD, secrets management
**Core framework version tested**: 1.14+

---

## When to use this pack

Select when the project's primary deliverable is infrastructure, deployment automation, or platform engineering. The core agents can write a Dockerfile or a GitHub Actions step as part of a feature task; this pack adds the infra-as-code mindset: idempotency, blast-radius of infra changes, rollback-first thinking, and secrets hygiene.

**Select this pack when your project involves:**
- Terraform, Pulumi, or CDK infrastructure definitions
- Kubernetes manifests, Helm charts, or Kustomize overlays
- Docker / Docker Compose service definitions as primary deliverables
- CI/CD pipeline authoring (GitHub Actions, GitLab CI, Buildkite, CircleCI)
- Platform engineering: internal developer platforms, GitOps workflows, ArgoCD

**Do NOT select if:** infra files are a small supporting concern for an app project — the core `backend-developer` can handle a Dockerfile and a GitHub Actions workflow without this pack.

---

## What this pack adds

| Resource | Type | Purpose |
|----------|------|---------|
| `devops-engineer` | Agent | Infra-as-code implementer: idempotency, drift detection, rollback-first |
| `infra-safety` | Skill | Pre-apply checklist for Terraform/K8s: resource deletion guard, cost estimate |
| `deployment-checklist` | Skill | Zero-downtime deploy checklist, health-check verification, rollback triggers |

**Boundary from core agents:**
- Core `backend-developer` handles: application Dockerfiles, simple CI steps, environment variables
- This pack's `devops-engineer` handles: infrastructure definitions, multi-service orchestration, platform-level concerns, secrets management architecture, cost/quota awareness

---

## Install

```sh
sh ~/.supervisor/setup.sh --pack devops
```

---

## Agents installed

### `devops-engineer`
**File**: `packs/devops/agents/devops-engineer.md`
Implements infrastructure slices with idempotency and rollback as defaults. Runs `infra-safety` before any `terraform apply` / `kubectl apply` equivalent. Never introduces a resource deletion or cost increase without explicit Evidence table sign-off.

---

## Skills installed

### `infra-safety`
**File**: `packs/devops/skills/infra-safety/SKILL.md`
Pre-apply gate for Terraform/K8s changes: checks for resource deletions, IAM escalations, public exposure, cost delta, and drift. Invoke before any infrastructure change reaches Stage 5.

### `deployment-checklist`
**File**: `packs/devops/skills/deployment-checklist/SKILL.md`
Zero-downtime deployment checklist: health checks, readiness probes, rollback trigger conditions, smoke test command, and post-deploy verification. Invoke as part of Stage 5 for any infra or service deployment task.
