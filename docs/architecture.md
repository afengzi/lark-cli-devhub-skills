# Architecture

## Repository Shape

```text
skills/
  lark-cli-devhub/
    SKILL.md
    references/
  lark-cli-devhub-code-loop/
    SKILL.md
  lark-cli-devhub-report-loop/
    SKILL.md
  lark-cli-devhub-pr-writeback/
    SKILL.md
  lark-cli-devhub-whiteboard-loop/
    SKILL.md
  lark-cli-devhub-base/
    SKILL.md
  lark-cli-devhub-docs-wiki/
    SKILL.md
  lark-cli-devhub-taskflow/
    SKILL.md
  lark-cli-devhub-whiteboard/
    SKILL.md
  lark-cli-devhub-drive/
  lark-cli-devhub-sheets/
  lark-cli-devhub-calendar/
  lark-cli-devhub-communications/
  lark-cli-devhub-meetings/
  lark-cli-devhub-approvals-okr/
  lark-cli-devhub-slides/
  lark-cli-devhub-events/
scripts/
  devhub.py
  devhub_lib/
  kb-gate.sh
  install-devhub.sh
templates/
  base-schema.json
  seed.example.json
  config.example.json
  report-daily.md
  report-weekly.md
  report-release.md
  whiteboard-draft.md
  github-pr-writeback.yml
  cron-report.yml
```

## Why Multiple Skills

The main skill is an orchestrator. It answers:

- Should the agent search Dev Hub?
- Should it write Bugfix, AI Run, or Release?
- What is Base versus Docs versus Whiteboard versus Tasks?
- Which domain skill should the agent read next?

Workflow skills compose domains into useful developer loops:

- `lark-cli-devhub-code-loop` searches old records before investigation and writes Bugfix/AI Run evidence after fixes.
- `lark-cli-devhub-report-loop` turns structured records into daily, weekly, bugfix, release, and project report drafts.
- `lark-cli-devhub-pr-writeback` maps PR and CI events to Dev Hub records.
- `lark-cli-devhub-whiteboard-loop` creates safe architecture, workflow, and bug investigation diagram drafts.

Domain skills answer:

- How should this Feishu component be used for Dev Hub?
- What are the safety rules?
- What should future agents avoid?

This follows progressive disclosure: the agent loads the small orchestrator first, then only reads the domain guidance it needs: Base, Docs/Wiki, Tasks, Whiteboard, Drive, Sheets, Calendar, Communications, Meetings, Approvals/OKR, Slides, or Events.

Boundary rule: workflow skills may compose domain skills, but domain skills should not implicitly compose each other.

## Helper Script Modules

`scripts/devhub.py` is only the entrypoint. Implementation lives in `scripts/devhub_lib/`:

| Module | Responsibility |
|---|---|
| `paths.py` | Runtime paths and environment overrides |
| `io.py` | JSON IO, timestamping, output parsing, token extraction |
| `config.py` | Config loading, redaction, receipt/outbox directories |
| `lark.py` | `lark-cli` subprocess calls |
| `base.py` | Base creation, schema provisioning, record upsert |
| `wiki_docs.py` | Wiki/Docs creation and starter artifacts |
| `records.py` | Bugfix/AI Run/Release/Task/Decision/Artifact/Project Fact receipts and outbox |
| `search.py` | Record search across the V1.5 full-recall table set with coverage metadata |
| `reports.py` | Deterministic daily, weekly, and release Markdown report drafts |
| `whiteboard.py` | Deterministic Whiteboard or fallback Doc diagram drafts |
| `hooks.py` | Commit/push writeback gate |
| `commands.py` | CLI command implementations |
| `cli.py` | Argument parser and command routing |

## Why Not Only Obsidian Or Agent Memory

Obsidian is excellent for personal note taking and graph browsing. Agent memory is good for preferences and cross-session collaboration habits. Dev Hub is different:

- Feishu Base gives structured rows and fields that AI can search and update.
- Docs/Wiki give human-readable long-form context.
- Whiteboard gives relationship maps for people.
- Tasks give operational state.

The AI-readable layer is Base. The human-readable layer is Docs/Wiki/Whiteboard. The personal preference layer stays in agent memory.
