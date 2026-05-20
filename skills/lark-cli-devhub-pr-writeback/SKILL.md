---
name: lark-cli-devhub-pr-writeback
description: Use when GitHub PR or CI events should write AI Runs, Decisions, Bugfix candidates, Tasks, or Releases into Feishu/Lark through Dev Hub.
metadata:
  requires:
    bins: ["python3", "lark-cli", "git"]
---

# Lark CLI Dev Hub PR Writeback

Use this workflow for PR and CI event writeback.

## Event Map

- PR created or updated: write `AI Runs`.
- PR reviewed: write `Decisions` or `Bugfixes`.
- PR merged to the default branch: write `Releases`.
- CI failed: write a Bugfix candidate or `Tasks`.

Before writing each record, use the matching template shape when available:

- AI Run: local `templates/wiki/ai-run.md`.
- Decision: local `templates/wiki/decision.md`.
- Bugfix: local `templates/wiki/bugfix-retro.md`.
- Release: local `templates/wiki/release-writeback.md`.
- PR workflow changes: update `PR 写回流程图` in the project Maps folder, and the global Maps folder when the change is reusable.

If a local template cannot be read, include that gap in the AI Run or outbox. Do not silently produce a minimal record that omits the expected evidence sections. Do not write blank template content into Feishu Wiki.

## Reliability

A GitHub event is only a trigger. The workflow succeeds only when a receipt exists. On failure, keep the outbox item and report its path.

## Safe Default

Run in draft or shadow mode until the project confirms the mapping is useful.
