# Domain Map

Use one small domain document per Feishu capability. This keeps the orchestrator skill easy to load and lets each domain evolve independently.

## Workflow Skills

Workflow skills compose domains into user-facing loops. Domain skills should not implicitly call each other.

| Workflow | Skill | Use For |
|---|---|---|
| Code Loop | `lark-cli-devhub-code-loop` | Bug investigation, old-record search, Bugfix/AI Run writeback |
| Report Loop | `lark-cli-devhub-report-loop` | Daily, weekly, bugfix, release, and project report drafts |
| PR Writeback | `lark-cli-devhub-pr-writeback` | PR/CI event mapping to AI Runs, Decisions, Bugfix candidates, Tasks, and Releases |
| Whiteboard Loop | `lark-cli-devhub-whiteboard-loop` | Architecture, workflow, dependency, and bug investigation diagram drafts |

## Split

| Domain | Skill | Use For |
|---|---|---|
| Base | `lark-cli-devhub-base` | Structured records, schema, views, dashboards, AI-readable database |
| Docs/Wiki | `lark-cli-devhub-docs-wiki` | Long-form notes, runbooks, design docs, wiki hierarchy |
| Taskflow | `lark-cli-devhub-taskflow` | Tasks, bug queues, ownership, status, current work |
| Whiteboard | `lark-cli-devhub-whiteboard` | Architecture maps, dependency maps, flow diagrams |
| Drive | `lark-cli-devhub-drive` | Files, folders, imports, exports, sync, comments, permissions |
| Sheets | `lark-cli-devhub-sheets` | Reports, QA matrices, release checklists, human-editable trackers |
| Calendar | `lark-cli-devhub-calendar` | Agenda, freebusy, scheduling, rooms, release windows, review blocks |
| Communications | `lark-cli-devhub-communications` | IM, Mail, chat search, email triage, announcements, sharing |
| Meetings | `lark-cli-devhub-meetings` | VC, Minutes, notes, recordings, decisions, action items |
| Approvals/OKR | `lark-cli-devhub-approvals-okr` | Approvals, sign-offs, OKR progress, governance evidence |
| Slides | `lark-cli-devhub-slides` | Briefings, release reviews, retrospectives, roadmap decks |
| Events | `lark-cli-devhub-events` | Event consumers, watchers, automation triggers, writeback loops |

## Why Split

- Better token economy: the agent reads only the domain it needs.
- Cleaner maintenance: Base fields can change without rewriting Whiteboard guidance.
- Better marketplace packaging: users can install the whole pack or a subset.
- Less conflict with project memory: Dev Hub records factual work; skills only teach how to operate the system.

## When To Add A New Domain

Create another domain skill when the domain has its own commands, safety rules, or repeated mistakes. Good candidates:

- `lark-cli-devhub-automation`
- `lark-cli-devhub-ai-assistant`
- `lark-cli-devhub-hr`
- `lark-cli-devhub-finance`
