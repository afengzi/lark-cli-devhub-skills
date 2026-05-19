# Lark CLI Dev Hub Skills

Turn Feishu/Lark into an AI-readable development knowledge hub for Codex, Claude Code, Cursor, OpenClaw, Trae-style AI IDEs, and any agent that can load `SKILL.md`.

Use it to remember bug fixes, avoid repeated debugging, keep task state clear, write release evidence, and build a reusable engineering knowledge base on top of `lark-cli` / `feishu-cli`.

Also discoverable as: `feishu-cli`, `飞书 CLI`, `lark-cli`, `Lark CLI`, `Feishu Dev Hub`, `Lark Dev Hub`, `Feishu knowledge base`, `Lark knowledge base`, `Codex Feishu`, and `Claude Code Feishu`.

## What It Does

- Searches old Bugfixes, Pitfalls, Playbooks, Decisions, and Areas before a new bug investigation.
- Writes structured Bugfix and AI Run records after meaningful fixes.
- Writes Release records before pushing `main` or `master`.
- Keeps task state, next actions, blockers, and bug queues explicit.
- Links long-form Docs/Wiki pages and Whiteboards back to searchable Base records.
- Separates project facts from personal agent memory so Codex, Claude Code, and other agents can share the same knowledge base.
- Provides a hook gate that warns when bugfix commits or main pushes lack knowledge writeback evidence.

## Skills Included

| Skill | Use When |
|---|---|
| `lark-cli-devhub` | You want the full Dev Hub workflow: search before fixing, write after fixing, release evidence, and routing to domain skills. |
| `lark-cli-devhub-base` | You want Feishu/Lark Base as the structured AI-readable database. |
| `lark-cli-devhub-docs-wiki` | You want Docs/Wiki pages for design notes, bug retrospectives, runbooks, and project pages. |
| `lark-cli-devhub-taskflow` | You want Feishu/Lark Tasks for bug queues, task lists, blockers, owners, and next actions. |
| `lark-cli-devhub-whiteboard` | You want Whiteboards for architecture maps, workflow maps, dependency maps, and knowledge graphs. |
| `lark-cli-devhub-drive` | You want Drive files, folders, imports, exports, sync, comments, permissions, and artifacts. |
| `lark-cli-devhub-sheets` | You want spreadsheet reports, QA matrices, release checklists, and human-editable trackers. |
| `lark-cli-devhub-calendar` | You want agendas, scheduling, freebusy, meeting rooms, release windows, and review blocks. |
| `lark-cli-devhub-communications` | You want IM/Mail search, summaries, drafts, replies, announcements, and artifact sharing. |
| `lark-cli-devhub-meetings` | You want VC/Minutes records, meeting notes, recordings, action items, and decision extraction. |
| `lark-cli-devhub-approvals-okr` | You want approvals, sign-offs, OKR progress, release governance, and goal evidence. |
| `lark-cli-devhub-slides` | You want briefings, release review decks, retrospectives, roadmap decks, and stakeholder updates. |
| `lark-cli-devhub-events` | You want event consumers, watchers, automation triggers, and writeback loops. |

## Supported Agents

This pack is plain `SKILL.md` plus helper scripts. It works best with tools that support Agent Skills or skill-like markdown instructions.

| Platform | Install Path |
|---|---|
| Codex | `npx skills add afengzi/lark-cli-devhub-skills -g --agent codex --skill '*'` |
| Claude Code | `npx skills add afengzi/lark-cli-devhub-skills -g --agent claude-code --skill '*'` |
| Cursor | `npx skills add afengzi/lark-cli-devhub-skills -g --agent cursor --skill '*'` |
| OpenClaw / ClawHub | `npx -y clawhub@0.16.0 install lark-cli-devhub` |
| Multiple Agent Skills hosts | `npx skills add afengzi/lark-cli-devhub-skills -g --agent '*' --skill '*'` |
| Trae, Windsurf, Continue, Aider, custom agents | Clone the repo and point the tool at `skills/*/SKILL.md`, or copy the skill folders into that tool's skill/rules/instructions directory. |

If your AI tool does not have first-class Agent Skills support yet, the fallback is still simple: copy the relevant `skills/<name>/SKILL.md` folder into the tool's custom instruction or skill directory.

## Quick Install

Install all skills from GitHub:

```bash
npx skills add afengzi/lark-cli-devhub-skills --all
```

Install for all detected Agent Skills hosts:

```bash
npx skills add afengzi/lark-cli-devhub-skills -g --agent '*' --skill '*'
```

Install helper scripts and templates:

```bash
git clone https://github.com/afengzi/lark-cli-devhub-skills.git
cd lark-cli-devhub-skills
./scripts/install-devhub.sh
```

## Install From ClawHub

Search:

```bash
npx -y clawhub@0.16.0 search feishu-cli
npx -y clawhub@0.16.0 search lark-cli-devhub
```

Install the main skill:

```bash
npx -y clawhub@0.16.0 install lark-cli-devhub
```

Install optional domain skills:

