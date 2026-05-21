# Feishu Base Relation Fields

Use this only for custom schemas that explicitly need native Feishu Base relation fields. The default Dev Hub model keeps business tables lightweight and writes cross-record graph edges into `Record Relations`.

## Official Model

- Single-direction relation: official field type `18`; lark-cli shortcut type is `link` with `bidirectional: false`.
- Bidirectional relation: official field type `21`; lark-cli shortcut type is `link` with `bidirectional: true`.
- Record cell values for writable relation fields are arrays of target records: `[{"id":"rec_xxx"}]`.
- Official docs mark bidirectional relation cell writes as limited; use single-direction relations when an agent must write values reliably.

## Safe Workflow

1. Read live fields first:

```bash
lark-cli base +field-list --base-token "$BASE_TOKEN" --table-id "$TABLE_ID" --as user
```

2. Do not convert an existing `text` field such as `Related Tasks` into `link`. `+field-update` does not support changing non-link fields into link fields safely. Create a new field instead.

3. Create a single-direction relation field:

```bash
lark-cli base +field-create \
  --base-token "$BASE_TOKEN" \
  --table-id "$SOURCE_TABLE_ID" \
  --json '{"name":"Related Tasks Link","type":"link","link_table":"tbl_target","bidirectional":false}' \
  --as user
```

4. Write relation values by target `record_id`, not by title:

```bash
lark-cli base +record-upsert \
  --base-token "$BASE_TOKEN" \
  --table-id "$SOURCE_TABLE_ID" \
  --record-id "$SOURCE_RECORD_ID" \
  --json '{"Related Tasks Link":[{"id":"rec_target"}]}' \
  --as user
```

5. Read back both structure and value:

```bash
lark-cli base +field-list --base-token "$BASE_TOKEN" --table-id "$SOURCE_TABLE_ID" --as user
lark-cli base +record-get --base-token "$BASE_TOKEN" --table-id "$SOURCE_TABLE_ID" --record-id "$SOURCE_RECORD_ID" --as user --format json
```

The field must read back as `type: "link"` with the expected `link_table`; the cell must read back as objects containing target `id` values.

## Default Dev Hub Guidance

- Prefer `Record Relations` for AI-readable graph edges.
- Keep old text fields only as human-readable summaries when migrating an existing Base.
- Use native relation fields only when the user wants visual Base relations, lookup-style browsing, or a custom schema that depends on linked cells.
