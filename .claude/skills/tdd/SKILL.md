---
name: tdd
description: Test-driven development with a red-green-refactor loop, one vertical slice at a time. Use during Stage 3 implementation when a sub-agent builds a feature or fixes a bug test-first. Directly operationalizes the Karpathy Task Transformation Table.
---

## Role: Test-First Implementer

You build features and fix bugs through a disciplined **red → green → refactor** loop. Tests verify behavior through public interfaces, never implementation details — code can change entirely; tests shouldn't.

### Karpathy Operational Commands (Specific Overrides)
- **Goal-Driven Execution**: This skill *is* the Task Transformation Table. "Add validation" → write a failing test for invalid input, then make it pass. Never write code without a failing test first.
- **Simplicity First**: Write only enough code to pass the current test. No speculative features, no anticipating future tests.
- **Surgical Changes**: One test → one implementation → repeat. Never refactor while RED.

### Anti-Pattern: Horizontal Slices
**DO NOT** write all tests first, then all implementation. Bulk-written tests verify *imagined* behavior and test the *shape* of things, not user-facing behavior.

```
WRONG (horizontal):  RED: test1..test5   GREEN: impl1..impl5
RIGHT (vertical):    test1→impl1, test2→impl2, test3→impl3, ...
```

### Workflow

#### 1. Planning
Read `PROJECT_SPEC.md` and the task's `tasks/TASK_GUIDE_Txxx.md`. Use the project's domain vocabulary so test names match the project's language; respect any ADRs in the area you touch.
- [ ] Confirm the public interface changes needed
- [ ] List the behaviors to test (not implementation steps) and prioritize critical paths
- [ ] Get Supervisor/user approval on the plan
- **You can't test everything** — focus on critical paths and complex logic.

#### 2. Tracer Bullet
Write ONE test for the first behavior → it fails (RED) → write minimal code → it passes (GREEN). This proves the path works end-to-end.

#### 3. Incremental Loop
For each remaining behavior: RED (next test fails) → GREEN (minimal code passes). One test at a time; only enough code to pass; don't anticipate future tests.

#### 4. Refactor (only when GREEN)
After all tests pass: extract duplication, deepen modules (small interface / deep implementation), apply SOLID where natural. Run tests after each refactor step. **Never refactor while RED.**

### Checklist Per Cycle
```
[ ] Test describes behavior, not implementation
[ ] Test uses the public interface only
[ ] Test would survive an internal refactor
[ ] Code is minimal for this test
[ ] No speculative features added
```

### Communication Protocol
- **Default Notification**: "TDD complete for [Task ID]. N behaviors covered via vertical slices; all green. Refactors applied: [summary]."
