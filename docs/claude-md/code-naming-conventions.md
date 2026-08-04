# Code Naming Conventions

> Extracted from `CLAUDE.md` — full naming table. See `CLAUDE.md` for the pointer back to this file.

Mandatory for all sub-agents (Backend, Frontend, Common-Infrastructure, QA) when writing or reviewing code. Applies to source code only — not skill/agent/infra naming.

| Element | Rule | Example |
|---|---|---|
| Function / method | Verb or verb phrase — names an action | `calculateTotal()`, `fetchUser()`, `validateInput()` |
| Boolean function / variable | `is` / `has` / `can` / `should` prefix | `isValid`, `hasPermission`, `canRetry` |
| Class / interface / type | Noun or noun phrase — names a thing | `UserService`, `OrderRepository`, `PaymentRequest` |
| Variable | Descriptive noun, no abbreviations | `userCount` not `uc`, `retryLimit` not `rl` |
| Constant | `UPPER_SNAKE_CASE`, noun | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT_MS` |
| File name | Matches its primary export's name and casing convention (per project/language norm) | `UserService.ts` exports `UserService` |
| REST endpoint | Plural noun resource path; the HTTP verb conveys the action, not the URL | `GET /users`, `POST /orders`, not `GET /getUsers` |
| Event / message name | Past-tense verb — states what happened | `UserCreated`, `OrderShipped` |
| Error / exception class | Noun ending in `Error`/`Exception` | `ValidationError`, `NotFoundException` |
| Private / internal member | Language-native privacy marker | `_cache` (Python), `#privateField` (JS), lowercase-unexported (Go) |
| Test name | States behavior + condition, not implementation | `should_return_error_when_input_invalid`, `it("rejects an expired token")` |
| Frontend component | PascalCase noun | `UserCard`, `OrderSummary` |
| Frontend hook (React) | `use` + noun/verb phrase | `useAuth()`, `useDebouncedValue()` |
| DB table | Plural, `snake_case` | `orders`, `user_sessions` |
| DB column | Singular, `snake_case`, no table-name repetition | `created_at` not `order_created_at` in the `orders` table |
| Environment variable | `UPPER_SNAKE_CASE`, prefixed by service/context | `AUTH_SERVICE_TIMEOUT_MS` |
| Directory / package / module | Lowercase, `kebab-case` or `snake_case` per language norm | `user-service/`, `payment_utils/` |
| Enum type | Noun, PascalCase | `OrderStatus`, `UserRole` |
| Enum member | PascalCase (or `UPPER_SNAKE_CASE` if language convention, e.g. Python) | `OrderStatus.Shipped`, `Status.ACTIVE` |
| Generic type parameter | Single uppercase letter, or `T`-prefixed descriptive name for multiples | `T`, `TKey`, `TValue` |

**Enforcement**: reviewed at Stage 4 `code-review` as a style-consistency check. Existing project/language conventions (e.g. an established linter config) take precedence over this table where they conflict — match existing style per the Surgical Changes principle.
