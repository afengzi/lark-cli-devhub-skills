# Lark CLI Dev Hub V1.5 Design

Date: 2026-05-20
Status: Draft for user review

## Summary

Lark CLI Dev Hub V1.5 turns Feishu/Lark into an AI-readable development
knowledge hub for AI IDEs and CLIs such as Codex, Claude Code, Cursor, Trae,
OpenClaw, and custom agents.

The product promise is simple: let the AI tool that fixes code also write
structured evidence into the office knowledge system, so future AI runs can
search old bug evidence, avoid repeated debugging paths, keep tasks clear, and
make daily, weekly, bugfix, and release reports easier.

V1.5 includes automation entrypoints, but it must not require users to configure
every automation before the system becomes useful. The reliable baseline is:

```text
manual command -> Feishu/Lark write attempt -> receipt or outbox evidence
```

Local git hooks, GitHub Actions, cron reports, and Whiteboard drafts are
progressive layers on top of that baseline.

## Goals

- Connect AI coding tools with Feishu/Lark Base, Docs/Wiki, Tasks, and
  Whiteboard through skills and helper commands.
- Help agents search previous bugfixes, pitfalls, playbooks, decisions,
  AI runs, releases, project facts, and artifacts before repeating work.
- Capture structured Bugfix, AI Run, Release, Task, Decision, Artifact, and
  Project Fact records.
- Provide a V1.5 automation suite for manual commands, local hooks, GitHub
  PR/CI writeback, cron report drafts, and Whiteboard drafts.
- Make write success auditable through `.devhub/receipts/`.
- Preserve failed writes in `.devhub/outbox/` so they can be retried or reviewed.
- Keep domain skills loosely coupled while adding workflow skills that compose
  them into useful developer workflows.

## Non-Goals

- Do not require every user to configure GitHub Actions, cron, Whiteboard, and
  IM publishing on day one.
- Do not claim a write succeeded because a PR, push, merge, or cron job ran.
  Success requires a receipt or explicit readback.
- Do not publish IM messages or stakeholder-facing reports without explicit
  approval in V1.5.
- Do not hardcode one user's project facts into public skills. Project-specific
  facts belong in Project Facts records.
- Do not store secrets, access tokens, app secrets, private keys, raw
  credentials, or full environment files in Feishu/Lark.

## User Experience

The first useful experience should be:

1. The user installs the skills and helper scripts.
2. The user runs preflight and provisions a Dev Hub.
3. Before fixing a bug, the agent searches the Dev Hub.
4. After the fix, the agent writes Bugfix and AI Run records.
5. The helper creates a receipt on success or an outbox item on failure.
6. Later, report-loop can generate a weekly or release draft from those records.

The full V1.5 experience adds:

```text
local hook reminders
GitHub PR/CI writeback
scheduled report drafts
Whiteboard architecture drafts
```

Each automation layer must degrade gracefully. If GitHub Actions are not
configured, manual commands and local hooks still work. If cron is unavailable,
manual report generation still works. If Whiteboard APIs or tooling are limited,
the workflow can create a Doc-based diagram draft instead.

## Architecture

V1.5 uses four layers plus a reliability layer.

```text
Trigger Layer
  manual command
  local git hook
  GitHub PR/CI event
  cron or scheduled workflow
  Feishu/Lark event

Workflow Orchestration Layer
  lark-cli-devhub-code-loop
  lark-cli-devhub-report-loop
  lark-cli-devhub-pr-writeback
  lark-cli-devhub-whiteboard-loop
  future: meeting-loop, release-loop, inbox-triage

Domain Skills Layer
  lark-cli-devhub-base
  lark-cli-devhub-docs-wiki
  lark-cli-devhub-taskflow
  lark-cli-devhub-whiteboard
  lark-cli-devhub-drive
  lark-cli-devhub-sheets
  lark-cli-devhub-calendar
  lark-cli-devhub-communications
  lark-cli-devhub-meetings
  lark-cli-devhub-approvals-okr
  lark-cli-devhub-slides
  lark-cli-devhub-events

Feishu Dev Hub Data Layer
  Base records
  Docs/Wiki pages
  Whiteboards
  Tasks
  Dashboards
  Receipts
  Outbox
  Project Facts
```

