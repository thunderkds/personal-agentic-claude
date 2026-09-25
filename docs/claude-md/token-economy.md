# Token economy: terse but verbatim

Replies are kept short for focus, not for a claimed saving. Terse never means changed: a
paraphrased error is a wrong error.

## Verbatim-preserve list

Never paraphrase, shorten or reflow these in a reply or report — quote them exactly:

- code
- exact error text
- file paths
- commands
- security warnings

## Reports point, Evidence carries

A sub-agent's final report must point to evidence by path:line in `TASK_REVIEW_Txxx.md` instead of
pasting logs. The Evidence table still carries full output: Hard-Stop Gate 5 is unchanged, and
pasted test output is what the Supervisor checks before a task moves to Done.

## Measuring a token claim

Any claim that something saves or costs tokens is measured with `scripts/token_meter.py`
(DDR-0009), never estimated by eye.
