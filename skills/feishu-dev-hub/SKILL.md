---
name: feishu-dev-hub
description: Use when a developer needs Feishu/Lark as a project knowledge hub for bugfix memory, task clarity, release evidence, pitfall lookup, AI run summaries, or main-branch writeback discipline.
metadata:
  requires:
    bins: ["lark-cli", "python3", "git"]
---

# Feishu Dev Hub

Feishu Dev Hub is a development knowledge system backed by Feishu Base, Docs/Wiki, Tasks, and Whiteboard. Use it to prevent repeated bug investigation, keep task state explicit, and preserve release evidence.

## Core Boundaries

- Agent memory stores collaboration preferences and workflow style.
- Feishu Dev Hub stores project facts, tasks, bug evidence, pitfalls, playbooks, decisions, releases, artifacts, and AI run summaries.
- Do not write secrets, access tokens, app secrets, private keys, raw credentials, or full environment files.
- Treat Base as the structured source of truth. Docs hold long-form context. Whiteboard is a visual aid with a text summary linked back to Base.

## Local Entry Points

```bash
export DEVHUB_HOME="${DEVHUB_HOME:-$HOME/.codex/devhub}"

python3 "$DEVHUB_HOME/bin/devhub.py" search --project "$(basename "$PWD")" --query "symptom area keywords"
python3 "$DEVHUB_HOME/bin/devhub.py" record-bugfix --payload /tmp/devhub-bugfix.json
python3 "$DEVHUB_HOME/bin/devhub.py" record-ai-run --payload /tmp/devhub-ai-run.json
python3 "$DEVHUB_HOME/bin/devhub.py" record-release --payload /tmp/devhub-release.json
python3 "$DEVHUB_HOME/bin/devhub.py" sync-outbox --cwd "$PWD"
```

Config defaults to:

```text
$HOME/.codex/devhub/config.json
```

Project-local receipts and outbox:

```text
.devhub/receipts/
.devhub/outbox/
```

## When Working On Bugs

Before investigation:

1. Extract project, area/module, symptom, error keywords, and relevant file paths.
2. Run `devhub.py search` with a concise query.
3. Read relevant Pitfalls, Bugfixes, Playbooks, Decisions, and Areas from the output.
4. Let old records influence the fix, but only mention them in the final summary when they materially changed the work.

After a meaningful fix:

1. Write a Bugfix record.
2. Write an AI Run record.
3. Create or update a Pitfall or Playbook when the lesson is reusable.
4. Keep long narratives in Docs only when they are worth reading later.

See [`references/writeback-flows.md`](references/writeback-flows.md).

## Before Main Pushes

Before pushing `main` or `master`, write a Release record or leave an outbox item. The hook chain accepts one of:

- `# kb-updated`
- a receipt under `.devhub/receipts/`
- an outbox item under `.devhub/outbox/`
- `# kb-skip: reason` for a justified skip

The default mode is Shadow Mode: warn first, then tighten to enforced mode after the workflow is trusted.

See [`references/hook-policy.md`](references/hook-policy.md).

## Domain Routing

Use the split domain skills when the work needs deeper Feishu CLI behavior:

- `feishu-devhub-base` for Base schema, records, views, dashboards, and structured AI search.
- `feishu-devhub-docs-wiki` for Docs, Wiki spaces, long-form pages, and node organization.
- `feishu-devhub-taskflow` for task lists, bug/feature tasks, owners, and status discipline.
- `feishu-devhub-whiteboard` for architecture maps, workflow maps, dependency graphs, and visual summaries.

See [`references/domain-map.md`](references/domain-map.md) and [`references/knowledge-model.md`](references/knowledge-model.md).
