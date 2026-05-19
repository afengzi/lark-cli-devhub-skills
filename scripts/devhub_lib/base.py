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
        for field in table.get("fields", []):
            field_name = field.get("name")
            if not field_name:
                continue
            known = table_info.setdefault("fields", {})
            if field_name in known:
                continue
            try:
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
                        json.dumps(field, ensure_ascii=False),
                    ]
                )
                known[field_name] = str(find_first(created, {"field_id", "id"}) or field_name)
            except Exception as exc:
                known[field_name] = f"unverified:{field_name}"
                table_info.setdefault("field_warnings", {})[field_name] = str(exc)


def upsert_record(config: dict[str, Any], table: str, payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
    base = config["base"]
    table_id = base.get("tables", {}).get(table, {}).get("id", table)
    return run_lark(
        [
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
    )


def seed_records(config: dict[str, Any], seed: dict[str, Any]) -> None:
    for table, records in seed.items():
        if not isinstance(records, list):
            continue
        for record in records:
            upsert_record(config, table, record)
