---
name: lark-cli-devhub-architecture-batch
description: Use when publishing a batch of architecture diagrams (N >= 3 boards) as SVG whiteboards into a Feishu/Lark Wiki space — full pipeline from per-module SVG authoring to wiki node creation, whiteboard block injection, SVG write, and index page assembly. Covers the cross-skill choreography (lark-wiki + lark-whiteboard + lark-doc) and the avoidable footguns each layer has.
metadata:
  requires:
    bins: ["lark-cli", "npx", "jq", "xmllint"]
---

# Lark CLI Dev Hub Architecture Batch

Use this skill when a project's architecture grows past one diagram and you want a coherent **index + N module boards** layout in Feishu/Lark Wiki, with each board independently editable, linkable, and version-trackable.

This is the workflow you reach for when you would otherwise stack 8 zones onto one over-dense board and lose review-ability. The skill exists because the cross-skill choreography (lark-wiki + lark-whiteboard + lark-doc) has several footguns that are not visible from any single SKILL.md — they only surface when you run the whole pipeline end-to-end.

Discovery aliases: `feishu 架构图批量`, `lark whiteboard batch`, `architecture diagrams pipeline`, `wiki 架构图索引`.

## When To Use

- Publishing 3+ related architecture / flow / data-model diagrams together (e.g. macro + per-module breakdown).
- Replacing a single dense "everything board" with an index page plus focused sub-boards.
- Re-publishing an aging architecture wiki page where the embedded board's `block_token` should ideally stay stable.
- Any time the diagrams need their own dedicated wiki pages so they can be linked from PRs, decisions, retros, and onboarding docs without dragging an entire mega-board with them.

## When Not To Use

- Single diagram → use `lark-cli-devhub-whiteboard` directly.
- One-off whiteboard with no permanent wiki home → use `lark-cli-devhub-whiteboard-loop` for the safe-write loop and stop there.
- Diagrams that belong inside an existing Doc / Wiki page rather than as standalone children → see `lark-cli-devhub-docs-wiki`.

## Pipeline Overview

```
  1. Recon       ─── list current wiki space + restate target structure to user
  2. Author      ─── one SVG per board under timestamped subdir, local --check + xmllint
  3. Create      ─── batch +node-create N sibling wiki docs under the chosen parent
  4. Inject      ─── docs +update --command append --content '<whiteboard type="blank"/>'
  5. Write       ─── whiteboard +update --source - --input_format raw (raw OpenAPI JSON)
  6. Index       ─── HTML (NOT markdown) content appended to the parent wiki doc
  7. Verify      ─── whiteboard +query --output_as image for 2-3 boards, diff vs local PNG
  8. Cleanup     ─── delete any temp nodes accidentally created during the run
```

