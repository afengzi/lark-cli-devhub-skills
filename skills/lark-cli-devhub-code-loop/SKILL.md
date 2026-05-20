---
name: lark-cli-devhub-code-loop
description: Use when an AI coding agent is fixing or investigating a bug and should search old Dev Hub records, write Bugfix and AI Run evidence, and leave receipt or outbox proof.
metadata:
  requires:
    bins: ["python3", "lark-cli", "git"]
---

# Lark CLI Dev Hub Code Loop

Use this workflow when work involves a bug, regression, incident, risky refactor, or repeated investigation path.

## Before Fixing

1. Extract project, area, symptom, error keywords, and relevant file paths.
2. Run `devhub.py search` with those terms.
3. Read Project Facts, Pitfalls, Playbooks, Bugfixes, AI Runs, Releases, Decisions, Tasks, Artifacts, and Areas when present.
4. Read the relevant Wiki template shape for the record you will write, especially Bugfix, AI Run, Project Fact, or Artifact. If it cannot be read, record that gap in the AI Run or outbox.
5. Let old records guide the investigation only when they match current evidence.

## After Fixing

1. Write `record-bugfix` for the root cause, fix, verification, and regression risk. Add `--wiki` when the fix needs a human-readable retrospective in Wiki.
2. Write `record-ai-run` for what the agent did and what evidence it checked.
3. Write `record-project-fact` if the work changes the current truth or retires an old path. Add `--wiki` when the current truth should also update the project Wiki.
4. Write `record-artifact` for linked docs, diagrams, PRs, commits, or screenshots.
5. If architecture, module boundaries, task flow, PR flow, or investigation path changed, update the relevant project map and reusable global map when appropriate, or leave an outbox/explicit note.
6. Mention receipt paths or outbox paths in the final work summary.

Base is the default write target. Wiki writeback is explicit with `--wiki` so small fixes do not create noisy pages.

## Reliability

No receipt means no confirmed Feishu/Lark write. Failed writes must remain in `.devhub/outbox/`.
