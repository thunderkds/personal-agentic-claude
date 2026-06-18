---
name: contract-review
description: Review OpenAPI/gRPC contract changes for breaking changes, missing status codes, inconsistent naming, auth gaps, and pagination correctness. Invoke before Stage 4 review of any task that modifies an API contract.
---

## Role: API Contract Reviewer

You review API contract changes (OpenAPI YAML, proto files, GraphQL schema) before they ship. A breaking change that reaches a consumer is an incident — this checklist catches them at the diff stage.

### Activation
```
Skill({ skill: "contract-review" })
```

### Checklist

#### 1. Breaking Change Detection
These changes are **always breaking** — require a version bump or a deprecation period:
- [ ] No field or parameter renamed
- [ ] No field or parameter removed
- [ ] No field type changed to an incompatible type
- [ ] No endpoint path or HTTP method changed
- [ ] No required field added to an existing response (consumers may not handle unknown fields)
- [ ] No auth requirement added to a previously public endpoint
- [ ] No enum value removed

These changes are **safe** (additive):
- ✅ New optional field in request or response
- ✅ New endpoint
- ✅ New optional query parameter
- ✅ New enum value (if consumers use `default` / unknown handling)

#### 2. Status Code Coverage
- [ ] Every endpoint documents: 400 (bad input), 401 (unauthenticated), 403 (unauthorised), 404 (not found), 500 (server error)
- [ ] Creation endpoints document: 409 (conflict) if duplicate detection exists
- [ ] Mutation endpoints document: 422 (unprocessable) if business validation can fail
- [ ] No undocumented status codes returned by the implementation

#### 3. Auth & Security
- [ ] Every endpoint explicitly declares its auth requirement (Bearer, API key, public)
- [ ] No endpoint is accidentally unauthenticated
- [ ] Scopes / permissions required are documented on each endpoint
- [ ] Sensitive response fields (tokens, PII) are flagged for the `auth-checklist` skill

#### 4. Naming Consistency
- [ ] Resource names, field names, and parameter names follow the project convention (camelCase / snake_case — check `PROJECT_SPEC.md`)
- [ ] No abbreviations introduced without a glossary entry
- [ ] Error codes follow the project's error schema

#### 5. Pagination & Lists
- [ ] All list endpoints are paginated (no unbounded list returns)
- [ ] Pagination follows the project's declared style (cursor / offset / keyset)
- [ ] `total_count` / `has_more` / `next_cursor` fields are present as required by the project convention

#### 6. Versioning
- [ ] Breaking changes are in a new version prefix (`/v2/`) or deprecated with a `Sunset` header
- [ ] Deprecation timeline is documented (sunset date in the spec description)

### Output Format

```
## Contract Review — [spec file or endpoint range]

**Gate**: PASS ✅ / FAIL ❌ / CONDITIONAL ⚠️

### Breaking changes detected
| # | Endpoint | Change | Action required |
|---|----------|--------|----------------|

### Missing status codes
| # | Endpoint | Missing code | Reason |
|---|----------|-------------|--------|

### Warnings
- ...

### Passed checks
- No breaking changes: ✅
- Auth on all endpoints: ✅
- ...
```

### Communication Protocol
Notify: "Contract review complete — [PASS/FAIL/CONDITIONAL]. N breaking changes, M missing status codes."
