# Lark Doc Caveats

`docs +update` footguns specific to the architecture-batch pipeline.

## 1. v2 Content Must Be HTML, Not Markdown

**Symptom:** `lark-cli docs +update --api-version v2 --command append --content "# Heading\n\nParagraph"` returns `{"ok": true}` but `new_blocks` is `0` (or `null`) and the page remains empty. No error, no warning.

**Root cause:** v2's `--content` expects inline HTML tags. Plain markdown is silently dropped; no parse error surfaces.

**Fix:** Author the content as HTML directly:

```html
<h1>Title</h1>
<p><b>Bold</b> text and <code>inline code</code>.</p>
<p>Link: <a href="<URL>">Anchor text</a></p>
<h2>Subsection</h2>
<p>▸ Bullet-style paragraph (bullets are not natively supported, use ▸ glyphs).</p>
```

Supported tags (verified in v2):

- `<h1>`, `<h2>`, `<h3>`
- `<p>`
- `<b>`, `<i>`, `<code>`
- `<a href="...">`
- `<whiteboard type="blank"></whiteboard>` (special: creates a whiteboard block, returns `block_token` in response)

Markdown-style features that **do not** work in v2 `--content`:

- `#`/`##` headings → use `<h1>`/`<h2>`
- `**bold**` → use `<b>`
- `[text](url)` → use `<a href>`
- `` `code` `` → use `<code>`
- `>` blockquotes → fold into `<p>` with prefix glyph
- Markdown tables → render to a sequence of `<p>` lines (no native table tag works reliably)
- Bullet lists `- item` → use `<p>▸ item</p>` per bullet

If your content is already authored as markdown, keep it as a separate `.md` file in the repo for human reading, and maintain a parallel `.html` for the pipeline. Don't try to feed `.md` through this command.

## 2. v2 `--command overwrite` Breaks v1 Access Permanently

**Symptom:** After running `docs +update --api-version v2 --command overwrite ...` on a docx, any later attempt to edit it via `--api-version v1` returns:

```
"Document page has been deleted. This page can no longer be edited; choose another page or create a new document"
```

**Root cause:** v2 overwrite operates by deleting the v1 root page record and creating new v2 blocks. The doc remains accessible in v2 but is irreversibly cut off from v1.

**Fix:** Pick v1 or v2 for each docx at creation time and stay there for that doc's lifetime. The pipeline as a whole uses v2 throughout (Stages 4, 5, 6).

If you've already overwritten a doc and need to restore v1 compatibility, the only path is to create a new docx and migrate content over. There's no rollback.

## 3. `--new-title` Side Effect: Orphan Node Creation

**Symptom:** Passing `--new-title "<new>"` to `docs +update` (any command, but most commonly observed with `overwrite`) results in:

- The original docx ends up with the title set to `Untitled` or unchanged.
- A new wiki node appears at the parent level with `<new>` as its title, containing the content that should have been written to the original.

**Root cause:** `--new-title` on a wiki-mounted docx creates a sibling wiki node rather than renaming the current one. The content written by the same command lands in the new node.

**Fix:** **Never pass `--new-title` to `docs +update` in this pipeline.** If you need to rename a wiki node, see `lark-wiki-caveats.md` §3 for the proper `wiki:node:update` API call.

If you've already created an orphan this way:

```bash
# 1. Confirm the orphan via +node-list under the parent
lark-cli wiki +node-list --space-id "<SPACE>" --parent-node-token "<PARENT>" --as user \
  | jq -r '.data.nodes[] | "\(.title)\t\(.node_token)"'

# 2. Delete the orphan using the URL form (see lark-wiki-caveats.md §2)
lark-cli wiki +node-delete \
  --node-token "https://<host>/wiki/<ORPHAN_NODE_TOKEN>" \
  --as user --yes

# 3. Verify the original node still has its expected content via docs +fetch
```

## 4. `--command overwrite` Without Content Replacement Loses Everything

**Symptom:** Ran `docs +update --command overwrite` with `--content` pointing to a file path that resolved to empty (e.g. `--content "@/tmp/file.md"` where the path was wrong, or where lark-cli silently rejected the path).

The doc is now empty. Title is `Untitled`. Any embedded whiteboard `block_token`s are gone.

**Root cause:** `overwrite` deletes existing content **first**, then writes the new content. If the new content fails to parse or is empty, you're left with a stripped doc and no rollback.

**Fix:**

- Prefer `--command append` over `overwrite` whenever the docx is non-empty. Append + later block_delete is reversible; overwrite is not.
- If you must overwrite, dry-run first with `--dry-run` and inspect the response to confirm content was parsed:

```bash
lark-cli docs +update --api-version v2 --doc "<OBJ_TOKEN>" \
  --command overwrite --content "$CONTENT" \
  --as user --dry-run 2>&1 | jq '.data.parsed_blocks | length'
```

If `parsed_blocks` is 0 or missing, your content didn't parse — fix it before running without `--dry-run`.

- Capture the existing content before overwrite as a backup:

```bash
lark-cli docs +fetch --api-version v2 --doc "<OBJ_TOKEN>" --as user \
  | jq -r '.data.document.content' > /tmp/docx-backup-$(date +%s).html
```

## 5. `--content` Path Format Quirks

`--content "@<path>"` reads from a file. lark-cli requires:

- A **relative** path, not absolute. `--content "@<absolute>/file.html"` (anything starting with `/`) fails with `--file must be a relative path within the current directory`.
- The file must exist when the command runs. No glob expansion.

Workarounds:

- Use shell command substitution to inline the content: `--content "$(cat ./relative/path.html)"`. Faster for one-offs.
- Or copy the file under the current working directory first: `cp /abs/path.html ./tmp.html; lark-cli docs +update --content @./tmp.html`.

Inline (`$(cat ...)`) is preferred for the pipeline because it works regardless of where the script is invoked from. File-path form is fine for ad-hoc edits in a known cwd.

## 6. v1 Markdown Is Available But Avoid It

`docs +update --api-version v1` does accept Lark-flavored Markdown, including headings, lists, links, tables, code blocks. It's tempting to fall back to v1 when v2's HTML restrictions feel cumbersome.

Don't:

- v1 is documented as deprecated and "will be removed soon" by lark-cli help.
- Mixing v1 and v2 on the same docx triggers the deletion footgun (§2).
- v1 markdown tables render unpredictably across Feishu clients.

If you find yourself wanting v1 markdown, write HTML instead and use this skill's index-page HTML template as a starting point.
