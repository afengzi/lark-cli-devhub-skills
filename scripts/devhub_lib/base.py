from __future__ import annotations

import json
from typing import Any

from .io import find_first
from .lark import run_lark


def schema_tables(schema: dict[str, Any]) -> list[dict[str, Any]]:
    tables = schema.get("tables", schema)
    if isinstance(tables, dict):
        return [{"name": name, **value} for name, value in tables.items()]
    if isinstance(tables, list):
        return tables
    raise ValueError("base schema must contain a tables object or list")


def ensure_base(config: dict[str, Any]) -> None:
    base = config.setdefault("base", {"token": "", "url": "", "tables": {}})
    if base.get("token"):
        return
    created, _ = run_lark(["base", "+base-create", "--as", "user", "--name", "Dev Hub Base", "--time-zone", "Asia/Shanghai"])
    token = str(find_first(created, {"app_token", "base_token", "token"}) or "")
    if not token:
        raise RuntimeError("could not find base token in lark-cli output")
    base["token"] = token
    base["url"] = str(find_first(created, {"url", "link"}) or f"base:{token}")
    base.setdefault("tables", {})


def _field_list_from_output(output: dict[str, Any]) -> list[dict[str, Any]]:
    data = output.get("data", output)
    fields = data.get("fields", []) if isinstance(data, dict) else []
    return [field for field in fields if isinstance(field, dict)]


def field_display_name(field: dict[str, Any]) -> str:
    return str(field.get("name") or field.get("field_name") or "")


def field_id(field: dict[str, Any]) -> str:
    return str(field.get("id") or field.get("field_id") or field_display_name(field))


def is_deprecated_relation_field(name: str) -> bool:
    return name in {"Project Relation", "Area Relation", "Project Link", "Area Link"} or name.startswith("Related ")


def field_type_matches_schema(existing: str | None, field: dict[str, Any], relation_mode: str | None = None) -> bool:
    expected = field.get("type")
    if expected in (18, 21):
        if existing == str(expected):
            return True
        if existing != "link":
            return False
        wants_bidirectional = expected == 21
        existing_bidirectional = relation_mode == "duplex"
        return existing_bidirectional == wants_bidirectional
    return not expected or not existing or str(expected) == existing


def resolve_relation_target_tables(config: dict[str, Any], field: dict[str, Any]) -> dict[str, Any]:
    resolved = json.loads(json.dumps(field, ensure_ascii=False))
    if resolved.get("type") not in (18, 21):
        return resolved
    prop = resolved.get("property")
    if not isinstance(prop, dict):
        return resolved
    target = prop.get("table_id")
    if not isinstance(target, str) or target.startswith("tbl"):
        return resolved
    table_info = config.get("base", {}).get("tables", {}).get(target, {})
    table_id = table_info.get("id")
    if table_id:
        prop["table_id"] = table_id
    return resolved


def field_create_payload(config: dict[str, Any], field: dict[str, Any]) -> dict[str, Any]:
    resolved = resolve_relation_target_tables(config, field)
    if resolved.get("type") not in (18, 21):
        return resolved

    prop = resolved.get("property")
    if not isinstance(prop, dict):
        prop = {}
    payload: dict[str, Any] = {
        "type": "link",
        "name": field_display_name(resolved),
        "link_table": prop.get("table_id"),
        "bidirectional": resolved.get("type") == 21,
    }
    if resolved.get("description"):
        payload["description"] = resolved["description"]
    back_field_name = prop.get("back_field_name")
    if resolved.get("type") == 21 and back_field_name:
        payload["bidirectional_link_field_name"] = back_field_name
    return payload


def hydrate_existing_fields(config: dict[str, Any], table_name: str) -> None:
    base = config["base"]
    token = base["token"]
    table_info = base.setdefault("tables", {}).setdefault(table_name, {})
    table_id = table_info.get("id")
    if not table_id:
        return
    output, _ = run_lark(
        [
            "base",
            "+field-list",
            "--as",
            "user",
            "--base-token",
            token,
            "--table-id",
            table_id,
            "--limit",
            "100",
        ],
        check=False,
    )
    fields = _field_list_from_output(output)
    if not fields:
        return
    known = table_info.setdefault("fields", {})
    types = table_info.setdefault("field_types", {})
    relation_modes = table_info.setdefault("field_relation_modes", {})
    for field in fields:
        name = field_display_name(field)
        if not name:
            continue
        known[name] = str(field.get("id") or known.get(name) or name)
        if field.get("type"):
            types[name] = str(field["type"])
        if field.get("type") == "link":
            relation_modes[name] = "duplex" if field.get("bidirectional") else "single"


def list_live_fields(config: dict[str, Any], table_name: str) -> list[dict[str, Any]]:
    base = config["base"]
    table_info = base.get("tables", {}).get(table_name, {})
    table_id = table_info.get("id")
    if not table_id:
        return []
    output, _ = run_lark(
        [
            "base",
            "+field-list",
            "--as",
            "user",
            "--base-token",
            base["token"],
            "--table-id",
            table_id,
            "--limit",
            "100",
        ],
        check=False,
    )
    return _field_list_from_output(output)


