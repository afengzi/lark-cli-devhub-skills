# Writeback Flows

## Bugfix Payload

Write after a meaningful bug fix:

```json
{
  "Title": "Short bug title",
  "Project": "project-name",
  "Area": "module or product area",
  "Status": "Fixed",
  "Relation Hints": "Tasks: task title or rec_xxx when known",
  "Symptom": "What failed from the user's or system's point of view.",
  "Evidence": "Logs, test failures, screenshots, command output, or code facts checked.",
  "Root Cause": "The actual cause, not only the visible symptom.",
  "Fix Summary": "What changed and why it fixes the issue.",
  "Changed Files": "path/a.ts, path/b.py",
  "Verification Commands": "pytest tests/foo_test.py",
  "Verification Result": "Passed, failed, skipped with reason, or partially verified.",
  "Regression Risk": "Low/Medium/High plus where to watch.",
  "Next Time Check": "Fast check future agents should run first.",
  "Avoid": "Wrong approach to avoid repeating.",
  "AI Summary": "Dense searchable summary.",
  "Search Keywords": "symptom module error file names"
}
```

Do not add `Related ...` columns to business tables. The helper consumes temporary payload hints such as `Relation Hints`, strips them from the business-table write, then writes lightweight graph edges into `Record Relations` when that table exists. Legacy `Related ...` input hints still work for compatibility, but documentation and templates should prefer `Relation Hints`.

Command:

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" record-bugfix --payload /tmp/devhub-bugfix.json
```

## AI Run Payload

Write after bug fixes, releases, large refactors, or investigations:

```json
{
  "Title": "AI run summary",
  "Project": "project-name",
  "Area": "module or product area",
  "Agent": "Codex or Claude Code",
  "Task Intent": "What the user wanted.",
  "Actions Taken": "Concise steps performed.",
  "Evidence Checked": "Files, tests, logs, old records, docs.",
  "Files Changed": "Changed paths.",
  "Verification Commands": "Commands run.",
  "Verification Result": "Result and caveats.",
  "Writeback Status": "Wrote Bugfix/Release/Outbox/Skipped with reason.",
  "AI Summary": "Dense searchable summary.",
  "Search Keywords": "task module command error"
}
```

Command:

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" record-ai-run --payload /tmp/devhub-ai-run.json
```

## Release Payload

Write before pushing `main` or `master`:

```json
{
  "Title": "Release YYYY-MM-DD short name",
  "Project": "project-name",
  "Area": "Release / Main Push",
  "Branch": "main",
  "Commit SHA": "abc123",
  "Summary": "What is being released.",
  "Verification Commands": "test/build commands",
  "Verification Result": "Result and caveats.",
  "Rollback Notes": "How to revert or what to watch.",
  "Relation Hints": "Tasks: task titles or URLs; Bugfixes: bugfix titles or URLs",
  "AI Summary": "Dense searchable release summary.",
  "Search Keywords": "release main deploy area"
}
```

Command:

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" record-release --payload /tmp/devhub-release.json
```

## Task Payload

Write when work needs explicit status, ownership, blocker, or next action tracking:

```json
{
  "Title": "Task title",
  "Project": "project-name",
  "Area": "module or product area",
  "Status": "Ready",
  "Task Source": "Feishu Task",
  "Feishu Task URL": "https://...",
  "Feishu Task GUID": "task guid from the native Tasks URL or API",
  "Type": "Bug",
  "Priority": "P1",
  "Expected Outcome": "What should be true when this task is done.",
  "Blocked By": "Current blocker or empty.",
  "Next Action": "Concrete next action.",
  "AI Summary": "Dense searchable task summary.",
  "Search Keywords": "task area blocker keywords"
}
```

Base `Tasks` is an AI-readable index. When there is a native Feishu/Lark Task, mirror its URL/GUID here. When there is no native task, set `Task Source` to `Base Only`.

`Feishu Task URL` is a URL-styled text field. `Feishu Task GUID` stays plain text.

Command:

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" record-task --payload /tmp/devhub-task.json
```

## Decision Payload

Write after PR review, architecture choices, product tradeoffs, or process decisions:

```json
{
  "Title": "Decision title",
  "Project": "project-name",
  "Area": "module or product area",
  "Status": "Accepted",
  "Decision": "What was decided.",
  "Context": "Why this decision was needed.",
  "Alternatives": "Options considered.",
  "Tradeoffs": "What this gives up and gains.",
  "Consequences": "Follow-up impact.",
  "Review Trigger": "When this should be revisited.",
  "AI Summary": "Dense searchable decision summary.",
  "Search Keywords": "decision architecture tradeoff keywords"
}
```

Command:

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" record-decision --payload /tmp/devhub-decision.json
```

## Artifact Payload

Write when a Doc, Wiki page, Whiteboard, PR, commit, file, screenshot, dashboard, or generated report should be linked back to structured records:

```json
{
  "Title": "Artifact title",
  "Project": "project-name",
  "Area": "module or product area",
  "Status": "Draft",
  "Artifact Type": "Doc",
  "Source URL": "safe URL",
  "Summary": "What this artifact contains.",
  "Relation Hints": "Bugfixes: bugfix title; Decisions: decision title; AI Runs: rec_xxx.",
  "AI Summary": "Dense searchable artifact summary.",
  "Search Keywords": "artifact doc whiteboard report keywords"
}
```

Command:

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" record-artifact --payload /tmp/devhub-artifact.json
```

## Project Fact Payload

Write when the current implementation truth changes or an old path becomes retired:

```json
{
  "Title": "Current fact title",
  "Project": "project-name",
  "Area": "module or product area",
  "Status": "Current",
  "Fact": "Short factual statement.",
  "Current Truth": "What agents should trust now.",
  "Retired Paths": "Old endpoints, modules, assumptions, or workflows to avoid.",
  "Source": "PR, commit, doc, code path, or user confirmation.",
  "Review Trigger": "When this fact should be checked again.",
  "AI Summary": "Dense searchable project fact summary.",
  "Search Keywords": "project fact retired path current truth keywords"
}
```

Command:

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" record-project-fact --payload /tmp/devhub-project-fact.json
```

## Outbox Rule

If Feishu write fails, do not fake success. Leave the generated `.devhub/outbox/*.json` item and mention it in the work summary. A later agent can retry with:

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" sync-outbox --cwd "$PWD"
```

## Receipt Format

Every successful write must create `.devhub/receipts/*.json` with:

- `operation`
- `created_at`
- `target.type`
- `target.table`
- `target.record_id`
- `source.type`
- `summary`

Every failed write must create `.devhub/outbox/*.json` with:

- `operation`
- `created_at`
- `error`
- `payload`
- `retry_count`
- `retry_hint`

Do not claim success from a push, PR event, merge, or cron run unless a receipt exists.
