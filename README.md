# Lark CLI Dev Hub Skills

Lark CLI Dev Hub Skills turn Feishu/Lark into a development knowledge hub for AI-assisted coding: bugfix memory, task clarity, release evidence, reusable pitfalls, project maps, and AI run summaries.

The pack is designed for Codex, Claude Code, Cursor, OpenClaw, and other agents that understand `SKILL.md`.

## What This Solves

- Search old bugfixes before fixing the same class of bug again.
- Write concise Bugfix and AI Run records after meaningful fixes.
- Require release evidence before pushing `main` or `master`.
- Keep current work in tasks and durable facts in Base.
- Link Docs and Whiteboards back to searchable Base records.
- Avoid mixing project facts with personal agent memory.

## Skills

| Skill | Purpose |
|---|---|
| `lark-cli-devhub` | Orchestrates bugfix search, writeback, release gates, and domain routing |
| `lark-cli-devhub-base` | Designs and writes the structured Base database |
| `lark-cli-devhub-docs-wiki` | Organizes long-form Docs and Wiki pages |
| `lark-cli-devhub-taskflow` | Manages task lists, task state, blockers, and task links |
| `lark-cli-devhub-whiteboard` | Creates architecture maps, flow maps, and knowledge graphs |

## Install From GitHub

After this repository is public:

```bash
npx skills add afengzi/lark-cli-devhub-skills --all
```

Install for specific agents:

```bash
npx skills add afengzi/lark-cli-devhub-skills -g --agent codex claude-code --skill '*'
```

Install helper scripts:

```bash
git clone https://github.com/afengzi/lark-cli-devhub-skills.git
cd lark-cli-devhub-skills
./scripts/install-devhub.sh
```

## Requirements

- `lark-cli` configured with Feishu/Lark app credentials.
- User auth for personal Wiki, Docs, Tasks, and Base operations.
- Python 3.10+.
- Optional: `npx` and `@larksuite/whiteboard-cli` for Whiteboard rendering.

Run:

```bash
python3 "$HOME/.codex/devhub/bin/devhub.py" preflight
```

## Provision A Dev Hub

```bash
export DEVHUB_HOME="$HOME/.codex/devhub"

python3 "$DEVHUB_HOME/bin/devhub.py" provision \
  --schema "$DEVHUB_HOME/templates/base-schema.json" \
  --seed "$DEVHUB_HOME/templates/seed.example.json"
```

This creates or reuses a Wiki space, creates a Dev Hub Base, creates tables and fields, seeds starter records, and stores config in:

```text
$HOME/.codex/devhub/config.json
```

## Everyday Commands

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

## Marketplace

- `npx skills` can install directly from this GitHub repository.
- ClawHub can publish each folder under `skills/` as an individual skill.

See [docs/marketplaces.md](docs/marketplaces.md).

## License

MIT. See [LICENSE](LICENSE).
