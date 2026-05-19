from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import load_json, write_json
from .paths import CONFIG_PATH, DEFAULT_REPO


def load_config() -> dict[str, Any]:
    if CONFIG_PATH.exists():
        return load_json(CONFIG_PATH)
    return {
        "version": 1,
        "mode": "shadow",
        "identity": "user",
        "timezone": "Asia/Shanghai",
        "wiki": {"space_id": "", "root_node_token": "", "root_url": "", "nodes": {}},
        "base": {"token": "", "url": "", "tables": {}},
        "defaults": {
            "project": DEFAULT_REPO.name,
            "repo_path": str(DEFAULT_REPO),
            "receipt_dir": ".devhub/receipts",
            "outbox_dir": ".devhub/outbox",
        },
    }


def save_config(config: dict[str, Any]) -> None:
    write_json(CONFIG_PATH, config)


def redact_resource_summary(config: dict[str, Any]) -> dict[str, Any]:
    wiki = config.get("wiki", {})
    base = config.get("base", {})
    return {
        "wiki": {
            "space_id": wiki.get("space_id", ""),
            "has_root_url": bool(wiki.get("root_url")),
            "has_root_node_token": bool(wiki.get("root_node_token")),
        },
        "base": {
            "has_url": bool(base.get("url")),
            "has_token": bool(base.get("token")),
            "tables": sorted(base.get("tables", {}).keys()),
        },
    }


def repo_runtime_dir(cwd: Path, key: str) -> Path:
    try:
        config = load_config()
    except Exception:
        config = {}
    fallback = {"receipt_dir": ".devhub/receipts", "outbox_dir": ".devhub/outbox"}
    dirname = config.get("defaults", {}).get(key, fallback.get(key, f".devhub/{key}"))
    return cwd / dirname
