# Architecture

## Repository Shape

```text
skills/
  lark-cli-devhub/
    SKILL.md
    references/
  lark-cli-devhub-base/
    SKILL.md
  lark-cli-devhub-docs-wiki/
    SKILL.md
  lark-cli-devhub-taskflow/
    SKILL.md
  lark-cli-devhub-whiteboard/
    SKILL.md
scripts/
  devhub.py
  kb-gate.sh
  install-devhub.sh
templates/
  base-schema.json
  seed.example.json
  config.example.json
```

## Why Multiple Skills

The main skill is an orchestrator. It answers:

- Should the agent search Dev Hub?
- Should it write Bugfix, AI Run, or Release?
- What is Base versus Docs versus Whiteboard versus Tasks?
- Which domain skill should the agent read next?

Domain skills answer:

- How should this Feishu component be used for Dev Hub?
- What are the safety rules?
- What should future agents avoid?

This follows progressive disclosure: the agent loads the small orchestrator first, then only reads Base, Docs/Wiki, Tasks, or Whiteboard guidance when needed.

## Why Not Only Obsidian Or Agent Memory

Obsidian is excellent for personal note taking and graph browsing. Agent memory is good for preferences and cross-session collaboration habits. Dev Hub is different:

- Feishu Base gives structured rows and fields that AI can search and update.
- Docs/Wiki give human-readable long-form context.
- Whiteboard gives relationship maps for people.
- Tasks give operational state.

The AI-readable layer is Base. The human-readable layer is Docs/Wiki/Whiteboard. The personal preference layer stays in agent memory.
