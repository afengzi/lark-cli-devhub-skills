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
  wiki/
  whiteboards/
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
| `wiki_docs.py` | Wiki/Docs creation, complete starter templates, and generated Whiteboard artifacts |
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

## Wiki And Base Boundaries

Provisioning creates scoped Wiki areas:

```text
Dev Knowledge Hub
  00 Global
  10 Projects/<project>
  90 Archive
```

Starter docs and maps belong under `00 Global` or `10 Projects/<project>`, never directly under the root. This keeps global templates, project-specific knowledge, and future cleanup separate.

Provisioning writes complete template content into Docs/Wiki rather than leaving placeholder pages. The reusable template set covers project records, bugfix retrospectives, playbooks, decisions, releases, AI runs, and bug investigation paths.

Provisioning creates starter Whiteboard pages in three places:

- `00 Global/50 Maps`: `Global: Dev Hub 总览图`, `Global: Bug 排查路径图`, `Global: PR 写回流程图`, and `Global: 任务执行闭环图`.
- `10 Projects/<project>/50 Maps`: `<project>: 架构图`, `<project>: Bug 排查路径图`, `<project>: PR 写回流程图`, and `<project>: 任务执行闭环图`.
- `00 Global/02 Templates`: `Template: Bug 排查路径图`, `Template: PR 写回流程图`, and `Template: 任务执行闭环图`.

Every generated map is a human-readable SVG visual template converted into Feishu Whiteboard native nodes. Each map gets an `Artifacts` Base record. The map itself helps humans scan relationships; the Artifact summary and keywords make the map discoverable to AI.

The Whiteboard writer accepts SVG, Mermaid, or raw OpenAPI JSON. Starter maps use SVG for human-readable layouts. SVG conversion output is cached under `$DEVHUB_HOME/cache/whiteboards/`, and existing boards are preserved by default unless `DEVHUB_WHITEBOARD_OVERWRITE=1` is set.

Artifact indexing uses a batched Base path where safe: list existing records once by match fields, skip unchanged rows, batch-create new rows, and update only changed existing rows individually. This avoids treating `record-batch-update` as row-specific, because current `lark-cli base +record-batch-update` applies one shared patch to every listed record.

Provisioning also archives known Wiki noise created by earlier or failed runs: root/global `Untitled` pages and old duplicate `Dev Hub 使用说明` / `AI 写入规则` nodes are moved under `90 Archive/99 Provision Cleanup` instead of being deleted.

Base stays lightweight:

- Business tables keep text search fields and evidence fields, not many cross-table relation columns.
- `Record Relations` stores graph edges for AI recall: source table/record, relation type, target table/ref, evidence, and search keywords.
- `base-views.json` creates human-facing views so people can browse task boards, bug triage, artifacts, current facts, and knowledge edges without widening every table.
- Advanced custom schemas may still use Feishu Base relation fields: 单向关联 maps to official `type: 18`, and 双向关联 maps to official `type: 21`.
- Existing Bases from older versions can remove deprecated `Project Relation`, `Area Relation`, and `Related ... Relation(s)` fields with `devhub.py cleanup-relation-fields` after reviewing `--dry-run`.

Native Feishu Tasks remain the execution/reminder system. Base `Tasks` is the searchable mirror; cross-record context belongs in `Record Relations`.
