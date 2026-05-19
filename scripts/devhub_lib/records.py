from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from .base import upsert_record
from .config import load_config, repo_runtime_dir
from .io import find_first_token, load_json, now_iso, write_json


def write_outbox(cwd: Path, kind: str, payload: dict[str, Any], error: str) -> Path:
    outbox = repo_runtime_dir(cwd, "outbox_dir")
    outbox.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    path = outbox / f"{now_iso().replace(':', '-')}-{kind}-{digest}.json"
    write_json(
        path,
        {
            "kind": kind,
            "operation": kind,
            "created_at": now_iso(),
            "error": error,
            "payload": payload,
            "retry_count": 0,
            "retry_hint": 'python3 "$DEVHUB_HOME/bin/devhub.py" sync-outbox --cwd "$PWD"',
        },
    )
    return path


def write_receipt(cwd: Path, kind: str, record_url: str, summary: str, extra: dict[str, Any] | None = None) -> Path:
    receipts = repo_runtime_dir(cwd, "receipt_dir")
    receipts.mkdir(parents=True, exist_ok=True)
    extra = extra or {}
    source = extra.get("source") or {"type": "manual", "commit": "", "pr": ""}
    target = {
        "type": "base-record",
        "table": extra.get("table", ""),
        "record_id": record_url,
    }
    data = {
        "kind": kind,
        "operation": kind,
        "created_at": now_iso(),
        "record_url": record_url,
        "target": target,
        "source": source,
        "summary": summary,
        "payload_title": extra.get("payload_title", ""),
    }
    digest = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    path = receipts / f"{now_iso().replace(':', '-')}-{kind}-{digest}.json"
    write_json(path, data)
    return path


def record_command(kind: str, table: str, payload_path: Path, cwd: Path) -> int:
    config = load_config()
    payload = load_json(payload_path)
    try:
        output, _stdout = upsert_record(config, table, payload)
        record_url = find_first_token(output, {"record_url", "url", "link", "record_id", "record_id_list"})
        if not record_url:
            raise RuntimeError("lark-cli write succeeded but returned no record identifier")
        summary = payload.get("AI Summary") or payload.get("Title") or kind
        receipt = write_receipt(cwd, kind, record_url, summary, {"table": table, "payload_title": payload.get("Title", "")})
        print(json.dumps({"ok": True, "record_url": record_url, "receipt": str(receipt)}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        outbox = write_outbox(cwd, kind, {"table": table, "payload": payload}, str(exc))
        print(json.dumps({"ok": False, "outbox": str(outbox), "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


def command_receipt(args: Any) -> int:
    path = write_receipt(Path.cwd(), args.kind, args.record_url, args.summary)
    print(path)
    return 0


def command_sync_outbox(args: Any) -> int:
    cwd = Path(args.cwd)
    outbox = repo_runtime_dir(cwd, "outbox_dir")
    if not outbox.exists():
        print("No outbox directory.")
        return 0
    files = sorted(outbox.glob("*.json"))
    print(json.dumps({"outbox": str(outbox), "count": len(files), "files": [str(path) for path in files]}, ensure_ascii=False, indent=2))
    return 0
