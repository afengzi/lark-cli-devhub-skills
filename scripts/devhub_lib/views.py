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


def list_views(config: dict[str, Any], table: str) -> dict[str, str]:
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
    return {view_display_name(view): view_id(view) for view in _views_from_output(output) if view_display_name(view)}


def filter_existing_fields(config: dict[str, Any], table: str, fields: list[str]) -> list[str]:
    known = table_fields(config, table)
    if not known:
        return fields
    return [field for field in fields if field in known]


def filter_config_is_usable(config: dict[str, Any], table: str, filter_config: dict[str, Any]) -> bool:
    known = table_fields(config, table)
    if not known:
        return True
    for condition in filter_config.get("conditions", []):
        if isinstance(condition, list) and condition and condition[0] not in known:
            return False
    return True


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
            current_view_id = existing.get(name)
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
                        json.dumps({"name": name, "type": spec.get("type", "grid")}, ensure_ascii=False),
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
                        json.dumps({"visible_fields": visible_fields}, ensure_ascii=False),
                    ],
                    check=False,
                )
            filter_config = spec.get("filter")
            if isinstance(filter_config, dict) and filter_config_is_usable(config, table, filter_config):
                run_lark(
                    [
                        "base",
                        "+view-set-filter",
                        "--as",
                        "user",
                        "--base-token",
                        base["token"],
                        "--table-id",
                        table_id,
                        "--view-id",
                        current_view_id,
                        "--json",
                        json.dumps(filter_config, ensure_ascii=False),
                    ],
                    check=False,
                )
    return changed
