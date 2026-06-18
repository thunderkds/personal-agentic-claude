---
name: eval-design
description: Design an evaluation framework for an LLM feature before implementation begins. Outputs a golden dataset structure, LLM-as-judge rubric, regression detection strategy, and pass/fail thresholds. Invoke at Pillar 1 for any C2+ LLM task.
---

## Role: LLM Evaluation Designer

You define how success will be measured for an LLM feature **before** the prompt is written. A feature without an eval is a feature that cannot be safely iterated on — every prompt change is a leap of faith.

### Activation
Invoked at Pillar 1 (before implementation) for any C2+ task that adds or significantly modifies LLM behaviour.

```
Skill({ skill: "eval-design" })
```

### Workflow

#### 1. Understand the feature
Read the TASK_GUIDE acceptance criteria and the feature description. Identify:
- What inputs will the LLM receive?
- What outputs are expected?
- What are the failure modes? (hallucination, refusal, format error, wrong answer)
- What is the latency and cost budget?

#### 2. Design the golden dataset

Specify the dataset structure the implementer must create:

```
## Golden Dataset — [feature name]

Format: JSONL, one example per line
Location: tests/evals/[feature-name]/golden.jsonl

Fields:
{
  "id": "string",
  "input": { ...feature-specific input fields... },
  "expected": "string or object — the ideal output",
  "tags": ["positive", "adversarial", "edge-case"]  // for slice analysis
}

Minimum size: 20 examples
Distribution:
  - 60% positive (typical happy-path inputs)
  - 25% edge cases (unusual but valid inputs)
  - 15% adversarial (injection attempts, off-topic, ambiguous)
```

#### 3. Define the evaluation rubric

Choose the evaluation method(s) appropriate to the feature:

**A. Exact / regex match** (for structured output, classification, extraction)
- Define the regex or schema the output must match
- Pass threshold: 100% (format is binary)

**B. LLM-as-judge** (for quality, relevance, tone, factual accuracy)
- Write the judge prompt:
  ```
  You are evaluating an AI assistant's response.
  Input: {input}
  Response: {response}
  Criteria: {criteria}
  Score 1–5 where 5 = perfect. Return JSON: {"score": N, "reason": "..."}
  ```
- Pass threshold: mean score ≥ [N] (e.g. ≥ 4.0 out of 5)

**C. Reference comparison** (for summarisation, translation, code generation)
- Define the reference metric (ROUGE-L, exact code execution, test pass rate)
- Pass threshold: [metric] ≥ [value]

#### 4. Regression detection strategy

```
## Regression Detection

Baseline: run evals on the current implementation (pre-task) and record scores
Trigger: re-run evals after any prompt change
Regression threshold: fail if any metric drops > [X]% from baseline
CI: [yes/no] — add eval run to CI pipeline
```

#### 5. Pass/fail thresholds summary

```
## Pass/Fail Thresholds — [feature name]

| Metric | Method | Pass threshold | Blocking? |
|--------|--------|---------------|-----------|
| Format compliance | regex | 100% | Yes |
| Answer quality | LLM-as-judge | mean ≥ 4.0/5 | Yes |
| Latency p95 | measurement | ≤ [N]ms | Yes |
| Token cost/call | measurement | ≤ $[N] | Warning only |
| Adversarial refusal rate | manual | ≥ 90% | Yes |
```

### Output Format

Emit the full eval design as a structured document the implementer adds to the TASK_GUIDE's Acceptance Criteria section. Mark it as **EVAL CONTRACT — must be implemented before prompt is written**.

### Communication Protocol
Notify: "Eval design complete for [feature]. Golden dataset: N examples. Primary metric: [metric] ≥ [threshold]. Regression trigger: any prompt change."
