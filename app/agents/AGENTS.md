# Agents Package Guide

`app/agents/` contains small, swappable decision components used by `KnowFlowWorkflow`.

## Components

- `query_router.py`: selects target knowledge-base folders using root/local indexes and manifest metadata.
- `file_router.py`: narrows selected folders to likely Markdown files from manifest metadata.
- `query_rewriter.py`: generates keyword and synonym variants for grep retrieval.
- `answer_agent.py`: composes grounded answers from ranked evidence and emits citations.
- `verifier.py`: decides whether the answer is sufficiently supported by retrieved evidence.

## Local Rules

- Keep these classes deterministic by default. If a hosted model is added later, hide it behind the same class boundary or a clearly named adapter.
- Preserve retry-aware behavior. Broader search should happen at higher retry levels, not by making first-pass routing indiscriminate.
- Answer generation must cite evidence with `Citation` objects and should not invent facts outside retrieved evidence.
- Verification should use evidence coverage and citations as support signals.
- Update tests when routing, confidence, or answerability thresholds change.

