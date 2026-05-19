---
name: lark-cli-devhub-taskflow
description: Use when turning development work into Feishu/Lark tasks through lark-cli or feishu-cli, including task lists, bug queues, status updates, blocked work, next actions, or task-linked Dev Hub records.
metadata:
  requires:
    bins: ["lark-cli"]
---

# Lark CLI Dev Hub Taskflow

Use Feishu Tasks for current work state. Use Base `Tasks` as the AI-readable task index and relation anchor. Use Bugfixes, Decisions, Releases, and AI Runs for durable evidence.

Discovery aliases: `feishu-cli task`, `飞书任务`, `lark-cli task`, `Lark Tasks`, `bug queue`, `developer task list`.

## Task Lists

Recommended task lists:

- `Dev Hub Inbox`
- `Current Sprint`
- `Bug Queue`
- `Release Checklist`
- `Backlog`

## Status Discipline

Keep status small and explicit:

- `Inbox`: captured but not shaped.
- `Ready`: clear next action exists.
- `Doing`: actively being changed.
- `Blocked`: needs user, external system, or missing permission.
- `Review`: implementation done, needs review.
- `Verify`: needs test/manual verification.
- `Done`: verified enough for the agreed scope.

## Linkage

When a task results in a fix:

- Update the Feishu task status.
- Write a `Bugfix` record when code changed to fix a bug.
- Write an `AI Run` record when an AI agent did meaningful investigation or implementation.
- Store the Feishu task URL and GUID in Base `Tasks` when a native task exists.
- Put cross-record links in `Record Relations` through text hints such as `Related Task`, `Related Bugfix`, or `Related Records`. Keep task tables lightweight.

## Work Loop

Before implementation:

1. Search Base `Tasks` and native Feishu Tasks for an existing task.
2. If a suitable task exists, update Base `Tasks.Status` to `Doing` and keep the native task URL/GUID.
3. If no task exists and the work is worth tracking, create a Feishu Task or a Base-only task, then record it in Base `Tasks`.

After implementation:

1. Write Bugfix, AI Run, Release, Decision, or Artifact records as appropriate.
2. Update the Base task status to `Verify` or `Done`.
3. Complete or comment on the native Feishu Task when one exists.
4. Keep verification detail in Base/Docs, not only in task comments.

## Avoid

- Do not make every thought a task.
- Do not put root cause detail only in task comments.
- Do not close a bug task unless the verification result is recorded somewhere durable.
- Do not assume Base `Tasks` replaces the native Feishu Tasks module; it mirrors and indexes the work for AI recall.

When official `lark-task` skill is installed, use it for exact CLI syntax and task GUID handling.
