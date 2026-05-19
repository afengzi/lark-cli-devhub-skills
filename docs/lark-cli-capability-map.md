# Lark CLI Capability Map

This map is derived from `lark-cli --help` and domain `--help` output from `lark-cli 1.0.34`.

## Dev Hub Core

| CLI Domain | Dev Hub Skill | Office Value |
|---|---|---|
| `base` | `lark-cli-devhub-base` | Structured source of truth, dashboards, workflows, forms, roles |
| `docs`, `wiki` | `lark-cli-devhub-docs-wiki` | Long-form pages, project knowledge hierarchy, runbooks |
| `task` | `lark-cli-devhub-taskflow` | Work queue, blockers, ownership, task comments and attachments |
| `whiteboard` | `lark-cli-devhub-whiteboard` | Architecture maps, workflow maps, knowledge graphs |

## Office Expansion

| CLI Domain | Dev Hub Skill | Office Value |
|---|---|---|
| `drive` | `lark-cli-devhub-drive` | Files, folders, import/export, sync, comments, permissions |
| `sheets` | `lark-cli-devhub-sheets` | Reports, QA matrices, release checklists, trackers |
| `calendar` | `lark-cli-devhub-calendar` | Agenda, scheduling, freebusy, rooms, release windows |
| `im`, `mail` | `lark-cli-devhub-communications` | Chat search, announcements, email triage, drafts |
| `vc`, `minutes` | `lark-cli-devhub-meetings` | Meeting notes, recordings, transcripts, action items |
| `approval`, `okr` | `lark-cli-devhub-approvals-okr` | Governance, sign-off, goal progress, executive reporting |
| `slides` | `lark-cli-devhub-slides` | Briefings, release reviews, roadmaps, retrospectives |
| `event` | `lark-cli-devhub-events` | Watchers, automations, event-driven writeback |

## Backlog Candidates

These domains are useful but not yet split into dedicated Dev Hub skills:

- `contact`: user lookup, owner resolution, reviewer resolution.
- `markdown`: Drive-native markdown knowledge pages.
- `attendance`: people operations and availability records.
- `profile`, `auth`, `config`, `doctor`, `schema`: setup and troubleshooting helpers.

## Product Direction

The pack should stay workflow-first, not API-first. A useful Dev Hub skill says:

- when to use the domain
- how it maps to Base/Docs/Tasks/Artifacts
- what evidence to preserve
- what not to write or automate
- which `lark-cli` commands are the stable entry points

The official `larksuite/cli` skills remain the command-level reference. This pack should teach office workflows that combine those commands into useful outcomes.
