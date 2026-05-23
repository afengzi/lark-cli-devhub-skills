# Lark Wiki Caveats

Wiki-layer footguns specific to the architecture-batch pipeline.

## 1. Always Restate Parent Location Before Creating Nodes

**Symptom:** New child pages end up under the wrong parent. The user expected them as siblings of an existing index page; they were created as its grandchildren instead.

**Root cause:** Same-named or similarly-numbered nodes can exist at multiple levels of the wiki tree (`50 Maps`, `50 Maps/<project>: 架构图`, etc.). Reading `--parent-node-token` from a previous command's output without verifying its title leads to silent mis-nesting.

**Fix:** Run `+node-list` immediately before `+node-create` and verify the parent's title against the user's intent. Restate explicitly:

> "I will create N child pages under `<parent_title>` (which is at `<full_path>`). The new pages will be siblings to: `<peer_titles>`. Confirm?"

Then create. Do **not** chain `+node-list` → `+node-create` without the restate step when running batch operations under a deeply nested parent.

## 2. `+node-delete` Often Fails With raw token + `--obj-type docx`

**Symptom:**

```
{ "ok": false, "error": { "code": 131005, "message": "node not found" } }
```

even though `+node-list` clearly shows the node exists with that exact `node_token` and `obj_type: docx`.

**Root cause:** lark-cli's `+node-delete` resolution path occasionally fails to find nodes given as `--node-token <raw_token> --obj-type docx`. The internal lookup uses a different code path than `+node-list`.

**Fix:** Pass the full Lark URL form, which forces a URL-based resolution that takes a different code path:

```bash
# Reliable
lark-cli wiki +node-delete \
  --node-token "https://<host>/wiki/<NODE_TOKEN>" \
  --as user --yes

# Unreliable
lark-cli wiki +node-delete \
  --node-token "<NODE_TOKEN>" --obj-type docx \
  --space-id "<SPACE_ID>" --as user --yes
```

`--yes` is required because `+node-delete` is high-risk-write. Do not chain unattended retries without user confirmation.

## 3. Don't Use `docs +update --new-title` Expecting It to Rename a Wiki Node

**Symptom:** Set `--new-title "<new>"` on a `docs +update` of an existing docx that lives under a wiki node. Expected the wiki node title to update. Instead, the wiki space gains a new orphan node titled `<new>` (with the title set as requested) while the original node keeps its old title and the original `docx` is left in an inconsistent state.

**Root cause:** `docs +update --new-title` on a wiki-mounted docx creates a new wiki node rather than mutating the existing one. The behavior is documented elsewhere as a side effect, but it's surprising in the batch context — you end up with duplicate listings in `+node-list`.

**Fix:** Never combine `--new-title` with `docs +update` in this pipeline. To rename a wiki node:

```bash
# Requires wiki:node:update scope
lark-cli api POST \
  /open-apis/wiki/v2/spaces/<SPACE_ID>/nodes/<NODE_TOKEN>/update_title \
  --data '{"title":"<new_title>"}' --as user
```

If the scope is missing:

```bash
lark-cli auth login --scope "wiki:node:update" --no-wait --json
# pass the verification_url to the user, then continue after they confirm
```

If you've already created a duplicate orphan via this footgun, see Stage 8 of the main SKILL — delete it using the URL form from §2.

## 4. `lark-cli` Writes Status to stderr, JSON to stdout

When parsing output in a loop, separate streams:

```bash
out=$(lark-cli wiki +node-create ... 2>/dev/null)
node=$(echo "$out" | jq -r '.data.node_token')
```

Not:

```bash
# Will fail mid-loop because "Creating wiki node..." gets piped to jq
out=$(lark-cli wiki +node-create ... 2>&1 | tail -25)
```

`tail -N` also reliably truncates the `"ok": true` line at the top of the JSON, leading to silent loop bails.

## 5. Wiki Node Title vs Doc Internal Title

`lark-cli wiki +node-list` reports the **wiki node** title — what the user sees in the wiki tree. `lark-cli docs +fetch` shows the **doc's internal** `<title>` element, which is independent. They can diverge.

When in doubt, the wiki node title is what matters for navigation; the doc's internal title only shows as a heading inside the page. If you set `<h1>` in the page body, that's a third title, and it's the one most users actually read.

Resolution order to verify "is the title right":

1. Wiki tree → shows wiki node title.
2. Click in → shows doc internal title at very top.
3. Page body → first `<h1>` is the visible heading users associate with the page.

For consistency, all three should match for the index page. For sub-boards, the wiki node title and the `<h1>` (if any) are what matters; the doc internal title is rarely seen because the embedded whiteboard dominates the page.