def cleanup_deprecated_relation_fields(config: dict[str, Any], *, dry_run: bool = False) -> list[dict[str, str]]:
    base = config["base"]
    removed: list[dict[str, str]] = []
    for table_name, table_info in sorted(base.get("tables", {}).items()):
        if table_name in {"Projects", "Record Relations"}:
            continue
        table_id = table_info.get("id")
        if not table_id:
            continue
        for field in list_live_fields(config, table_name):
            name = field_display_name(field)
            if not is_deprecated_relation_field(name):
                continue
            item = {
                "table": table_name,
                "table_id": str(table_id),
                "field": name,
                "field_id": field_id(field),
                "status": "pending" if dry_run else "deleted",
            }
            removed.append(item)
            if dry_run:
                continue
            try:
                run_lark(
                    [
                        "base",
                        "+field-delete",
                        "--as",
                        "user",
                        "--base-token",
                        base["token"],
                        "--table-id",
                        str(table_id),
                        "--field-id",
                        item["field_id"],
                        "--yes",
                    ]
                )
            except Exception as exc:
                item["status"] = "failed"
                item["error"] = str(exc)
                continue
            for key in ("fields", "field_types", "field_relation_modes", "field_warnings"):
                value = table_info.get(key)
                if isinstance(value, dict):
                    value.pop(name, None)
    return removed


def create_tables_and_fields(config: dict[str, Any], schema: dict[str, Any]) -> None:
    base = config["base"]
    token = base["token"]
    table_map = base.setdefault("tables", {})
    for table in schema_tables(schema):
        table_name = table["name"]
        table_info = table_map.setdefault(table_name, {})
        if not table_info.get("id"):
            created, _ = run_lark(["base", "+table-create", "--as", "user", "--base-token", token, "--name", table_name])
            table_info["id"] = str(find_first(created, {"table_id", "id"}) or table_name)
        hydrate_existing_fields(config, table_name)

    for table in schema_tables(schema):
        table_name = table["name"]
        table_info = table_map.setdefault(table_name, {})
        for field in table.get("fields", []):
            field_name = field_display_name(field)
            if not field_name:
                continue
            known = table_info.setdefault("fields", {})
            types = table_info.setdefault("field_types", {})
            relation_modes = table_info.setdefault("field_relation_modes", {})
            known_value = str(known.get(field_name) or "")
            if known_value and not known_value.startswith("unverified:"):
                existing_type = types.get(field_name)
                if not field_type_matches_schema(existing_type, field, relation_modes.get(field_name)):
                    table_info.setdefault("field_warnings", {})[field_name] = (
                        f"existing field type is {existing_type}; schema expects {field.get('type')}. "
                        "Dev Hub will not mutate existing field types automatically."
                    )
                continue
            try:
                field_to_create = field_create_payload(config, field)
                created, _ = run_lark(
                    [
                        "base",
                        "+field-create",
                        "--as",
                        "user",
                        "--base-token",
                        token,
                        "--table-id",
                        table_info["id"],
                        "--json",
                        json.dumps(field_to_create, ensure_ascii=False),
                    ]
                )
                known[field_name] = str(find_first(created, {"field_id", "id"}) or field_name)
                table_info.setdefault("field_warnings", {}).pop(field_name, None)
            except Exception as exc:
                known[field_name] = f"unverified:{field_name}"
                table_info.setdefault("field_warnings", {})[field_name] = str(exc)


def cell_text(value: Any) -> str:
    if isinstance(value, list):
        return ",".join(cell_text(item) for item in value)
    if isinstance(value, dict):
        for key in ("text", "name", "value", "title", "id", "record_id"):
            if value.get(key) is not None:
                return str(value[key])
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value or "")


def table_fields(config: dict[str, Any], table: str) -> set[str]:
    fields = config.get("base", {}).get("tables", {}).get(table, {}).get("fields", {})
    return {str(field) for field in fields}


def filter_known_payload_fields(config: dict[str, Any], table: str, payload: dict[str, Any]) -> dict[str, Any]:
    fields = table_fields(config, table)
    if not fields:
        return dict(payload)
    return {field: value for field, value in payload.items() if field in fields}


def find_matching_record_id(config: dict[str, Any], table: str, payload: dict[str, Any], match_fields: list[str]) -> str:
    if not match_fields:
        return ""
    base = config["base"]
    table_id = base.get("tables", {}).get(table, {}).get("id", table)
    keyword = cell_text(payload.get(match_fields[0], ""))
    if not keyword:
        return ""
    output, _ = run_lark(
        [
            "base",
            "+record-search",
            "--as",
            "user",
            "--base-token",
            base["token"],
            "--table-id",
            table_id,
            "--json",
            json.dumps(
                {
                    "keyword": keyword,
                    "search_fields": [match_fields[0]],
                    "select_fields": match_fields,
                    "limit": 200,
                },
                ensure_ascii=False,
            ),
            "--format",
            "json",
        ],
        check=False,
    )
    data = output.get("data", {}) if isinstance(output, dict) else {}
    fields = data.get("fields", [])
    rows = data.get("data", [])
    record_ids = data.get("record_id_list", [])
    for record_id, row in zip(record_ids, rows):
        values = dict(zip(fields, row))
        if all(cell_text(values.get(field)) == cell_text(payload.get(field)) for field in match_fields):
            return str(record_id)
    return ""


