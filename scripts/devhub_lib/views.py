from __future__ import annotations

import json
from typing import Any

from .base import table_fields
from .io import find_first
from .lark import run_lark


def view_display_name(view: dict[str, Any]) -> str:
    return str(view.get("name") or view.get("view_name") or "")


def view_id(view: dict[str, Any]) -> str:
    return str(view.get("id") or view.get("view_id") or view_display_name(view))


def _views_from_output(output: dict[str, Any]) -> list[dict[str, Any]]:
    data = output.get("data", output)
    if not isinstance(data, dict):
        return []
    items = data.get("items") or data.get("views") or data.get("data") or []
    return [item for item in items if isinstance(item, dict)]


def list_views(config: dict[str, Any], table: str) -> dict[str, dict[str, str]]:
    base = config["base"]
    table_id = base.get("tables", {}).get(table, {}).get("id")
    if not table_id:
        return {}
    output, _ = run_lark(
        [
            "base",
            "+view-list",
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
    return {
        view_display_name(view): {"id": view_id(view), "type": str(view.get("type") or "")}
        for view in _views_from_output(output)
        if view_display_name(view)
    }


def filter_existing_fields(config: dict[str, Any], table: str, fields: list[str]) -> list[str]:
    known = table_fields(config, table)
    if not known:
        return fields
    return [field for field in fields if field in known]


def table_field_map(config: dict[str, Any], table: str) -> dict[str, str]:
    fields = config.get("base", {}).get("tables", {}).get(table, {}).get("fields", {})
    return {str(name): str(field_id) for name, field_id in fields.items()}


def field_id_for(config: dict[str, Any], table: str, field: str) -> str:
    return table_field_map(config, table).get(field, field)


def translate_visible_fields(config: dict[str, Any], table: str, fields: list[str]) -> list[str]:
    return [field_id_for(config, table, field) for field in fields]


def filter_config_is_usable(config: dict[str, Any], table: str, filter_config: dict[str, Any]) -> bool:
    known = table_fields(config, table)
    if not known:
        return True
    for condition in filter_config.get("conditions", []):
        if isinstance(condition, list) and condition and condition[0] not in known:
            return False
    return True


def translate_filter_config(config: dict[str, Any], table: str, payload: dict[str, Any]) -> dict[str, Any]:
    translated = json.loads(json.dumps(payload, ensure_ascii=False))
    conditions = translated.get("conditions", [])
    if isinstance(conditions, list):
        for condition in conditions:
            if isinstance(condition, list) and condition:
                condition[0] = field_id_for(config, table, str(condition[0]))
    return translated


def field_config_is_usable(config: dict[str, Any], table: str, payload: dict[str, Any], keys: list[str]) -> bool:
    known = table_fields(config, table)
    if not known:
        return True
    return all(not payload.get(key) or payload[key] in known for key in keys)


def list_field_config_is_usable(config: dict[str, Any], table: str, payload: dict[str, Any], key: str) -> bool:
    known = table_fields(config, table)
    if not known:
        return True
    items = payload.get(key, [])
    return all(isinstance(item, dict) and item.get("field") in known for item in items)


def translate_field_config(config: dict[str, Any], table: str, payload: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    translated = json.loads(json.dumps(payload, ensure_ascii=False))
    for key in keys:
        if translated.get(key):
            translated[key] = field_id_for(config, table, str(translated[key]))
    return translated


def translate_list_field_config(config: dict[str, Any], table: str, payload: dict[str, Any], key: str) -> dict[str, Any]:
    translated = json.loads(json.dumps(payload, ensure_ascii=False))
    for item in translated.get(key, []):
        if isinstance(item, dict) and item.get("field"):
            item["field"] = field_id_for(config, table, str(item["field"]))
    return translated


def set_view_config(config: dict[str, Any], table: str, table_id: str, view_id_value: str, command: str, payload: dict[str, Any]) -> None:
    run_lark(
        [
            "base",
            command,
            "--as",
            "user",
            "--base-token",
            config["base"]["token"],
            "--table-id",
            table_id,
            "--view-id",
            view_id_value,
            "--json",
            json.dumps(payload, ensure_ascii=False),
        ],
        check=False,
    )


def ensure_base_views(config: dict[str, Any], views: dict[str, Any]) -> list[dict[str, str]]:
    base = config["base"]
    changed: list[dict[str, str]] = []
    for table, view_specs in views.items():
        table_id = base.get("tables", {}).get(table, {}).get("id")
        if not table_id or not isinstance(view_specs, list):
            continue
        existing = list_views(config, table)
        table_views = base.setdefault("tables", {}).setdefault(table, {}).setdefault("views", {})
        for spec in view_specs:
            if not isinstance(spec, dict):
                continue
            name = str(spec.get("name") or "")
            if not name:
                continue
            view_type = str(spec.get("type", "grid"))
            current = existing.get(name, {})
            current_view_id = current.get("id", "")
            if current_view_id and current.get("type") and current.get("type") != view_type:
                run_lark(
                    [
                        "base",
                        "+view-delete",
                        "--as",
                        "user",
                        "--base-token",
                        base["token"],
                        "--table-id",
                        table_id,
                        "--view-id",
                        current_view_id,
                        "--yes",
                    ],
                    check=False,
                )
                current_view_id = ""
            if not current_view_id:
                created, _ = run_lark(
                    [
                        "base",
                        "+view-create",
                        "--as",
                        "user",
                        "--base-token",
                        base["token"],
                        "--table-id",
                        table_id,
                        "--json",
                        json.dumps({"name": name, "type": view_type}, ensure_ascii=False),
                    ]
                )
                current_view_id = str(find_first(created, {"view_id", "id"}) or name)
                changed.append({"table": table, "view": name, "action": "created"})
            table_views[name] = current_view_id
            visible_fields = filter_existing_fields(config, table, [str(field) for field in spec.get("visible_fields", [])])
            if visible_fields:
                run_lark(
                    [
                        "base",
                        "+view-set-visible-fields",
                        "--as",
                        "user",
                        "--base-token",
                        base["token"],
                        "--table-id",
                        table_id,
                        "--view-id",
                        current_view_id,
                        "--json",
                        json.dumps({"visible_fields": translate_visible_fields(config, table, visible_fields)}, ensure_ascii=False),
                    ],
                    check=False,
                )
            group_config = spec.get("group")
            if isinstance(group_config, dict) and list_field_config_is_usable(config, table, group_config, "group_config"):
                set_view_config(config, table, table_id, current_view_id, "+view-set-group", translate_list_field_config(config, table, group_config, "group_config"))
            sort_config = spec.get("sort")
            if isinstance(sort_config, dict) and list_field_config_is_usable(config, table, sort_config, "sort_config"):
                set_view_config(config, table, table_id, current_view_id, "+view-set-sort", translate_list_field_config(config, table, sort_config, "sort_config"))
            card_config = spec.get("card")
            if isinstance(card_config, dict) and field_config_is_usable(config, table, card_config, ["cover_field"]):
                set_view_config(config, table, table_id, current_view_id, "+view-set-card", translate_field_config(config, table, card_config, ["cover_field"]))
            timebar_config = spec.get("timebar")
            if isinstance(timebar_config, dict) and field_config_is_usable(config, table, timebar_config, ["start_time", "end_time", "title"]):
                set_view_config(config, table, table_id, current_view_id, "+view-set-timebar", translate_field_config(config, table, timebar_config, ["start_time", "end_time", "title"]))
            filter_config = spec.get("filter")
            if isinstance(filter_config, dict) and filter_config_is_usable(config, table, filter_config):
                set_view_config(config, table, table_id, current_view_id, "+view-set-filter", translate_filter_config(config, table, filter_config))
    return changed
