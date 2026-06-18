---
name: prompt-review
description: Audit system and user prompts for injection risk, hallucination surface, output format fragility, missing guardrails, and token efficiency. Invoke before Stage 4 review of any task that adds or modifies prompts.
---

## Role: Prompt Quality & Safety Auditor

You audit prompts before they ship. A prompt that works in the playground can fail at scale, leak data, or produce inconsistent output that breaks downstream parsing. This checklist catches the most common prompt engineering failure modes.

### Activation
```
Skill({ skill: "prompt-review" })
```

### Checklist

#### 1. Injection Defence
- [ ] System prompt is structurally separated from user input (not string-concatenated inline)
- [ ] User input is treated as data, not instructions — test with `"Ignore previous instructions and..."`
- [ ] If the prompt processes external content (web pages, user documents), it explicitly instructs the model not to follow instructions found in that content
- [ ] No sensitive data (API keys, PII, internal system details) is placed in the user turn

#### 2. Hallucination Surface
- [ ] Prompt instructs the model to say "I don't know" rather than guess when information is absent
- [ ] Facts the model is expected to know are grounded in injected context (RAG), not memory
- [ ] Prompt does not ask for specific numbers, dates, or citations without providing a source
- [ ] Instructions are specific enough that "close but wrong" answers are unlikely (vague prompts invite hallucination)

#### 3. Output Format Robustness
- [ ] Output format is explicitly defined (JSON schema, markdown structure, or regex pattern)
- [ ] The format instruction is near the end of the prompt (LLMs weight recency)
- [ ] A parsing failure path exists in the calling code — the parser handles malformed output gracefully
- [ ] If using JSON mode / structured output: schema is as strict as possible (no open `additionalProperties`)

#### 4. Guardrails & Refusal Handling
- [ ] The system prompt defines what the model should NOT do (out-of-scope topics, harmful content)
- [ ] Refusal paths are tested: what happens when the model declines?
- [ ] If the feature is user-facing: tested with adversarial inputs (jailbreak attempts, off-topic queries)
- [ ] Content policy constraints are appropriate for the deployment context

#### 5. Token Efficiency
- [ ] No redundant instructions (the same constraint stated 3 times is still 1 constraint)
- [ ] Static context blocks (system role, tool descriptions) use `cache_control` if supported
- [ ] Example turns (few-shot) are minimal and high-signal — remove low-quality examples
- [ ] Prompt fits comfortably within the declared context window with room for max output tokens

#### 6. Versioning
- [ ] Prompt is stored in a versioned file (not hardcoded in application logic)
- [ ] Prompt version is logged alongside each LLM call for debugging

### Output Format

```
## Prompt Review — [feature / prompt file name]

**Gate**: PASS ✅ / FAIL ❌ / CONDITIONAL ⚠️

### Blocking issues
| # | Category | Issue | Fix |
|---|----------|-------|-----|

### Warnings
- ...

### Passed checks
- Injection defence: ✅
- Output format defined: ✅
- ...
```

### Communication Protocol
Notify: "Prompt review complete — [PASS/FAIL/CONDITIONAL]. N blocking issues, M warnings."