def list_records_for_match(
    config: dict[str, Any],
    table: str,
    *,
    match_fields: list[str],
    select_fields: list[str],
) -> dict[tuple[str, ...], tuple[str, dict[str, Any]]]:
    base = config["base"]
    table_id = base.get("tables", {}).get(table, {}).get("id", table)
    result: dict[tuple[str, ...], tuple[str, dict[str, Any]]] = {}
    offset = 0
    while True:
        args = [
            "base",
            "+record-list",
            "--as",
            "user",
            "--base-token",
            base["token"],
            "--table-id",
            table_id,
            "--limit",
            "200",
            "--offset",
            str(offset),
            "--format",
            "json",
        ]
        for field in select_fields:
            args.extend(["--field-id", field])
        output, _ = run_lark(args, check=False)
        data = output.get("data", {}) if isinstance(output, dict) else {}
        output_fields = data.get("fields", [])
        rows = data.get("data", [])
        record_ids = data.get("record_id_list", [])
        for record_id, row in zip(record_ids, rows):
            values = dict(zip(output_fields, row))
            key = tuple(cell_text(values.get(field)) for field in match_fields)
            result[key] = (str(record_id), values)
        if not data.get("has_more"):
            break
        offset += len(rows) or 200
    return result


def records_equal(existing: dict[str, Any], payload: dict[str, Any]) -> bool:
    for field, value in payload.items():
        if cell_text(existing.get(field)) != cell_text(value):
            return False
    return True


def batch_create_records(config: dict[str, Any], table: str, payloads: list[dict[str, Any]]) -> None:
    if not payloads:
        return
    payloads = [filter_known_payload_fields(config, table, payload) for payload in payloads]
    base = config["base"]
    table_id = base.get("tables", {}).get(table, {}).get("id", table)
    fields: list[str] = []
    for payload in payloads:
        for field in payload:
            if field not in fields:
                fields.append(field)
    for start in range(0, len(payloads), 200):
        chunk = payloads[start : start + 200]
        rows = [[payload.get(field) for field in fields] for payload in chunk]
        run_lark(
            [
                "base",
                "+record-batch-create",
                "--as",
                "user",
                "--base-token",
                base["token"],
                "--table-id",
                table_id,
                "--json",
                json.dumps({"fields": fields, "rows": rows}, ensure_ascii=False),
            ]
        )


def batch_upsert_records(
    config: dict[str, Any],
    table: str,
    payloads: list[dict[str, Any]],
    *,
    match_fields: list[str] | None = None,
) -> None:
    if not payloads:
        return
    payloads = [filter_known_payload_fields(config, table, payload) for payload in payloads]
    match_fields = match_fields or []
    if not match_fields:
        batch_create_records(config, table, payloads)
        return

    select_fields = list(match_fields)
    for payload in payloads:
        for field in payload:
            if field not in select_fields:
                select_fields.append(field)
    existing = list_records_for_match(config, table, match_fields=match_fields, select_fields=select_fields)
    to_create: list[dict[str, Any]] = []
    for payload in payloads:
        key = tuple(cell_text(payload.get(field)) for field in match_fields)
        matched = existing.get(key)
        if not matched:
            to_create.append(payload)
            continue
        record_id, existing_values = matched
        if records_equal(existing_values, payload):
            continue
        upsert_record(config, table, payload, match_fields=match_fields, record_id=record_id)
    batch_create_records(config, table, to_create)


def upsert_record(
    config: dict[str, Any],
    table: str,
    payload: dict[str, Any],
    *,
    match_fields: list[str] | None = None,
    record_id: str = "",
) -> tuple[dict[str, Any], str]:
    payload = filter_known_payload_fields(config, table, payload)
    base = config["base"]
    table_id = base.get("tables", {}).get(table, {}).get("id", table)
    args = [
        "base",
        "+record-upsert",
        "--as",
        "user",
        "--base-token",
        base["token"],
        "--table-id",
        table_id,
        "--json",
        json.dumps(payload, ensure_ascii=False),
    ]
    if not record_id:
        record_id = find_matching_record_id(config, table, payload, match_fields or [])
    if record_id:
        args.extend(["--record-id", record_id])
    output, stdout = run_lark(args)
    if record_id:
        output.setdefault("_record_id", record_id)
    return output, stdout


def seed_records(config: dict[str, Any], seed: dict[str, Any]) -> None:
    for table, records in seed.items():
        if not isinstance(records, list):
            continue
        for record in records:
            upsert_record(config, table, record)