Reliability is a cross-cutting layer:

```text
trigger does not equal success
write success requires receipt or readback
failed writes must produce outbox items
search workflows must disclose their coverage
automation must support dry-run where possible
```

## Skill Boundaries

Workflow skills compose domain skills. Domain skills do not implicitly compose
each other.

### Workflow Skills

`lark-cli-devhub-code-loop`

- Search old project facts, pitfalls, bugfixes, AI runs, releases, decisions,
  and playbooks before investigation.
- After a meaningful fix, write Bugfix and AI Run records.
- Create or update reusable Pitfalls and Playbooks when the lesson is general.
- Produce Bugfix Brief material for report-loop.
- Enforce receipt/outbox discipline.

`lark-cli-devhub-report-loop`

- Collect Tasks, Bugfixes, AI Runs, Releases, Decisions, Project Facts, and
  Artifacts.
- Generate daily, weekly, monthly, bugfix, release, and project report drafts.
- Write report drafts to Docs/Wiki and optionally update Base dashboard records.
- Keep IM publication approval-gated.

`lark-cli-devhub-pr-writeback`

- Convert PR and CI events into structured Dev Hub records.
- Map PR created or updated events to AI Runs.
- Map PR review decisions to Decisions or Bugfixes.
- Map merges to `main` or the default branch to Releases.
- Map CI failures to Bugfix candidates or Tasks.
- Never treat GitHub event completion as Feishu/Lark write success without a
  receipt or outbox item.

`lark-cli-devhub-whiteboard-loop`

- Generate Whiteboard or Doc diagram drafts for architecture changes, complex
  bugs, module rewrites, and workflow maps.
- Run dry-run first where possible.
- Write final boards only after approval.
- Link diagrams back to Base Artifacts and relevant Decisions.

### Domain Skills

Domain skills stay focused on one Feishu/Lark component:

- Base: schemas, records, views, dashboards, search, and receipts.
- Docs/Wiki: long-form context, project pages, reports, and release notes.
- Taskflow: tasks, blockers, status, owners, and next actions.
- Whiteboard: diagrams, architecture maps, and visual knowledge graphs.
- Drive: files, folders, imports, exports, permissions, and artifacts.
- Sheets: spreadsheets, QA matrices, report tables, and trackers.
- Calendar: scheduling, review blocks, release windows, and agenda planning.
- Communications: IM/Mail drafts, summaries, announcements, and artifact sharing.
- Meetings: minutes, action items, decisions, recordings, and summaries.
- Approvals/OKR: sign-offs, governance, goals, and progress evidence.
- Slides: briefings, release decks, retrospectives, and stakeholder updates.
- Events: event consumers, watchers, triggers, and writeback loops.

Shared helper commands may sit under the skills when behavior is stable,
testable, and receipt-aware.

## Data Model

Base is the structured source of truth for AI-readable project memory. Docs/Wiki
is the human-readable narrative layer. Whiteboard is a visual layer linked back
to structured records.

Core V1.5 tables:

| Table | Purpose |
|---|---|
| `Projects` | Repository identity, current focus, default branch, Wiki URL. |
| `Areas` | Product/code areas, code paths, risk, ownership. |
| `Tasks` | Work queue, priority, status, blockers, next action. |
| `Bugfixes` | Symptom, evidence, root cause, fix, verification, regression risk. |
| `Pitfalls` | Reusable traps and "check this first" lessons. |
| `Playbooks` | Diagnosis order, commands, evidence requirements, forbidden actions. |
| `Decisions` | PR review decisions, architecture choices, tradeoffs, consequences. |
| `Releases` | Branch, commit, included fixes, verification, rollback notes. |
| `Artifacts` | Linked Docs, Whiteboards, PRs, commits, files, screenshots, dashboards. |
| `AI Runs` | Agent task intent, evidence checked, files changed, verification, confidence. |
| `Project Facts` | Current facts, retired paths, invariants, source, last reviewed time. |

`Project Facts` prevents stale AI behavior. For example, a project can record
that an old voice path is retired and that the current implementation uses a
new command-stream path. Public skills provide the mechanism; project facts
provide the project-specific truth.

## Feishu/Lark Information Structure

