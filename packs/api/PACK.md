# PACK.md — API
**Pack**: `api`
**Domain**: REST/gRPC services, OpenAPI specs, GraphQL, auth flows, SDK design, API versioning
**Core framework version tested**: 1.14+

---

## When to use this pack

Select when the project's primary deliverable is a public or internal API contract — not just an app that has a backend. The core `backend-developer` implements business logic; this pack adds the API-design mindset: contract-before-code, versioning strategy, backward-compatibility invariants, and consumer-driven testing.

**Select this pack when your project involves:**
- Designing or evolving a public REST or gRPC API
- OpenAPI / Swagger spec as a first-class deliverable
- GraphQL schema design
- Auth flows (OAuth2, OIDC, API keys, JWTs) as a primary concern
- SDK generation or consumer-driven contract testing (Pact)

**Do NOT select if:** the project has a backend API purely as an internal implementation detail with no external consumers — the core `backend-developer` is sufficient.

---

## What this pack adds

| Resource | Type | Purpose |
|----------|------|---------|
| `api-designer` | Agent | Contract-first API implementer: versioning, backward-compat, consumer-driven design |
| `contract-review` | Skill | Reviews OpenAPI/gRPC specs for breaking changes, missing error codes, auth gaps |
| `auth-checklist` | Skill | OAuth2/OIDC flow audit, token expiry, PKCE, scope minimisation, session fixation |

**Boundary from core agents:**
- Core `backend-developer` handles: business logic, data access, internal service-to-service calls
- This pack's `api-designer` handles: public API contract design, OpenAPI spec authoring, versioning strategy, breaking-change detection, SDK ergonomics, consumer-driven test contracts

---

## Install

```sh
sh ~/.supervisor/setup.sh --pack api
```

---

## Agents installed

### `api-designer`
**File**: `packs/api/agents/api-designer.md`
Implements API slices contract-first: the OpenAPI / proto spec is written and reviewed before the implementation begins. Flags breaking changes before they ship and maintains backward compatibility as a hard invariant.

---

## Skills installed

### `contract-review`
**File**: `packs/api/skills/contract-review/SKILL.md`
Reviews OpenAPI/gRPC contract changes for breaking changes, missing status codes, inconsistent naming, auth gaps, and pagination correctness. Invoke before Stage 4 review of any task that modifies an API contract.

### `auth-checklist`
**File**: `packs/api/skills/auth-checklist/SKILL.md`
Audits OAuth2/OIDC flows, JWT handling, API key management, token expiry, PKCE, and scope minimisation. Invoke for any task that adds or modifies authentication or authorisation logic.
