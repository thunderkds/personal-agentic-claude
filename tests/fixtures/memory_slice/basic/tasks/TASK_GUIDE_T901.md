# TASK_GUIDE — T901: fixture guide for memory_slice.py (SC1)
**Complexity Level**: C1

## Dependencies & Reachability

**Depends on**: T122 — the MANIFEST `!` fix this task builds on

**Entry point**: `scripts/validate.sh`

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `scripts/validate.sh` | Edit — mentions `lib/other.sh` in this column, which is prose, not a key |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `tests/fixtures/transcripts/**` | Fixture data |