Each project should have a Project Dev Hub:

```text
00 Index
01 Project
02 Bugs & Pitfalls
03 Playbooks
04 Reports
05 Project Facts
06 Releases
07 Meetings & Decisions
```

Cross-project knowledge should live in a Global Engineering Hub:

```text
00 Index
01 Debugging Playbooks
02 Architecture Patterns
03 Tooling & Agent Workflows
04 Release & Ops Checklists
05 Reusable Report Templates
```

Promotion rule:

```text
Project Dev Hub stores project-specific evidence.
Global Engineering Hub stores reusable engineering experience.
Agent memory stores collaboration preferences and workflow habits.
```

## Search Policy

V1.5 search should cover:

```text
Tasks
Bugfixes
AI Runs
Releases
Decisions
Project Facts
Artifacts
Pitfalls
Playbooks
Areas
```

If a helper command only searches a subset, it must disclose that subset in the
output. The skill must not claim complete project-history recall unless AI Runs,
Releases, Decisions, and Project Facts are included or separately checked.

Recommended search output metadata:

```json
{
  "coverage": ["Pitfalls", "Bugfixes", "Playbooks", "Decisions", "Areas"],
  "missing_for_full_recall": ["Tasks", "AI Runs", "Releases", "Project Facts", "Artifacts"]
}
```

After writing an AI Run or Release, receipt verification is required. Readback is
a stronger optional check when scopes and CLI support allow it.

## Workflow Details

### Init

`init` or `provision` should:

- run preflight checks;
- create or validate config;
- create Base tables and required fields;
- create starter Wiki/Docs structure;
- create local `.devhub/receipts/` and `.devhub/outbox/`;
- report missing Feishu/Lark scopes or missing local dependencies.

If provisioning partially fails, it should save known resource IDs and produce
an outbox item with the failed operation and redacted resource summary.

### Code Loop

Before fixing:

1. Extract project, area, symptom, error keywords, and relevant paths.
2. Search Dev Hub with explicit coverage.
3. Read relevant facts, pitfalls, bugfixes, playbooks, decisions, and AI runs.
4. Use old evidence to guide investigation when it is relevant.

After fixing:

1. Write a Bugfix record.
2. Write an AI Run record.
3. Update or create a Pitfall or Playbook if the lesson is reusable.
4. Link changed files, commit, PR, Docs, and Whiteboard artifacts when available.
5. Verify receipts or leave outbox items.

### PR Writeback

Event mapping:

| Event | Record |
|---|---|
| PR created | AI Run |
| PR updated | AI Run |
| PR reviewed | Decision or Bugfix |
| PR merged to default branch | Release |
| CI failed | Bugfix candidate or Task |

PR writeback can run in GitHub Actions, a local command, or a custom automation
host. It must preserve the same receipt/outbox semantics as manual commands.

### Report Loop

Report-loop should collect structured records and synthesize drafts:

- Daily draft: completed work, blockers, risks, next actions.
- Weekly draft: bugfixes, releases, decisions, risks, progress, next week.
- Bugfix brief: symptom, root cause, fix, verification, risk, related records.
- Release brief: included fixes, verification, rollback note, known risk.
- Project brief: milestone progress, project health, decisions, blockers.

Reports are drafts by default. Publishing to IM, Mail, Slides, or stakeholder
channels requires explicit approval in V1.5.

### Whiteboard Loop

Whiteboard-loop should trigger for:

- architecture changes;
- complex bug investigations;
- workflow or dependency changes;
- module rewrites;
- incident or release retrospectives.

The safe path is:

```text
generate draft -> dry-run -> user/agent approval -> write board -> link artifact
```

If Whiteboard rendering is unavailable, create a Doc diagram draft and link it
as an Artifact.

## Receipt And Outbox Discipline

Every write operation must produce one of:

```text
.devhub/receipts/*.json
.devhub/outbox/*.json
```

Receipt fields should include:

```json
{
  "operation": "record-ai-run",
  "project": "project-name",
  "target": {
    "type": "base-record",
    "table": "AI Runs",
    "record_id": "redacted-or-safe-id"
  },
  "source": {
    "type": "manual|hook|github-action|cron",
    "commit": "optional-sha",
    "pr": "optional-pr-url"
  },
  "created_at": "iso-8601"
}
```

