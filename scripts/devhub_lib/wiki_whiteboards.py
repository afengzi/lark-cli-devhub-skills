from __future__ import annotations

import hashlib
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .io import find_first, find_first_token, parse_json_output
from .lark import run_lark, run_lark_with_input
from .paths import DEVHUB_HOME
from .wiki_common import fetch_doc_content, iter_dicts


def find_whiteboard_token(output: dict[str, Any]) -> str:
    for item in iter_dicts(output):
        if item.get("block_type") == "whiteboard" and item.get("block_token"):
            return str(item["block_token"])
        for key in ("whiteboard_token", "board_token"):
            if item.get(key):
                return str(item[key])
    return find_first_token(output, {"whiteboard_token", "board_token", "block_token"})


def find_whiteboard_token_in_content(content: str) -> str:
    match = re.search(r"<whiteboard\s+[^>]*token=\"([^\"]+)\"", content)
    return match.group(1) if match else ""


def append_whiteboard(doc_token: str) -> str:
    output, _ = run_lark(
        [
            "docs",
            "+update",
            "--api-version",
            "v2",
            "--as",
            "user",
            "--doc",
            doc_token,
            "--mode",
            "append",
            "--markdown",
            '<whiteboard type="blank"></whiteboard>',
        ]
    )
    token = find_whiteboard_token(output)
    if token:
        return token
    return find_whiteboard_token_in_content(fetch_doc_content(doc_token))


def ensure_whiteboard_token(doc_token: str) -> tuple[str, bool]:
    content = fetch_doc_content(doc_token)
    existing = find_whiteboard_token_in_content(content)
    if existing:
        return existing, False
    return append_whiteboard(doc_token), True


def idempotent_token(title: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-").lower() or "devhub"
    digest = hashlib.sha1(title.encode("utf-8")).hexdigest()[:10]
    return f"devhub-{safe[:20]}-{digest}"


def whiteboard_delete_count(stdout: str) -> int:
    matches = re.findall(r"(\d+)\s+whiteboard nodes? will be deleted", stdout)
    return max((int(value) for value in matches), default=0)


def whiteboard_overwrite_enabled() -> bool:
    return os.environ.get("DEVHUB_WHITEBOARD_OVERWRITE", "").lower() in {"1", "true", "yes", "y"}


def should_preserve_existing_whiteboard(newly_created: bool) -> bool:
    return not newly_created and not whiteboard_overwrite_enabled()


def cached_svg_conversion(template_name: str, source: str) -> str:
    cache_dir = DEVHUB_HOME / "cache" / "whiteboards"
    digest = hashlib.sha256(
        f"whiteboard-cli@0.2.11\0{template_name}\0{source}".encode("utf-8")
    ).hexdigest()
    cache_path = cache_dir / f"{digest}.json"
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".svg", delete=False) as handle:
        handle.write(source)
        temp_path = Path(handle.name)
    try:
        result = subprocess.run(
            [
                "npx",
                "-y",
                "@larksuite/whiteboard-cli@^0.2.11",
                "-i",
                str(temp_path),
                "--to",
                "openapi",
                "--format",
                "json",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    finally:
        temp_path.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "whiteboard SVG conversion failed")
    parsed = parse_json_output(result.stdout)
    if parsed.get("code") not in (None, 0):
        raise RuntimeError(str(parsed.get("error") or "whiteboard SVG conversion failed"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(result.stdout, encoding="utf-8")
    return result.stdout


def whiteboard_update_input(template_name: str, source: str) -> tuple[str, str]:
    suffix = Path(template_name).suffix.lower()
    if suffix == ".mmd":
        return source, "mermaid"
    if suffix == ".json":
        return source, "raw"
    if suffix == ".svg":
        return cached_svg_conversion(template_name, source), "raw"
    raise RuntimeError(f"unsupported whiteboard template: {template_name}")


def update_whiteboard(board_token: str, source: str, input_format: str, title: str, *, newly_created: bool) -> str:
    if not board_token:
        return "missing whiteboard token"
    args = [
        "whiteboard",
        "+update",
        "--as",
        "user",
        "--whiteboard-token",
        board_token,
        "--input_format",
        input_format,
        "--source",
        "-",
        "--idempotent-token",
        idempotent_token(title),
        "--overwrite",
    ]
    dry_output, dry_stdout = run_lark_with_input([*args, "--dry-run"], source, check=False)
    if dry_output.get("ok") is False:
        return str(find_first(dry_output, {"message"}) or "whiteboard dry-run failed")
    if not newly_created and whiteboard_delete_count(dry_stdout) > 0 and not whiteboard_overwrite_enabled():
        return "dry-run would delete existing whiteboard nodes; skipped overwrite"
    run_lark_with_input(args, source)
    return ""
