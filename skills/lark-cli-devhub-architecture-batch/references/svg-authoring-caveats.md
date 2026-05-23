# SVG Authoring Caveats

Footguns that bit a real 9-board architecture batch. Each entry: symptom → root cause → fix.

## 1. Duplicate Attributes on One Element (parsererror)

**Symptom:** whiteboard-cli `--check` returns 0 errors, PNG renders fine, but the SVG fails to load in browsers / Claude Code preview with:

```
error on line N at column M: Attribute font-family redefined
```

**Root cause:** A `<text>` (or other element) was written with two attributes of the same name, e.g.:

```xml
<text font-family="Noto Sans SC" font-size="11" font-family="monospace">…</text>
```

whiteboard-cli's lenient parser keeps the last one; strict XML parsers reject the whole document.

**Fix:** Add `xmllint --noout diagram.svg` as a mandatory post-write step. Failed lint blocks the board from advancing to render.

```bash
for f in diagrams/<ts>/*/diagram.svg; do xmllint --noout "$f" || echo "FAIL: $f"; done
```

## 2. Rotated Text Triggers False `text-overflow` Errors

**Symptom:** `--check` reports `text-overflow ... overflows container by N px` even though the text visually fits.

**Root cause:** `--check` measures the unrotated horizontal bounding box. A `<text transform="rotate(-90 ...)">` 12-character Latin string is computed as `~80px wide` against whatever container its x/y falls inside — usually a wrong one.

**Fix:** Don't rotate `<text>`. If you need a side label, use a short horizontal label aligned to the connector, or break the label across lines with `<tspan dy="...">`.

## 3. Text Color Disappears Into Gradient Stops

**Symptom:** A line of body text inside a colored panel is unreadable in the rendered PNG. Looks fine in raw SVG inspection.

**Root cause:** Text color was picked from the same hue family as the panel's `linearGradient` stop colors. Examples that bit us:

- Text `#fb923c` (orange) on a tool-loop yellow gradient `#facc15 → #ca8a04` — both warm, no contrast.
- Text `#ea580c` (deep orange) on a volcano panel `#fb923c → #ea580c` — text matches the bottom stop exactly.

**Fix:** Pair contrast deliberately:

- Dark fill / dark gradient → use a light text color (e.g. `#fed7aa`, `#fff7ed`, `#ecfdf5`).
- Light fill / pastel gradient → use a dark text color (e.g. `#7c2d12`, `#451a03`, `#0f172a`).

When in doubt, drop the text into the PNG output and squint at 25% zoom. If you can't tell where the words end, contrast is too low.

## 4. Connectors Must Route Around Containers, Not Through Them

**Symptom:** A horizontal arrow visually passes through the middle of a labeled container, with the connector line painting over the text inside.

**Root cause:** Used a direct line `points="X1,Y X2,Y"` where the y-coordinate intersects an intermediate container's vertical extent.

**Fix:** Use orthogonal polylines that route over or under blocking containers:

```xml
<!-- Wrong: horizontal line slices through Context box -->
<polyline points="1380,230 880,230" ... />

<!-- Right: jog up above all blocking boxes, then back down -->
<polyline points="1380,210 1380,150 690,150 690,210" ... />
```

The label that follows the arrow should sit on the horizontal segment of the polyline, not on the original direct path.

## 5. Cross-Reference Labels Belong on Header Rows, Not Content Rows

**Symptom:** A "see figure 03" tag, placed at the right end of a long features list (e.g. `· A · B · C · D · IntentClassifier · see figure 03`), visually collides with the rightmost feature.

**Root cause:** The features list expands further than expected; the tag is on the same line.

**Fix:** Reserve the **container's header row** or **top-right corner** for cross-references. Body rows are for content only.

```xml
<!-- Wrong: tag on same row as content -->
<text x="680" y="582">+ Memory · Persona · ContextBuilder · ... · IntentClassifier</text>
<text x="1230" y="582" fill="#9d174d">详见图 03</text>

<!-- Right: tag on header row, away from content row -->
<text x="680" y="557" font-weight="600">agents/</text>
<text x="780" y="557">决策层 — MainAgent · ChatAgent · TeachingAgent</text>
<text x="1340" y="557" font-weight="600" fill="#9d174d">详见图 03 ▸</text>
<text x="680" y="582">+ Memory · Persona · ContextBuilder · ...</text>
```

## 6. Batch Directory Convention

When authoring N >= 3 boards in one batch, give each its own subdirectory under a single timestamped root:

```
diagrams/YYYY-MM-DDTHHMMSS/
  01-<slug>/
    diagram.svg
    diagram.png    ← whiteboard-cli render
    diagram.json   ← exported OpenAPI nodes for the writer stage
  02-<slug>/
    ...
  _index_page.html  ← optional, for Stage 6 index assembly
  _wiki_verify/     ← optional, for Stage 7 sample cloud-vs-local diff
    01-<slug>_from_wiki.png
```

Benefits:

- Each board independently rendered, checked, exported, and (re)written.
- Failed validation on one board doesn't block the others.
- Re-rendering a single board after edits is one targeted command, not a whole-batch rerun.
- The flat `_wiki_verify/` sink keeps Stage 7 diffs colocated for one-shot visual scan.

## 7. Hard Constraints on SVG Primitives (Reminder)

whiteboard's SVG parser **does not** support and will silently rasterize or break on:

- `<radialGradient>`
- `<filter>` (including drop shadows)
- `<pattern>`
- `<clipPath>`
- `<mask>`

It tolerates but downgrades:

- `skewX`, `skewY`, `matrix(...)` — avoid for new authoring.

It fully supports:

- `<rect>`, `<circle>`, `<ellipse>`, `<polygon>`, `<line>`, `<polyline>`, `<path>`
- `<text>`, `<tspan>` (font hardcoded to Noto Sans SC by the parser)
- `<g>`, `<a>`, `<use>` referencing `<symbol>`
- `<linearGradient>` (radial is not supported — single hue + opacity is your gradient-equivalent escape)
- `translate`, `rotate`, `scale` transforms

If a board needs a visual effect that hits an unsupported primitive, replace it with a supported approximation rather than letting whiteboard-cli silently downgrade — silent downgrades are how Stage 7's cloud-vs-local PNG diff diverges.
