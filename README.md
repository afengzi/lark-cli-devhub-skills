# Lark CLI Dev Hub Skills

Turn Feishu/Lark into an AI-readable development knowledge hub for Codex, Claude Code, Cursor, OpenClaw, Trae-style AI IDEs, and any agent that can load `SKILL.md`.

Use it to remember bug fixes, avoid repeated debugging, keep task state clear, write release evidence, and build a reusable engineering knowledge base on top of `lark-cli` / `feishu-cli`.

It is designed to bridge the last wall between AI coding tools and office knowledge work: your AI IDE/CLI fixes code, Dev Hub writes the evidence into Feishu/Lark, and future AI runs can search that memory before repeating the same debugging path. Start with manual commands, then add hooks, PR writeback, cron reports, and Whiteboard drafts when your workflow is ready.

## Why Developers Use It

- Let your AI IDE/CLI search old bug evidence before investigating a new failure.
- Build a repeatable bug location -> fix -> verification -> writeback loop.
- Avoid repeated debugging by turning pitfalls, root causes, and playbooks into searchable Feishu/Lark records.
- Keep tasks, blockers, release notes, and AI run evidence in the same workspace your team already uses.
- Make reports easier: daily notes, weekly summaries, bugfix briefs, and release updates can be generated from structured records instead of memory.
- Connect Codex, Claude Code, Cursor, Trae, OpenClaw, and custom agents to Feishu/Lark without forcing every automation to be configured on day one.

You do not need to set up full automation up front. The reliable baseline is manual command + receipt/outbox; local git hooks, GitHub Actions, cron reports, and Whiteboard workflows can be added gradually.

Also discoverable as: `feishu-cli`, `飞书 CLI`, `lark-cli`, `Lark CLI`, `Feishu Dev Hub`, `Lark Dev Hub`, `Feishu knowledge base`, `Lark knowledge base`, `Codex Feishu`, and `Claude Code Feishu`.

## What It Does

- Searches old Tasks, Bugfixes, AI Runs, Releases, Decisions, Project Facts, Artifacts, Pitfalls, Playbooks, and Areas before a new bug investigation.
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
| `lark-cli-devhub-code-loop` | You want bug investigation, old-record search, Bugfix/AI Run writeback, and receipt/outbox discipline. |
| `lark-cli-devhub-report-loop` | You want daily, weekly, bugfix, release, or project report drafts from Dev Hub records. |
| `lark-cli-devhub-pr-writeback` | You want GitHub PR/CI events mapped to AI Runs, Decisions, Bugfix candidates, Tasks, or Releases. |
| `lark-cli-devhub-whiteboard-loop` | You want architecture, workflow, dependency, or bug investigation diagram drafts linked to Artifacts. |
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

Most users should start with the Agent Skills installer, not individual ClawHub commands. The installer can install the whole pack in one command, list available sub-skills, or install only the sub-skills you select.

### Dependency Checklist

Required for local helper scripts:

- Python 3.10+
- `git`
- `lark-cli` configured with Feishu/Lark app credentials and user auth

Required for one-command skill installation:

- Node.js 18+ with `npx`

Optional, depending on the workflow you enable:

- `clawhub` via `npx -y clawhub@0.16.0` for ClawHub install/publish.
- `gh` or GitHub Actions for PR/CI writeback automation.
- `cron`, GitHub scheduled workflows, or another scheduler for daily/weekly report drafts.
- `@larksuite/whiteboard-cli` for Whiteboard rendering and architecture map workflows.
- Feishu/Lark app scopes for Base, Docs/Wiki, Drive, Tasks, IM, Calendar, Sheets, Meetings, Approvals, or Whiteboard depending on the domain skills you use.

Preview available skills before installing:

```bash
npx skills add afengzi/lark-cli-devhub-skills --list
```

Install all skills from GitHub:

```bash
npx skills add afengzi/lark-cli-devhub-skills -g -y
```

This installs the full skill pack; you do not need to install every sub-skill one by one.

Install for all detected Agent Skills hosts:

```bash
npx skills add afengzi/lark-cli-devhub-skills -g --agent '*' --skill '*'
```

Install selected skills when you want a smaller footprint:

```bash
npx skills add afengzi/lark-cli-devhub-skills -g -y -s lark-cli-devhub
npx skills add afengzi/lark-cli-devhub-skills -g -y -s lark-cli-devhub -s lark-cli-devhub-code-loop -s lark-cli-devhub-report-loop
```

Many interactive shells can show prompts when you omit non-interactive flags such as `-y`. In non-interactive AI IDE/CLI sessions, use `-s`/`--skill` for explicit selection.

Install local helper scripts and templates:

```bash
git clone https://github.com/afengzi/lark-cli-devhub-skills.git
cd lark-cli-devhub-skills
./scripts/install-devhub.sh
```

The helper installer defaults to all local skills, but it can also install a subset:

```bash
./scripts/install-devhub.sh --list-skills
./scripts/install-devhub.sh --skills core
./scripts/install-devhub.sh --skills workflow
./scripts/install-devhub.sh --skills lark-cli-devhub,lark-cli-devhub-code-loop
```

The helper installer also prints the recommended `lark-cli auth` setup commands after installation. Use `--no-auth-guide` only if your Feishu/Lark app is already authorized.

