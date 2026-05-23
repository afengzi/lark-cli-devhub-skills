# Lark Whiteboard Caveats

Whiteboard-write footguns specific to the architecture-batch pipeline.

## 1. Empty Boards Can Skip dry-run

The base `lark-whiteboard` skill says "writing to a board with existing content **must** be preceded by `--overwrite --dry-run` to confirm the deletion count".

For freshly created blank whiteboards (Stage 4 of this pipeline appended `<whiteboard type="blank"/>` blocks moments before), there is nothing to delete. Dry-run would report zero deletions every time and adds a full network round-trip per board.

**Rule:** Skip `--dry-run` only when the board was created in the same pipeline run and has not been written to. If there's any doubt (e.g. you're resuming a partially completed batch), keep `--dry-run` in.

Belt-and-braces check before skipping en masse:

```bash
# Confirm zero deletions on the first board, then drop --dry-run for the rest
cat diagrams/<ts>/01-*/diagram.json | \
  lark-cli whiteboard +update \
    --whiteboard-token "$FIRST_WB" \
    --source - --input_format raw \
    --idempotent-token "$(date +%s)-probe" \
    --overwrite --dry-run --as user 2>&1 \
  | grep -i "nodes will be deleted" || echo "OK: no deletions reported"
```

## 2. Write-Then-Verify Is Mandatory

`--check` passing locally and `xmllint --noout` passing locally **do not guarantee** the cloud render matches the local PNG.

The whiteboard parser silently downgrades unsupported decorations (radial gradient, filter, clipPath, mask) — the upload succeeds and `--check` passes, but the rendered board diverges. The only reliable verification is round-trip:

```bash
# Per sampled board:
lark-cli whiteboard +query --whiteboard-token "$WB" \
  --output_as image --output "diagrams/<ts>/_wiki_verify/${sub}_cloud.png" \
  --as user

# Visually diff:
open "diagrams/<ts>/_wiki_verify/${sub}_cloud.png" \
     "diagrams/<ts>/${sub}/diagram.png"
```

**Minimum sample:** 2-3 boards per batch (first, middle, last). All N boards if any of:

- Any board's SVG used a primitive flagged in `svg-authoring-caveats.md` §7.
- Any board's SVG was substantially re-authored mid-batch (different style than the rest).
- This is the first time the pipeline ran for this project.

## 3. Partial-Batch Recovery

If Stage 5's write loop fails partway through (some boards written, some not), do not re-run from the top.

The failed board's `idempotent-token` was probably never accepted (otherwise it would have moved on). Recover by:

```bash
# 1. List which boards already have content (any new_blocks > 0 from the inject stage means the block exists; query confirms content)
for entry in $(cat /tmp/wiki_map.tsv); do
  sub=$(echo "$entry" | cut -f1)
  wb=$(echo "$entry"  | cut -f3)
  count=$(lark-cli whiteboard +query --whiteboard-token "$wb" \
            --output_as raw --as user 2>/dev/null \
          | jq '.data.nodes | length')
  echo "$sub  nodes=$count"
done

# 2. Re-run the write loop, skipping any board with nodes > 0
#    (or use --overwrite to forcibly replace; in that case dry-run becomes mandatory again)
```

Never run the write loop in parallel — `--idempotent-token` collisions across concurrent writes are not well-tested.

## 4. The `--source -` + `--input_format raw` Combo Is Load-Bearing

In Stage 5 you'll see:

```bash
cat diagrams/<ts>/$sub/diagram.json | \
  lark-cli whiteboard +update --whiteboard-token "$wb" \
    --source - --input_format raw \
    --idempotent-token "..." --overwrite --as user
```

- `--source -` reads JSON from stdin. Required because the JSON files are too large for `--source <file>` on some shells, and stdin pipes work consistently.
- `--input_format raw` tells the CLI the JSON is already OpenAPI-shaped (from `whiteboard-cli --to openapi --format json`). Without this, the CLI tries to re-parse the JSON as DSL or Mermaid and fails.

Don't substitute `--input_format mermaid` or `--input_format dsl` for SVG-derived content. The pipeline's source of truth is the SVG; the JSON is just its OpenAPI-node serialization.

## 5. Stable `block_token` Is Not Always Achievable

When updating an old architecture page, it's natural to want the whiteboard's `block_token` to stay stable so existing PR/Doc cross-references don't break.

If the page was previously written via v1 or `docs +update --command overwrite`, the original whiteboard block may already be unrecoverable (see `lark-doc-caveats.md` §2). In that case, accept token churn and update the cross-references in one shot. Track which token-stable boards you have so the next batch run knows whether to inject-fresh or update-in-place.

Rule of thumb:

- Page newly created by this pipeline → tokens stable for life unless explicitly overwritten.
- Page touched by `--command overwrite` → assume tokens churned; rewrite all references.
- Page never touched by v2 overwrite → v1 markdown updates may still work; tokens often stable.
