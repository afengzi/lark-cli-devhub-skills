---
name: lark-cli-devhub-whiteboard
description: Use when creating or updating Feishu/Lark Whiteboards through lark-cli or feishu-cli for a development knowledge hub, including architecture maps, bug investigation paths, task maps, dependency maps, and project knowledge graphs.
metadata:
  requires:
    bins: ["lark-cli", "npx"]
---

# Lark CLI Dev Hub Whiteboard

Whiteboard is for human scanning and relationship maps. It is not the only AI-readable source of truth.

Discovery aliases: `feishu-cli whiteboard`, `飞书画板`, `lark-cli whiteboard`, `Lark Whiteboard`, `architecture diagram`, `knowledge graph`.

## Good Uses

- Architecture map with 3-7 zones.
- Bug diagnosis path.
- Release flow.
- Task dependency map.
- Project knowledge graph overview.
- Decision impact map.

## Starter Maps

`devhub.py provision` should create and index these durable maps when permissions allow:

- Global Maps: `Global: Dev Hub 总览图`, `Global: Bug 排查路径图`, `Global: PR 写回流程图`, `Global: 任务执行闭环图`.
- Project Maps: `<project>: 架构图`, `<project>: Bug 排查路径图`, `<project>: PR 写回流程图`, `<project>: 任务执行闭环图`.

Local SVG templates live under `templates/whiteboards/` or `$DEVHUB_HOME/templates/whiteboards/` for redraw guidance. They should not appear as template pages in Feishu Wiki.

If a map is written to Wiki/Docs, create or update a matching Base `Artifacts` row. Do not leave Whiteboard-only knowledge without an AI-readable summary.

## Required Pairing

Every durable Whiteboard should have a Base `Artifacts` record with:

- `Title`
- `Project`
- `Area`
- `Artifact Type = Whiteboard`
- `Source URL`
- `Summary`
- `AI Summary`
- `Search Keywords`

This lets future agents discover the map without needing to visually inspect it first.

## Rendering Rules

- Default Dev Hub starter maps use SVG visual templates converted to Feishu Whiteboard nodes. Prefer this for overview maps intended for human scanning.
- Mermaid is good for simple flows, timelines, sequence diagrams, and mind maps.
- SVG or DSL is better for dense architecture and knowledge maps.
- Raw OpenAPI JSON can be used when a workflow already has native Whiteboard node data.
- Existing provisioned maps are preserved by default; use `DEVHUB_WHITEBOARD_OVERWRITE=1` only when intentionally redrawing from templates.
- SVG conversion output is cached by template content under `$DEVHUB_HOME/cache/whiteboards/`.
- Keep line count low. Prefer grouping and adjacency over all-to-all edges.
- Validate locally before writing to Feishu when possible.

## CLI Pattern

```bash
npx -y @larksuite/whiteboard-cli@^0.2.11 \
  -i diagram.mmd -o diagram.png -f mermaid

npx -y @larksuite/whiteboard-cli@^0.2.11 \
  -i diagram.mmd --to openapi --format json \
  | lark-cli whiteboard +update \
      --whiteboard-token "$WHITEBOARD_TOKEN" \
      --source - --input_format raw \
      --idempotent-token "$(date +%s)-devhub" \
      --overwrite --dry-run --as user
```

After a meaningful redraw, query or export the remote board once to confirm the write landed.

When official `lark-whiteboard` skill is installed, use it for exact query/update workflows.