## Lark CLI Auth Setup

Dev Hub needs `lark-cli` authentication and Feishu/Lark app scopes before it can write Base, Docs/Wiki, Tasks, or other resources. Use the official `lark-cli auth` flow:

```bash
lark-cli doctor --offline
lark-cli auth status --verify
lark-cli auth login --domain base,wiki,docs --recommend
lark-cli auth scopes --format pretty
```

For extra workflows, request only the domains you enable:

```bash
lark-cli auth login --domain task,drive,im,calendar,sheets,minutes --recommend
```

To inspect exact scopes before requesting or checking them:

```bash
lark-cli schema <service.resource.method> --format pretty
lark-cli auth check --scope "<space-separated scopes>"
```

For headless agent sessions, start device login and send the browser URL to the user:

```bash
lark-cli auth login --domain base,wiki,docs --recommend --no-wait --json
lark-cli auth login --device-code "<device_code>"
```

## Install From ClawHub

ClawHub publishes one skill slug at a time. Use it when you want one specific skill from the ClawHub registry. Use `npx skills add afengzi/lark-cli-devhub-skills -g -y` when you want the full pack from GitHub.

Search:

```bash
npx -y clawhub@0.16.0 search feishu-cli
npx -y clawhub@0.16.0 search lark-cli-devhub
```

Install the main skill:

```bash
npx -y clawhub@0.16.0 install lark-cli-devhub
```

Install workflow skills:

```bash
npx -y clawhub@0.16.0 install lark-cli-devhub-code-loop
npx -y clawhub@0.16.0 install lark-cli-devhub-report-loop
npx -y clawhub@0.16.0 install lark-cli-devhub-pr-writeback
npx -y clawhub@0.16.0 install lark-cli-devhub-whiteboard-loop
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

Note: `npx skills find` searches the Agent Skills / skills.sh index, not the ClawHub registry. Use `npx skills add afengzi/lark-cli-devhub-skills -g -y` for the full GitHub skill pack, or `npx clawhub search/install` for individual ClawHub skills.

## Requirements

- `lark-cli` configured with Feishu/Lark app credentials.
- User auth and app scopes for the Feishu/Lark resources you want to write.
- Python 3.10+ and `git`.
- Node.js 18+ with `npx` if you install from GitHub/ClawHub using npm commands.
- Optional: `gh` or GitHub Actions for PR/CI writeback.
- Optional: cron/scheduled workflows for daily, weekly, or monthly report drafts.
- Optional: `@larksuite/whiteboard-cli` for Whiteboard rendering.

Minimum useful Feishu/Lark scopes are Docs/Wiki read-write plus Base record read-write. Add Drive, Task, IM, Calendar, Sheets, Meetings, Approvals, and Whiteboard scopes only when you enable those workflows.

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

Write task, decision, artifact, or project fact evidence:

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" record-task --payload /tmp/devhub-task.json
python3 "$DEVHUB_HOME/bin/devhub.py" record-decision --payload /tmp/devhub-decision.json
python3 "$DEVHUB_HOME/bin/devhub.py" record-artifact --payload /tmp/devhub-artifact.json
python3 "$DEVHUB_HOME/bin/devhub.py" record-project-fact --payload /tmp/devhub-project-fact.json
```

Search scope note: full project-history recall should cover Tasks, Bugfixes, AI Runs, Releases, Decisions, Project Facts, Artifacts, Pitfalls, Playbooks, and Areas. The helper reports its coverage so agents do not overclaim what they checked.

## Automation Roadmap

The pack is useful without installing every automation. Add these layers gradually:

| Layer | What It Adds | Safe Default |
|---|---|---|
| Manual commands | Search, bugfix writeback, AI run evidence, release records. | Always available; every write creates receipt or outbox evidence. |
| Local git hook | Reminds you to write knowledge evidence before bugfix commits or main pushes. | Shadow Mode warnings before enforcement. |
| PR writeback | PR created/updated writes AI Runs, reviews write Decisions/Bugfixes, merges write Releases, CI failures write task/bug candidates. | A PR event is only a trigger; success requires a receipt. |
| Cron reports | Daily, weekly, monthly, and release report drafts from Base records. | Draft first; publish only after explicit approval. |
| Whiteboard workflow | Architecture maps, dependency maps, and bug investigation diagrams. | Dry-run or draft first; link final boards back to Base Artifacts. |

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
| `Project Facts` | Current implementation truths, retired paths, invariants, source, and review triggers. |
| `Releases` | Branch, commit SHA, verification, rollback notes, related tasks and bugfixes. |
| `Artifacts` | Linked Docs, Whiteboards, dashboards, files, and summaries. |
| `AI Runs` | Agent task intent, actions taken, evidence checked, files changed, verification result. |

## Repository Layout

```text
skills/
  lark-cli-devhub/
  lark-cli-devhub-code-loop/
  lark-cli-devhub-report-loop/
  lark-cli-devhub-pr-writeback/
  lark-cli-devhub-whiteboard-loop/
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
  report-daily.md
  report-weekly.md
  report-release.md
  whiteboard-draft.md
  github-pr-writeback.yml
  cron-report.yml
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
