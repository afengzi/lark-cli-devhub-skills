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

## Reliability

A GitHub event is only a trigger. The workflow succeeds only when a receipt exists. On failure, keep the outbox item and report its path.

## Safe Default

Run in draft or shadow mode until the project confirms the mapping is useful.
