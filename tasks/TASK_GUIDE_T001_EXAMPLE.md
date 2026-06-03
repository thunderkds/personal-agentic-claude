# TASK_GUIDE — T001: Reject login with invalid email format

> **This is a worked EXAMPLE** showing a filled-in Evaluation & Acceptance block.
> Delete or ignore it in real projects — real guides are generated from
> `templates/TASK_GUIDE_template.md` at Stage 2.

**Date**: 2026-06-03
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: Backend-Implementer
**Agent guide**: `.claude/agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:
1. Read `PROJECT_SPEC.md`
2. Read `memory/MEMORY.md`
3. Read this file completely
4. Read `.claude/agents/backend.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `.claude/agents/general-agent-template.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

"The login endpoint should not accept obviously malformed emails — right now `POST /login`
with `notanemail` reaches the password check and leaks timing. Validate the email format first."

**Restated intent:**
> Malformed-email login attempts must be rejected up front with a generic `400`, before any user
> lookup or password work, so the endpoint neither wastes work nor leaks account existence/timing.

**Out of scope:**
- Changing the password hashing or timing-equalization logic
- Rate-limiting / lockout on repeated failures

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (confirmed by Supervisor)
- [x] Domain terms align with `PROJECT_SPEC.md` glossary ("malformed" = fails `is_valid_email`)
- [x] Every Acceptance Criterion traces to a line in the Requirement

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | Well-formed email + correct password still logs in (`200`) | "validate the email format first" must not break valid logins |
| 2 | Malformed email rejected with `400` before any password/DB work | "reaches the password check and leaks timing" |
| 3 | Rejection message identical for existing vs non-existent accounts | "leaks timing" → no account enumeration |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> Success Criteria + Verification Command were filled by the Supervisor **before** the agent started.
> Evidence was filled by the reviewer at Stage 4/5.

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | `POST /login` `{email:"alice@acme.com", password:"<correct>"}` | `200` + session token | automated test |
| 2 | `POST /login` `{email:"notanemail", password:"x"}` | `400 {"error":"invalid email format"}`, no DB query | automated test |
| 3 | `POST /login` `{email:"", password:"x"}` | `400`, same generic message | automated test |
| 4 | malformed email for a **non-existent** account | identical `400` to case 2 (no account enumeration) | automated test |

### Verification Command (exact, runnable)

```bash
pytest tests/test_login_validation.py -q
```

### Evidence (filled by reviewer at Stage 4/5)

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| Verification command run | ☑ pass | `4 passed in 0.41s` |
| Negative cases hold | ☑ pass | cases 2–4 return `400` before `db.users.find` (asserted via mock call-count == 0) |
| `verify` skill — works in running app | ☑ pass | live `curl -d '{"email":"notanemail"...}'` → `400 {"error":"invalid email format"}`; valid login → `200` + token |
| Full smoke suite still green (no regression) | ☑ pass | `pytest -q` → `87 passed` |

---

## Approach

Add a format check at the top of the `/login` handler, before the user lookup. Reuse the existing
`is_valid_email()` helper in `app/validators.py` (already used by signup) — do **not** introduce a
new regex. Return the same generic `400` for every malformed/empty case so the response can't be
used to enumerate accounts.

---

## Edge Case Checklist

- [x] Empty string email
- [x] Whitespace-only email
- [x] Valid format but non-existent account → must look identical to malformed (no enumeration)
- [x] Leading/trailing spaces trimmed before validation

---

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `app/routes/auth.py` | Add `is_valid_email()` guard at top of `login()` handler |
| `tests/test_login_validation.py` | New test file covering the 4 success criteria |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `app/auth/password.py` | Hashing/timing logic is out of scope — surgical change only |
| `app/validators.py` | Reuse existing helper; do not modify the shared validator |

---

## Test Plan

Unit tests in `tests/test_login_validation.py` cover all 4 success criteria, asserting both the
status code and (via a mocked DB) that no user lookup occurs on malformed input. Manual `verify`
confirms the running app behaves the same.

---

## Completion Checklist

- [x] Implementation done
- [x] Self-review: `Skill({ skill: "code-review" })` run
- [x] Security review: `Skill({ skill: "security-review" })` run (Medium risk — auth path)
- [x] Lint passes
- [x] Tests pass
- [x] `Skill({ skill: "verify" })` run — feature confirmed working in running app
- [ ] `docs/legacy/` updated (N/A — greenfield)
- [x] `memory/MEMORY.md` updated (noted: reuse `is_valid_email`, generic 400 to prevent enumeration)
- [x] Supervisor notified: task ready for Stage 4 review
