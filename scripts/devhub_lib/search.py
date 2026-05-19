from __future__ import annotations

import json
from typing import Any, Callable

from .lark import run_lark


FULL_RECALL_TABLES = [
    "Tasks",
    "Bugfixes",
    "AI Runs",
    "Releases",
    "Decisions",
    "Project Facts",
    "Artifacts",
    "Pitfalls",
    "Playbooks",
    "Areas",
]

SEARCH_FIELDS = ["Title", "AI Summary", "Search Keywords"]
SELECT_FIELDS = ["Title", "Project", "Area", "Status", "AI Summary", "Search Keywords", "Source URL"]


def build_record_search_query(query: str) -> dict[str, Any]:
    return {
        "keyword": query,
        "search_fields": SEARCH_FIELDS,
        "select_fields": SELECT_FIELDS,
        "limit": 10,
    }


def search_devhub(
    config: dict[str, Any],
    project: str,
    query: str,
    *,
    tables: list[str] | None = None,
    run_lark_func: Callable[..., tuple[dict[str, Any], str]] = run_lark,
) -> dict[str, Any]:
    base = config.get("base", {})
    token = base.get("token")
    if not token:
        raise RuntimeError("Dev Hub Base is not configured yet.")

    requested = tables or FULL_RECALL_TABLES
    results: dict[str, Any] = {}
    for table in requested:
        table_id = base.get("tables", {}).get(table, {}).get("id", table)
        try:
            data, stdout = run_lark_func(
                [
                    "base",
                    "+record-search",
                    "--as",
                    "user",
                    "--base-token",
                    token,
                    "--table-id",
                    table_id,
                    "--json",
                    json.dumps(build_record_search_query(query), ensure_ascii=False),
                    "--format",
                    "json",
                ],
                check=False,
            )
            results[table] = data if data else stdout.strip()
        except Exception as exc:
            results[table] = {"error": str(exc)}

    missing = [table for table in FULL_RECALL_TABLES if table not in requested]
    return {
        "project": project,
        "query": query,
        "coverage": requested,
        "missing_for_full_recall": missing,
        "results": results,
    }
