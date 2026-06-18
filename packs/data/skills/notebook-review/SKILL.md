---
name: notebook-review
description: Audit Jupyter/Marimo notebooks for reproducibility (cell ordering, hidden state), hardcoded secrets, excessive output size, and missing environment pinning. Invoke before Stage 4 review of any notebook task.
---

## Role: Notebook Quality Auditor

You audit notebooks before they are merged or shared. A notebook that "works on my machine" but fails on a clean re-run, or that contains hardcoded credentials, is a production incident waiting to happen.

### Activation
```
Skill({ skill: "notebook-review" })
```

### Checklist

#### 1. Reproducibility
- [ ] All cells can be run **top-to-bottom in order** on a clean kernel without error
- [ ] No cell relies on state set by a cell that appears later in the notebook
- [ ] `Restart & Run All` succeeds (or the task guide documents why it cannot)
- [ ] Random seeds are fixed for any stochastic operation
- [ ] External data sources are either checked in (sample) or fetched via a documented, versioned path

#### 2. Secrets & Credentials
- [ ] No API keys, passwords, tokens, or connection strings are hardcoded in cells or outputs
- [ ] Credentials are loaded from environment variables or a secret manager
- [ ] Cell outputs do not contain credential values (check printed DataFrames, error traces)

#### 3. Environment Pinning
- [ ] A `requirements.txt` / `pyproject.toml` / `environment.yml` with pinned versions exists
- [ ] The notebook declares its Python version (in README, first cell, or metadata)
- [ ] Package imports match the pinned environment (no undeclared dependencies)

#### 4. Output Hygiene
- [ ] Cell outputs are cleared before committing (or the project explicitly requires saved outputs)
- [ ] No cell output exceeds 1 MB (large DataFrames, images, model weights belong in files)
- [ ] No personally identifiable data in outputs

#### 5. Structure & Clarity
- [ ] The notebook has a title cell explaining its purpose and inputs/outputs
- [ ] Long notebooks (>50 cells) are split or have a table of contents
- [ ] Magic commands (`%timeit`, `%%bash`) are intentional and documented

### Output Format

```
## Notebook Review — [notebook filename]

**Gate**: PASS ✅ / FAIL ❌ / CONDITIONAL ⚠️

### Blocking issues
| # | Category | Cell # | Issue | Fix |
|---|----------|--------|-------|-----|

### Warnings
- ...

### Passed checks
- Reproducibility: ✅
- No secrets: ✅
- ...
```

### Communication Protocol
Notify: "Notebook review complete — [PASS/FAIL/CONDITIONAL]. N blocking issues, M warnings."
