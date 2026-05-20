---
name: lark-cli-devhub-docs-wiki
description: Use when organizing Feishu/Lark Wiki spaces or Docs through lark-cli or feishu-cli for a development knowledge hub, including project pages, design notes, runbooks, bug retrospectives, and long-form artifacts linked from Base.
metadata:
  requires:
    bins: ["lark-cli"]
---

# Lark CLI Dev Hub Docs And Wiki

Use Docs/Wiki for long-form context that would make Base records too noisy. Base remains the index; Docs/Wiki are linked artifacts.

Discovery aliases: `feishu-cli docs`, `feishu-cli wiki`, `飞书知识库`, `飞书文档`, `lark-cli docs`, `lark-cli wiki`.

## Wiki Structure

Recommended first-level pages:

- `00 Inbox`: temporary notes waiting to become structured records.
- `10 Projects`: one page per project, linked from the `Projects` Base table.
- `20 Bugfix Retros`: long bug narratives worth rereading.
- `30 Playbooks`: expanded runbooks that do not fit in Base.
- `40 Decisions`: architecture and product decisions.
- `50 Maps`: whiteboard landing pages and visual summaries.
- `90 Archive`: stale or superseded artifacts.

## Page Rules

- Every useful page should have a matching `Artifacts` Base record.
- Put summary, project, area, tags, and search keywords into Base.
- Do not rely on Wiki hierarchy as the only retrieval mechanism.
- Avoid dumping raw logs unless they are short and safe.

## Creation Pattern

When a structured Base record should also become a durable human-readable Wiki page, prefer the Dev Hub helper so Base, Wiki, Artifact indexing, receipt, and outbox stay together:

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" record-bugfix --payload /tmp/devhub-bugfix.json --wiki
python3 "$DEVHUB_HOME/bin/devhub.py" record-release --payload /tmp/devhub-release.json --wiki
python3 "$DEVHUB_HOME/bin/devhub.py" record-decision --payload /tmp/devhub-decision.json --wiki
python3 "$DEVHUB_HOME/bin/devhub.py" record-project-fact --payload /tmp/devhub-project-fact.json --wiki
```

Use direct Docs/Wiki commands for custom pages that are not tied to a Base record:

```bash
lark-cli docs +create --api-version v2 --as user \
  --content '<title>Bugfix Retro: short title</title><p>Summary...</p>'
```

Move into Wiki when needed:

```bash
lark-cli wiki +node-create --as user \
  --space-id "$SPACE_ID" \
  --title "Bugfix Retro: short title" \
  --obj-type docx
```

When official `lark-doc` or `lark-wiki` skills are installed, use them for exact command syntax and permission handling.
