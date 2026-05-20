# Knowledge Model

Dev Hub separates human browsing from AI retrieval.

## Source Of Truth

| Layer | Role | AI Use |
|---|---|---|
| Base | Structured facts: Projects, Areas, Tasks, Bugfixes, Pitfalls, Playbooks, Decisions, Project Facts, Releases, Artifacts, AI Runs | Search first; use field names and keywords |
| Docs/Wiki | Long-form design notes, retrospectives, runbooks, incident notes | Open when a Base record links to a useful page |
| Whiteboard | Architecture, workflow, dependency, and knowledge maps | Visual aid; always pair with a Base Artifact summary |
| Tasks | Operational work queue and ownership | Use for current work state, not historical root cause detail |

## Wiki Layout

Provisioning should create scoped pages instead of dumping starter artifacts at the root:

```text
Dev Knowledge Hub
  00 Global
    02 Templates
    50 Maps
  10 Projects
    <project>
      00 Overview
      20 Bugfix Retros
      30 Playbooks
      40 Decisions
      50 Maps
      60 Reports
  90 Archive
```

## Records

- `Projects`: repository identity, default branch, current focus, wiki URL.
- `Areas`: modules or domains with code paths and risk level.
- `Tasks`: planned work, bugs, blockers, next action, and Feishu task URL.
- `Bugfixes`: symptom, evidence, root cause, fix, verification, regression risk.
- `Pitfalls`: reusable traps and what to check next time.
- `Playbooks`: diagnosis order, required evidence, commands, and forbidden actions.
- `Decisions`: accepted technical/product choices and review triggers.
- `Project Facts`: current implementation truths, retired paths, invariants, source, and review trigger. Use this before trusting older docs or old bug paths.
- `Releases`: branch, commit, verification, rollback notes, related tasks and bugfixes.
- `Artifacts`: Docs, Whiteboards, dashboards, links, and summaries.
- `AI Runs`: what the AI did, what evidence it checked, what changed, and writeback status.

## Field Policy

Fill these fields whenever they exist:

- `Title`
- `Project`
- `Area`
- `Status`
- `AI Summary`
- `Search Keywords`

Fill content-specific evidence fields when the record type calls for them, such as `Symptom`, `Root Cause`, `Verification Result`, `Decision`, or `Current Truth`.

Keep the default Base lightweight. Do not add `Related ...` columns to business tables.

Use `Record Relations` for AI-readable graph edges:

- `Source Table` / `Source Record ID` / `Source Title`
- `Relation Type`
- `Target Table` / `Target Record ID` / `Target Ref`
- `Evidence`
- `Search Keywords`

Feishu Base relation fields are still available for custom schemas. Describe them as 单向关联 / official `type: 18` or 双向关联 / official `type: 21`, but do not make them part of the default Dev Hub model.

Temporary write payloads may include `Relation Hints`, for example `Tasks: task title; Bugfixes: rec_xxx`. The helper strips that key from the business-table write and writes graph edges into `Record Relations`. Legacy `Related ...` input hints are still accepted for compatibility, but they are not Base fields.

## Task Layers

Feishu/Lark Tasks and Base `Tasks` are not the same thing:

- Feishu/Lark Tasks: native execution, reminders, assignees, and completion.
- Base `Tasks`: AI-readable index and task history anchor. Cross-record links are written into `Record Relations`.

Before coding, agents may create or pick an existing task. During work, update Base `Tasks` to `Doing`/`Blocked`/`Review`. After completion, update the native Feishu task when one exists and update the Base task to `Verify` or `Done` with links to the resulting Bugfix/AI Run/Release records.

## Avoiding Memory Conflict

Use agent memory for collaboration behavior:

- preferred tone
- approval habits
- how the user likes summaries
- recurring workflow preferences

Use Lark CLI Dev Hub for project facts:

- bugs and fixes
- code paths and architecture decisions
- test or verification evidence
- release history
- reusable mistakes and playbooks

This keeps AI personal memory small and keeps project knowledge portable across Codex, Claude Code, and teammates.
