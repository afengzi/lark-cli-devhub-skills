# Base Field Type Policy

Dev Hub Base keeps the default schema lightweight and AI-readable. Prefer fields that are easy for agents to write reliably and easy for humans to filter or scan.

## Supported Field Types

The lark-cli Base shortcut layer supports these field types for schema work:

- `text`
- `number`
- `select`
- `datetime`
- `created_at` / `updated_at`
- `user` / `group_chat`
- `created_by` / `updated_by`
- `link`
- `formula`
- `lookup`
- `auto_number`
- `attachment`
- `location`
- `checkbox`

URL, email, phone, and barcode fields are modeled as `text` fields with `style.type`.

## Default Decisions

| Field family | Default type | Reason |
|---|---|---|
| `Source URL`, `Repo URL`, `Wiki URL`, `Feishu Task URL` | `text` with `style.type=url` | Human-clickable while agents can keep writing strings. |
| `Receipt Path`, `Outbox Path` | `text` | Local filesystem paths are not URLs. |
| `Commit SHA`, `Feishu Task GUID`, record IDs | `text` | Identifiers are strings, not numbers. Use `Source URL` for clickable commit/task links. |
| `Search Keywords` | `text` | Open vocabulary for AI recall; select options would expand too quickly. |
| `Tags` | `text` for now | Flexible AI-generated labels. Consider multi-select only after defining a controlled tag vocabulary. |
| Evidence and narrative fields | `text` | These store summaries, commands, root causes, and long notes. |
| `Status`, `Priority`, `Risk Level`, `Severity`, `Artifact Type`, `Relation Type`, `Writeback Status` | single `select` | Controlled workflow state and grouping. |
| `Last Reviewed At`, `Due At`, `Started At`, `Completed At`, `Last Seen At`, `Pushed At`, `Created At` | `datetime` with `yyyy-MM-dd HH:mm` | Calendar/gantt views and consistent scanning. |
| `ID` | `auto_number` | Stable human-readable row number. |

## Deferred Options

- `Tags` can become `select` with `multiple=true` when the project has a controlled tag set.
- Attachments can be added as separate `Evidence Files` fields, but file upload must use `lark-cli base +record-upload-attachment`, not normal record upsert.
- `Owner` can become a `user` field only when the workflow has reliable Feishu `open_id` resolution. Until then, text is safer.
- Commit-specific clickable links should use `Source URL` or a future `Commit URL` URL-styled text field; keep `Commit SHA` plain text.

## Native Relation Fields

The default Dev Hub schema uses the `Record Relations` table for graph edges instead of adding many relation columns to business tables. Native Feishu Base relation fields are still valid for custom schemas.

- Official single-direction relation type: `18`.
- Official bidirectional relation type: `21`.
- lark-cli shortcut field payload: `{"type":"link","name":"Related Tasks Link","link_table":"tbl_target","bidirectional":false}`.
- Writable cell value: `[{"id":"rec_target"}]`.

Do not convert an existing text `Related ...` field into a relation field. Create a new `... Link` field, write record ids into it, and keep the text field only as a readable summary during migration.