```bash
npx -y clawhub@0.16.0 install lark-cli-devhub-base
npx -y clawhub@0.16.0 install lark-cli-devhub-docs-wiki
npx -y clawhub@0.16.0 install lark-cli-devhub-taskflow
npx -y clawhub@0.16.0 install lark-cli-devhub-whiteboard
npx -y clawhub@0.16.0 install lark-cli-devhub-drive
npx -y clawhub@0.16.0 install lark-cli-devhub-sheets
npx -y clawhub@0.16.0 install lark-cli-devhub-calendar
npx -y clawhub@0.16.0 install lark-cli-devhub-communications
npx -y clawhub@0.16.0 install lark-cli-devhub-meetings
npx -y clawhub@0.16.0 install lark-cli-devhub-approvals-okr
npx -y clawhub@0.16.0 install lark-cli-devhub-slides
npx -y clawhub@0.16.0 install lark-cli-devhub-events
```

Note: `npx skills find` searches the Agent Skills / skills.sh index, not the ClawHub registry. Use `npx skills add afengzi/lark-cli-devhub-skills --all` for GitHub install, or `npx clawhub search/install` for ClawHub.

## Requirements

- `lark-cli` configured with Feishu/Lark app credentials.
- User auth for personal Wiki, Docs, Tasks, and Base operations.
- Python 3.10+.
- Optional: `npx` and `@larksuite/whiteboard-cli` for Whiteboard rendering.

Preflight:

```bash
python3 "$HOME/.codex/devhub/bin/devhub.py" preflight
```

## Create Your Dev Hub

Provision Base tables, starter records, Wiki pages, and starter artifacts:

```bash
export DEVHUB_HOME="$HOME/.codex/devhub"

python3 "$DEVHUB_HOME/bin/devhub.py" provision \
  --schema "$DEVHUB_HOME/templates/base-schema.json" \
  --seed "$DEVHUB_HOME/templates/seed.example.json"
```

The generated config lives at:

```text
$HOME/.codex/devhub/config.json
```

Project-local runtime files live at:

```text
.devhub/receipts/
.devhub/outbox/
```

## Daily Workflow

Search before fixing a bug:

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" search \
  --project "$(basename "$PWD")" \
  --query "area symptom error keywords"
```

Write bugfix evidence:

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" record-bugfix --payload /tmp/devhub-bugfix.json
```

Write AI run evidence:

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" record-ai-run --payload /tmp/devhub-ai-run.json
```

Write release evidence:

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" record-release --payload /tmp/devhub-release.json
```

## Hook Gate

The default gate is Shadow Mode. It warns when a bugfix commit or main push lacks knowledge writeback evidence.

Accepted evidence:

- `# kb-updated`
- `.devhub/receipts/*.json`
- `.devhub/outbox/*.json`
- `# kb-skip: reason`

Script:

```bash
$HOME/.codex/devhub/bin/kb-gate.sh
```

## Data Model

Base is the structured source of truth. Docs/Wiki and Whiteboards are linked artifacts.

| Table | Purpose |
|---|---|
| `Projects` | Repository identity, current focus, default branch, Wiki URL. |
| `Areas` | Product or code areas, paths, risk, and ownership. |
| `Tasks` | Current work, priority, blockers, next action, and Feishu task URL. |
| `Bugfixes` | Symptom, evidence, root cause, fix summary, changed files, verification, regression risk. |
| `Pitfalls` | Reusable traps and "check this first" notes. |
| `Playbooks` | Diagnosis order, commands, success criteria, and forbidden actions. |
| `Decisions` | Architecture/product decisions, alternatives, consequences, review triggers. |
| `Releases` | Branch, commit SHA, verification, rollback notes, related tasks and bugfixes. |
| `Artifacts` | Linked Docs, Whiteboards, dashboards, files, and summaries. |
| `AI Runs` | Agent task intent, actions taken, evidence checked, files changed, verification result. |

## Repository Layout

```text
skills/
  lark-cli-devhub/
  lark-cli-devhub-base/
  lark-cli-devhub-docs-wiki/
  lark-cli-devhub-taskflow/
  lark-cli-devhub-whiteboard/
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
docs/
  architecture.md
  lark-cli-capability-map.md
  marketplaces.md
```

## Safety

- Do not write secrets, access tokens, app secrets, private keys, raw credentials, or full environment files into Feishu.
- Git hooks check for receipts or outbox items; they do not perform complex network writes.
- Whiteboard is a visual aid, not the only source of truth. Always pair durable maps with Base `Artifacts` records.
- Agent memory should store collaboration preferences. Dev Hub should store project facts and engineering evidence.

## Discovery Keywords

Use these keywords when searching or linking this project:

- English: `feishu-cli`, `lark-cli`, `Feishu CLI`, `Lark CLI`, `Feishu Dev Hub`, `Lark Dev Hub`, `AI knowledge base`, `developer knowledge base`, `bugfix memory`, `release evidence`, `Claude Code Feishu`, `Codex Feishu`
- Chinese: `飞书 CLI`, `飞书知识库`, `飞书多维表格`, `飞书任务`, `飞书画板`, `AI 项目知识库`, `bug 复盘`, `踩坑记录`, `发布证据`

## License

MIT. See [LICENSE](LICENSE).