The eight stages must be **strictly sequential** for stages 3 → 4 → 5 (each consumes the previous stage's tokens). Stages 1, 2, 6, 7, 8 can be reordered as long as their preconditions hold.

---

## Stage 1 — Recon and Restate

Before any write:

```bash
lark-cli wiki +space-list --as user
lark-cli wiki +node-list --space-id "$SPACE_ID" --parent-node-token "$PARENT_TOKEN" --as user
```

**Critical:** restate the parent location to the user **before** creating any node:

> "I will create N child pages under `<parent_title>` (so they sit as siblings to `<peer_title>` if any). Confirm?"

This avoids the most common footgun in this skill: nesting boards under the wrong parent because the same name appears at multiple wiki levels. See `references/lark-wiki-caveats.md` §1.

## Stage 2 — Author SVGs

Each board in its own subdir under one timestamped root:

```
diagrams/YYYY-MM-DDTHHMMSS/
  01-<slug>/diagram.svg
  02-<slug>/diagram.svg
  ...
  09-<slug>/diagram.svg
```

Per-board author loop:

1. Write `diagram.svg`.
2. Render:
   ```bash
   npx -y @larksuite/whiteboard-cli@^0.2.11 -i diagram.svg -o diagram.png -f svg
   ```
3. Check overflow / overlap:
   ```bash
   npx -y @larksuite/whiteboard-cli@^0.2.11 -i diagram.svg -f svg --check
   ```
4. **Also run strict XML lint** — whiteboard-cli tolerates malformed XML that browsers and Claude Code preview reject:
   ```bash
   xmllint --noout diagram.svg
   ```
5. Export raw OpenAPI JSON for the writer stage:
   ```bash
   npx -y @larksuite/whiteboard-cli@^0.2.11 -i diagram.svg -f svg \
     --to openapi --format json > diagram.json
   ```

The SVG design rules that prevent re-work later are catalogued in `references/svg-authoring-caveats.md`. Read it once before authoring the first board; it covers duplicate-attribute parse errors, rotated-text overflow false positives, color/gradient contrast on dark fills, polyline routing around containers, and where to place cross-reference labels.

## Stage 3 — Batch Create Wiki Nodes

```bash
PARENT="<parent_node_token>"
SPACE="<space_id>"
titles=("01 <slug>" "02 <slug>" "03 <slug>" ...)

for t in "${titles[@]}"; do
  out=$(lark-cli wiki +node-create \
        --space-id "$SPACE" --parent-node-token "$PARENT" \
        --title "$t" --as user 2>/dev/null)
  node=$(echo "$out" | jq -r '.data.node_token')
  obj=$(echo  "$out" | jq -r '.data.obj_token')
  echo -e "$t\t$node\t$obj" >> /tmp/wiki_map.tsv
done
```

`lark-cli` writes informational lines to **stderr** and pure JSON to stdout, so `2>/dev/null | jq` works cleanly. Do not pipe combined stderr+stdout into `jq`; it will fail mid-loop.

## Stage 4 — Inject Whiteboard Blocks

For each docx, append a blank whiteboard block and capture its `block_token` (this is the whiteboard token used in Stage 5):

```bash
wb=$(lark-cli docs +update --api-version v2 --doc "$OBJ_TOKEN" \
       --command append --content '<whiteboard type="blank"></whiteboard>' \
       --as user 2>/dev/null \
     | jq -r '.data.document.new_blocks[0].block_token')
echo -e "$SUB\t$OBJ_TOKEN\t$wb" >> /tmp/wiki_map.tsv
```

**Use HTML for `--content`, never markdown.** v2 `docs +update` silently drops markdown content (returns `ok=true, new_blocks=0`) — see `references/lark-doc-caveats.md` §1.

## Stage 5 — Write SVG JSON Into Whiteboards

Newly created whiteboards are empty, so `--overwrite --dry-run` will report zero deletions; you may skip dry-run in batch mode for empty boards. For any board with existing content, dry-run is mandatory.

```bash
while IFS=$'\t' read -r sub obj wb; do
  ts=$(date +%s%N | cut -c1-13)
  ok=$(cat "diagrams/<ts>/$sub/diagram.json" \
       | lark-cli whiteboard +update \
           --whiteboard-token "$wb" \
           --source - --input_format raw \
           --idempotent-token "${ts}-${sub}" \
           --overwrite --as user 2>/dev/null \
       | jq -r '.ok')
  [ "$ok" = "true" ] && echo "✓ $sub" || { echo "✗ $sub"; break; }
  sleep 0.7
done < /tmp/wiki_map.tsv
```

Notes:

- `--source -` reads stdin (the raw OpenAPI JSON exported in Stage 2).
- `--idempotent-token` must be ≥10 chars; the `ts-sub` pattern gives a stable, debuggable handle.
- Do not parse `ok` from `tail -10`; the `"ok": true` line is at the top of the JSON. Pipe the full stdout to `jq -r '.ok'`.
- See `references/lark-whiteboard-caveats.md` for the dry-run rule, write-then-verify pattern, and how to recover from a partial batch.

## Stage 6 — Assemble Index Page

The index page is typically the **parent wiki node itself** (e.g. `50 Maps`), not a new child. Append HTML, not markdown, into its docx:

```bash
CONTENT=$(cat ./diagrams/<ts>/_index_page.html)
lark-cli docs +update --api-version v2 \
  --doc "$PARENT_OBJ_TOKEN" \
  --command append --content "$CONTENT" \
  --as user
```

Index page HTML template (paste into your authored file, replace placeholders):

```html
<h1>&lt;Project&gt; 架构图</h1>
<p><b>最后更新</b>:YYYY-MM-DD · 对应代码迁移至 <code>...</code></p>
<h2>速查目录</h2>
<p>▸ <b>01</b> <a href="WIKI_URL_01">&lt;Board 01 Title&gt;</a> —— 这张图能回答什么问题</p>
<p>▸ <b>02</b> <a href="WIKI_URL_02">&lt;Board 02 Title&gt;</a> —— ...</p>
<h2>维护约定</h2>
<p>▸ 任何大改动 → 编辑对应 SVG → <code>whiteboard +update --overwrite</code> → 更新顶部"最后更新"。</p>
```

**Three hard rules** that apply at this stage:

1. **Never set `--new-title`** on `docs +update`. It does not rename the existing wiki node; it creates a duplicate orphan node. Always omit it. See `references/lark-doc-caveats.md` §3.
2. **Never `--command overwrite` an existing docx** unless you want the v1 API to mark its root page deleted. Once overwritten via v2, the page is permanently v2-only. Prefer `append` on an empty docx, or `block_replace` on a specific block.
3. If the parent docx has any prior content (banner, links, AI writeback), copy what you want to keep into your HTML **before** appending — overwrite of any sort will not preserve it.

## Stage 7 — Verify

Sample 2-3 boards by exporting cloud renders and diffing visually against the local PNGs:

```bash
mkdir -p diagrams/<ts>/_wiki_verify
lark-cli whiteboard +query --whiteboard-token "$WB" \
  --output_as image --output diagrams/<ts>/_wiki_verify/<sub>.png \
  --as user
```

Open both PNGs side-by-side. The cloud render should be visually identical: same layout, same text, same connector routing, same color hierarchy. If any board diverges, the most likely cause is an unsupported decoration (`<radialGradient>`, `<filter>`, `<clipPath>`, `<mask>`) that whiteboard-cli silently rasterized rather than translated. Re-author with supported primitives only.

Mandatory whether dry-run was skipped or not. See `references/lark-whiteboard-caveats.md` §2.

## Stage 8 — Cleanup

If the pipeline produced any temp nodes (most often from accidental `--new-title` usage in earlier iterations), delete them:

```bash
# Use full URL form — raw node_token + --obj-type often reports "node not found"
lark-cli wiki +node-delete \
  --node-token "https://<host>/wiki/<NODE_TOKEN>" \
  --as user --yes
```

Also worth pairing the published board set with an `Artifacts` Base row per `lark-cli-devhub-whiteboard`. Keep the local SVG sources under `docs/devhub/whiteboards/<project>-<slug>.svg` (or any project-local path) so the source is reviewable with future code changes.

## Maintenance Contract

The published boards are only useful if they stay in sync with the code. Wire one of the following into your maintenance loop:

- **Manual:** Edit `diagrams/<ts>/0X-*/diagram.svg`, rerun Stages 2 → 5 for the affected board, bump the index page's "最后更新" line.
- **Hooked:** Add the SVG paths and the index page docx token to a project-level "architecture drift" precommit / PR check (out of scope for this skill).

Either way, the rule is one-direction-only: SVG source in repo is the truth, the whiteboard is a re-render. Never hand-edit the whiteboard in the Feishu UI without porting the edit back to the SVG, or the next batch write will silently revert it.

## See Also

- `lark-cli-devhub-whiteboard` — single-board good-use shapes and pairing with Base `Artifacts`.
- `lark-cli-devhub-whiteboard-loop` — safe-write loop for one board at a time.
- `lark-cli-devhub-docs-wiki` — wiki space conventions, the `00–90` numbered structure, and Base pairing rules.
- `references/svg-authoring-caveats.md` — six SVG authoring footguns that cause re-work.
- `references/lark-wiki-caveats.md` — wiki node creation, deletion, and the parent-clarification rule.
- `references/lark-whiteboard-caveats.md` — dry-run policy and the write-then-verify pattern.
- `references/lark-doc-caveats.md` — v1/v2 split, HTML-vs-markdown, and the `--new-title` trap.
