from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .base import create_tables_and_fields, ensure_base, seed_records
from .config import load_config, redact_resource_summary, save_config
from .io import load_json
from .lark import run_lark
from .records import write_outbox
from .wiki_docs import create_artifacts, ensure_wiki


def command_preflight(_args: Any) -> int:
    for cmd in [
        ["doctor", "--offline"],
        ["auth", "status", "--verify"],
        ["auth", "scopes"],
    ]:
        _data, stdout = run_lark(cmd)
        print(stdout.strip())
    return 0


def command_provision(args: Any) -> int:
    config: dict[str, Any] = {}
    config_loaded = False
    try:
        config = load_config()
        config_loaded = True
        schema = load_json(Path(args.schema))
        seed = load_json(Path(args.seed))
        ensure_wiki(config)
        ensure_base(config)
        create_tables_and_fields(config, schema)
        save_config(config)
        seed_records(config, seed)
        create_artifacts(config)
        save_config(config)
        print(json.dumps({"ok": True, **redact_resource_summary(config)}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        if config_loaded:
            save_config(config)
        outbox = write_outbox(
            Path.cwd(),
            "provision",
            {
                "operation": "provision",
                "schema_path": str(Path(args.schema)),
                "seed_path": str(Path(args.seed)),
                "resource_summary": redact_resource_summary(config),
            },
            str(exc),
        )
        print(json.dumps({"ok": False, "outbox": str(outbox), "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


def command_search(args: Any) -> int:
    config = load_config()
    if not config.get("base", {}).get("token"):
        print("Dev Hub Base is not configured yet.", file=sys.stderr)
        return 1
    results: dict[str, Any] = {}
    for table in ["Pitfalls", "Bugfixes", "Playbooks", "Decisions", "Areas"]:
        table_id = config["base"].get("tables", {}).get(table, {}).get("id", table)
        query = {
            "keyword": args.query,
            "search_fields": ["Title", "AI Summary", "Search Keywords"],
            "select_fields": ["Title", "Project", "Area", "AI Summary", "Search Keywords"],
            "limit": 10,
        }
        try:
            data, stdout = run_lark(
                [
                    "base",
                    "+record-search",
                    "--as",
                    "user",
                    "--base-token",
                    config["base"]["token"],
                    "--table-id",
                    table_id,
                    "--json",
                    json.dumps(query, ensure_ascii=False),
                    "--format",
                    "json",
                ],
                check=False,
            )
            results[table] = data if data else stdout.strip()
        except Exception as exc:
            results[table] = {"error": str(exc)}
    print(json.dumps({"project": args.project, "query": args.query, "results": results}, ensure_ascii=False, indent=2))
    return 0
