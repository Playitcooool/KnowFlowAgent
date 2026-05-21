# Eval Set Guide

`eval_set/` stores lightweight evaluation examples for QA quality checks.

## Local Rules

- Keep files JSON unless introducing an explicit evaluator format.
- Each example should include the question, expected source files, and expected answer keywords.
- Expected files should use knowledge-base relative paths such as `finance/reimbursement_policy.md`.
- Avoid secrets or private source text in eval examples.