Outbox fields should include:

```json
{
  "operation": "record-release",
  "project": "project-name",
  "payload_path": "optional-local-json",
  "error": "redacted error message",
  "retry_hint": "what to run next",
  "created_at": "iso-8601"
}
```

Rules:

- Never fake a receipt.
- Do not delete outbox items automatically after failed writes.
- Hook and PR automation may generate outbox items, but must not block all work
  until the workflow has been intentionally switched out of Shadow Mode.
- Push, PR, merge, and cron completion are triggers, not proof of write success.

## Dependencies And Scopes

Required baseline:

- Python 3.10+
- `git`
- `lark-cli` configured with Feishu/Lark app credentials and user auth

Required for one-command skill installation:

- Node.js 18+ with `npx`

Optional:

- `gh` or GitHub Actions for PR/CI writeback.
- cron, GitHub scheduled workflows, or another scheduler for reports.
- `@larksuite/whiteboard-cli` for Whiteboard rendering.
- ClawHub CLI through `npx -y clawhub@0.16.0`.

Minimum useful Feishu/Lark scopes:

```text
Docs/Wiki read-write
Base record read-write
```

Add Drive, Task, IM, Calendar, Sheets, Meetings, Approvals, Slides, Events, and
Whiteboard scopes only when those workflows are enabled.

## Safety And Privacy

- Redact credentials from receipts, outbox files, Docs, and Base records.
- Do not store raw environment files or secrets in Feishu/Lark.
- Prefer dry-run before external writes.
- Use approval gates before publishing to chat, mail, or stakeholder channels.
- Keep Whiteboard as a visual aid; Base remains the AI-readable source of truth.
- Keep project facts separate from agent memory.

## V1.5 Must Ship

- README explains the product promise, dependencies, and gradual automation path.
- Main skill documents code-loop, report-loop, PR writeback, and receipt/outbox
  discipline.
- Helper search discloses coverage and is extended or routed to cover the V1.5
  record set.
- Base schema includes or migrates to include Project Facts.
- Manual commands can write Bugfix, AI Run, and Release records.
- Local hook gate can warn about missing receipts or outbox evidence.
- GitHub Action template or documentation maps PR/CI events to writeback commands.
- Cron report template or documentation can generate report drafts.
- Whiteboard workflow supports draft/dry-run behavior and Artifact linking.

## Deferred Beyond V1.5

- Fully unattended IM publishing.
- Whiteboard writes without dry-run or approval.
- Organization-wide approval and OKR governance.
- Rich dashboards beyond the minimum Base/Dashboard linkage.
- Slides generation as a default report target.
- Deep bi-directional sync between every Feishu/Lark component.

## Acceptance Criteria

1. A user can install the skills and helper scripts with documented dependencies.
2. Preflight explains missing local tools or Feishu/Lark scopes.
3. Provisioning creates or validates the expected Dev Hub structure.
4. A bugfix workflow can search old records, write Bugfix and AI Run records,
   and produce receipts or outbox items.
5. A release workflow can write a Release record before or after merging to the
   default branch.
6. Search output makes its coverage explicit.
7. PR writeback documentation or templates map PR/CI events to records.
8. Report-loop can generate at least daily, weekly, bugfix, and release drafts
   from structured records.
9. Whiteboard-loop can produce a safe draft or fallback Doc diagram.
10. Validation catches forbidden local paths, concrete Feishu resource URLs, and
    secret-like markers in committed files.

## Implementation Notes For Planning

The implementation plan should be split so the reliable baseline lands before
automation expansion:

1. Update schemas, references, README, and search policy.
2. Extend helper search coverage and coverage reporting.
3. Add or document workflow skills for code-loop, report-loop, pr-writeback, and
   whiteboard-loop.
4. Add Project Facts support.
5. Add GitHub Action and cron templates.
6. Add Whiteboard draft/dry-run workflow support.
7. Run validation and marketplace discovery checks.

The planning phase should preserve the existing repository style: small
`SKILL.md` files, deeper references under `references/`, portable helper
scripts under `scripts/devhub_lib/`, and no personal paths or real Feishu
resource tokens in committed content.
