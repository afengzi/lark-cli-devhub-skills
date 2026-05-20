from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .base import cleanup_deprecated_relation_fields, create_tables_and_fields, ensure_base, seed_records
from .config import load_config, redact_resource_summary, save_config
from .io import load_json
from .lark import run_lark
from .records import write_outbox, write_receipt
from .reports import draft_report
from .search import search_devhub
from .views import ensure_base_views
from .whiteboard import draft_whiteboard
from .wiki_docs import create_artifacts, ensure_wiki, write_report_wiki_artifact


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
        views = load_json(Path(args.views)) if getattr(args, "views", "") else {}
        ensure_wiki(config)
        ensure_base(config)
        create_tables_and_fields(config, schema)
        save_config(config)
        if views:
            ensure_base_views(config, views)
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
                "views_path": str(Path(args.views)) if getattr(args, "views", "") else "",
                "resource_summary": redact_resource_summary(config),
            },
            str(exc),
        )
        print(json.dumps({"ok": False, "outbox": str(outbox), "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


def command_cleanup_relation_fields(args: Any) -> int:
    config = load_config()
    removed = cleanup_deprecated_relation_fields(config, dry_run=args.dry_run)
    if not args.dry_run:
        save_config(config)
    failed = [item for item in removed if item.get("status") == "failed"]
    print(json.dumps({"ok": not failed, "dry_run": args.dry_run, "fields": removed}, ensure_ascii=False, indent=2))
    return 1 if failed else 0


def command_search(args: Any) -> int:
    config = load_config()
    try:
        result = search_devhub(config, args.project, args.query)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_report_draft(args: Any) -> int:
    records = load_json(Path(args.records))
    report = draft_report(args.kind, args.project, records)
    if not getattr(args, "wiki", False):
        print(report)
        return 0
    config: dict[str, Any] = {}
    config_loaded = False
    try:
        config = load_config()
        config_loaded = True
        result = write_report_wiki_artifact(config, kind=args.kind, project=args.project, body=report)
        save_config(config)
        receipt = write_receipt(
            Path.cwd(),
            f"report-{args.kind}-wiki",
            str(result.get("url") or ""),
            f"{args.kind} report for {args.project}",
            {
                "payload_title": str(result.get("title") or ""),
                "target": {
                    "type": "wiki-doc",
                    "table": "Artifacts",
                    "url": str(result.get("url") or ""),
                    "title": str(result.get("title") or ""),
                    "path": str(result.get("path") or ""),
                    "artifact_record_id": str(result.get("artifact_record_id") or ""),
                },
            },
        )
        print(json.dumps({"ok": True, "wiki": result, "receipt": str(receipt)}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        if config_loaded:
            save_config(config)
        outbox = write_outbox(
            Path.cwd(),
            f"report-{args.kind}-wiki",
            {"kind": args.kind, "project": args.project, "records_path": str(Path(args.records))},
            str(exc),
        )
        print(json.dumps({"ok": False, "outbox": str(outbox), "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    return 0


def command_whiteboard_draft(args: Any) -> int:
    print(draft_whiteboard(args.kind, args.project, args.summary))
    return 0
