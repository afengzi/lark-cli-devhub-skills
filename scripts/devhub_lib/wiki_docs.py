from __future__ import annotations

import html
import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

from .base import batch_upsert_records, cell_text, find_matching_record_id, upsert_record
from .io import find_first, find_first_token, parse_json_output
from .lark import run_lark, run_lark_with_input
from .paths import DEFAULT_REPO, DEVHUB_HOME
from .relationships import write_record_relations


_WIKI_CHILD_CACHE: dict[tuple[str, str], list[dict[str, Any]]] = {}


def current_project_name(config: dict[str, Any]) -> str:
    defaults = config.get("defaults", {})
    configured_path = str(defaults.get("repo_path") or "")
    if configured_path and DEFAULT_REPO.resolve() != Path(configured_path).expanduser().resolve():
        return DEFAULT_REPO.name
    return str(defaults.get("project") or DEFAULT_REPO.name)


def ensure_wiki(config: dict[str, Any]) -> None:
    if config.get("wiki", {}).get("root_url"):
        return
    wiki = config.setdefault("wiki", {})
    target_name = "Dev Knowledge Hub"
    space_id = wiki.get("space_id", "")
    try:
        spaces, _ = run_lark(["wiki", "+space-list", "--as", "user", "--format", "json", "--page-all"])
        for space in spaces.get("data", {}).get("spaces", []):
            if space.get("name") == target_name:
                space_id = space.get("space_id", "")
                break
        if not space_id:
            created, _ = run_lark(
                [
                    "wiki",
                    "spaces",
                    "create",
                    "--as",
                    "user",
                    "--data",
                    json.dumps(
                        {
                            "name": target_name,
                            "description": "Personal and project development knowledge hub for tasks, bugfixes, pitfalls, playbooks, and AI writeback.",
                            "open_sharing": "closed",
                        },
                        ensure_ascii=False,
                    ),
                    "--yes",
                ]
            )
            space_id = str(find_first(created, {"space_id"}) or "")
        node, _ = run_lark(
            [
                "wiki",
                "+node-create",
                "--as",
                "user",
                "--space-id",
                space_id,
                "--title",
                target_name,
                "--obj-type",
                "docx",
            ]
        )
        wiki["space_id"] = space_id
        wiki["root_node_token"] = str(find_first(node, {"node_token", "obj_token", "token"}) or "")
        wiki["root_url"] = str(find_first(node, {"url", "link"}) or f"space:{space_id}")
    except Exception as exc:
        fallback, _ = run_lark(
            [
                "wiki",
                "+node-create",
                "--as",
                "user",
                "--space-id",
                "my_library",
                "--title",
                target_name,
                "--obj-type",
                "docx",
            ]
        )
        wiki["space_id"] = "my_library"
        wiki["root_node_token"] = str(find_first(fallback, {"node_token", "obj_token", "token"}) or "")
        wiki["root_url"] = str(find_first(fallback, {"url", "link"}) or f"my_library:{wiki['root_node_token']}")
        wiki["fallback_reason"] = str(exc)


def iter_dicts(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from iter_dicts(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from iter_dicts(value)


def node_token(output: dict[str, Any]) -> str:
    return str(find_first(output, {"node_token", "obj_token", "token"}) or "")


def node_url(output: dict[str, Any], fallback: str) -> str:
    return str(find_first(output, {"url", "link"}) or fallback)


def template_dirs(kind: str) -> list[Path]:
    source_root = Path(__file__).resolve().parents[2]
    candidates = [
        DEVHUB_HOME / "templates" / kind,
        source_root / "templates" / kind,
    ]
    result: list[Path] = []
    for candidate in candidates:
        if candidate not in result:
            result.append(candidate)
    return result


def read_template(kind: str, name: str, fallback: str) -> str:
    for directory in template_dirs(kind):
        path = directory / name
        if path.exists():
            return path.read_text(encoding="utf-8")
    return fallback


def render_template(text: str, *, project: str) -> str:
    replacements = {
        "{{PROJECT}}": project,
        "PROJECT_NAME": project,
        "{{REPO_PATH}}": str(DEFAULT_REPO.resolve()),
        "{{DATE}}": date.today().isoformat(),
    }
    for needle, value in replacements.items():
        text = text.replace(needle, value)
    return text


def markdown_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return ", ".join(markdown_value(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def markdown_table_row(field: str, value: Any) -> str:
    safe_field = str(field).replace("|", "\\|")
    safe_value = markdown_value(value).replace("|", "\\|").replace("\n", "<br>")
    return f"| {safe_field} | {safe_value} |"


WIKI_WRITEBACKS: dict[str, dict[str, str]] = {
    "Bugfixes": {
        "title_prefix": "Bugfix Retro",
        "template": "bugfix-retro.md",
        "layout_key": "project_bugfixes",
        "artifact_type": "Doc",
        "area_fallback": "20 Bugfix Retros",
    },
    "AI Runs": {
        "title_prefix": "AI Run",
        "template": "ai-run.md",
        "layout_key": "project_reports",
        "artifact_type": "Doc",
        "area_fallback": "60 Reports",
    },
    "Releases": {
        "title_prefix": "Release",
        "template": "release-writeback.md",
        "layout_key": "project_reports",
        "artifact_type": "Doc",
        "area_fallback": "60 Reports",
    },
    "Decisions": {
        "title_prefix": "Decision",
        "template": "decision.md",
        "layout_key": "project_decisions",
        "artifact_type": "Doc",
        "area_fallback": "40 Decisions",
    },
    "Project Facts": {
        "title_prefix": "Project Fact",
        "template": "project-record.md",
        "layout_key": "project_overview",
        "artifact_type": "Doc",
        "area_fallback": "00 Overview",
    },
}


def wiki_writeback_supported(table: str) -> bool:
    return table in WIKI_WRITEBACKS


def wiki_writeback_title(table: str, payload: dict[str, Any]) -> str:
    spec = WIKI_WRITEBACKS[table]
    title = str(payload.get("Wiki Title") or payload.get("Title") or spec["title_prefix"]).strip()
    prefix = spec["title_prefix"]
    if title.startswith(f"{prefix}:"):
        return title
    return f"{prefix}: {title}"


def wiki_writeback_body(table: str, payload: dict[str, Any], *, title: str, base_record_id: str = "") -> str:
    project = str(payload.get("Project") or current_project_name({})).strip() or DEFAULT_REPO.name
    template = render_template(read_template("wiki", WIKI_WRITEBACKS[table]["template"], f"# {title}\n"), project=project)
    visible_payload = {key: value for key, value in payload.items() if key not in {"Relation Hints", "Wiki Body", "Wiki Title"}}
    rows = "\n".join(markdown_table_row(key, value) for key, value in visible_payload.items())
    body = str(payload.get("Wiki Body") or "").strip()
    parts = [
        f"# {title}",
        "",
        "> Generated by Dev Hub wiki writeback. Base remains the structured index; this page is the human-readable long-form artifact.",
    ]
    if base_record_id:
        parts.extend(["", f"Base record: `{base_record_id}`"])
    parts.extend(["", "## Template", "", template.strip(), "", "## Structured Writeback", "", "| Field | Value |", "|---|---|"])
    if rows:
        parts.append(rows)
    else:
        parts.append("|  |  |")
    if body:
        parts.extend(["", "## Long-form Notes", "", body])
    return "\n".join(parts).rstrip() + "\n"


def write_wiki_artifact(config: dict[str, Any], table: str, payload: dict[str, Any], *, base_record_id: str = "") -> dict[str, Any]:
    if not wiki_writeback_supported(table):
        raise RuntimeError(f"wiki writeback is not configured for table {table}")
    ensure_wiki(config)
    project = str(payload.get("Project") or current_project_name(config)).strip() or current_project_name(config)
    layout = wiki_layout(config, project)
    spec = WIKI_WRITEBACKS[table]
    parent = layout[spec["layout_key"]]["node_token"]
    title = wiki_writeback_title(table, payload)
    body = wiki_writeback_body(table, payload, title=title, base_record_id=base_record_id)
    output, _stdout = ensure_doc(config, title, body, parent_token=parent)
    doc_token = document_token(output)
    update_doc_content(doc_token, title, body)
    ensure_doc_title(doc_token, title)
    url = wiki_node_url(config, output, title)
    artifact_payload = {
        "Title": title,
        "Project": project,
        "Area": str(payload.get("Area") or spec["area_fallback"]),
        "Artifact Type": spec["artifact_type"],
        "Source URL": url,
        "Summary": str(payload.get("Summary") or payload.get("AI Summary") or payload.get("Title") or title),
        "AI Summary": f"Wiki long-form artifact for {table}: {payload.get('Title') or title}",
        "Search Keywords": str(payload.get("Search Keywords") or f"{project} {table} wiki artifact {title}"),
        "Status": "Active",
        "Relation Hints": f"{table}: {base_record_id or payload.get('Title') or title}",
    }
    artifact_output, _stdout = upsert_record(config, "Artifacts", artifact_payload, match_fields=["Title", "Project"])
    artifact_record_id = cell_text(find_first_token(artifact_output, {"_record_id", "record_id", "record_url", "url", "link"}))
    if not artifact_record_id:
        artifact_record_id = find_matching_record_id(config, "Artifacts", artifact_payload, ["Title", "Project"])
    relation_records = write_record_relations(config, "Artifacts", artifact_record_id, artifact_payload) if artifact_record_id else []
    return {
        "title": title,
        "url": url,
        "doc_token": doc_token,
        "artifact_record_id": artifact_record_id,
        "artifact_relation_records": relation_records,
        "artifact": artifact_payload,
    }


def write_report_wiki_artifact(config: dict[str, Any], *, kind: str, project: str, body: str) -> dict[str, Any]:
    ensure_wiki(config)
    layout = wiki_layout(config, project)
    title = f"Report: {project} {kind} {date.today().isoformat()}"
    output, _stdout = ensure_doc(config, title, body, parent_token=layout["project_reports"]["node_token"])
    doc_token = document_token(output)
    update_doc_content(doc_token, title, body)
    ensure_doc_title(doc_token, title)
    url = wiki_node_url(config, output, title)
    artifact_payload = {
        "Title": title,
        "Project": project,
        "Area": "60 Reports",
        "Artifact Type": "Doc",
        "Source URL": url,
        "Summary": f"{kind.title()} report draft for {project}.",
        "AI Summary": f"{kind.title()} report Wiki draft generated from Dev Hub records.",
        "Search Keywords": f"{project} report {kind} weekly daily release Dev Hub",
        "Status": "Draft",
    }
    artifact_output, _stdout = upsert_record(config, "Artifacts", artifact_payload, match_fields=["Title", "Project"])
    artifact_record_id = cell_text(find_first_token(artifact_output, {"_record_id", "record_id", "record_url", "url", "link"}))
    if not artifact_record_id:
        artifact_record_id = find_matching_record_id(config, "Artifacts", artifact_payload, ["Title", "Project"])
    return {"title": title, "url": url, "doc_token": doc_token, "artifact_record_id": artifact_record_id, "artifact": artifact_payload}


def document_token(output: dict[str, Any]) -> str:
    if isinstance(output, dict):
        for key in ("obj_token", "document_id"):
            if output.get(key):
                return str(output[key])
    return find_first_token(output, {"obj_token", "document_id"})


def wiki_node_url(config: dict[str, Any], output: dict[str, Any], fallback: str) -> str:
    url = str(find_first(output, {"url", "link"}) or "")
    if url:
        return url
    node = str(output.get("node_token") or find_first(output, {"node_token"}) or "")
    root_url = str(config.get("wiki", {}).get("root_url") or "")
    if node and "/wiki/" in root_url:
        return f"{root_url.split('/wiki/')[0]}/wiki/{node}"
    return node or fallback


def fetch_doc_content(doc_token: str) -> str:
    if not doc_token:
        return ""
    output, _ = run_lark(
        ["docs", "+fetch", "--api-version", "v2", "--as", "user", "--doc", doc_token, "--format", "json"],
        check=False,
    )
    return str(find_first(output, {"content"}) or "")


def update_doc_content(doc_token: str, title: str, body: str) -> None:
    if not doc_token:
        return
    args = [
        "docs",
        "+update",
        "--api-version",
        "v2",
        "--as",
        "user",
        "--doc",
        doc_token,
        "--command",
        "overwrite",
        "--doc-format",
        "markdown",
        "--content",
        "-",
    ]
    try:
        run_lark_with_input(args, body)
    except RuntimeError as exc:
        if "unknown flag" not in str(exc) and "unknown shorthand" not in str(exc) and "doc-format" not in str(exc):
            raise
        run_lark(
            [
                "docs",
                "+update",
                "--api-version",
                "v2",
                "--as",
                "user",
                "--doc",
                doc_token,
                "--command",
                "overwrite",
                "--content",
                f"<title>{html.escape(title)}</title><p>{html.escape(body)}</p>",
            ]
        )


def ensure_doc_title(doc_token: str, title: str) -> None:
    content = fetch_doc_content(doc_token)
    match = re.search(r"<title>(.*?)</title>", content)
    current = match.group(1) if match else ""
    if current == title:
        return
    if current:
        run_lark(
            [
                "docs",
                "+update",
                "--api-version",
                "v2",
                "--as",
                "user",
                "--doc",
                doc_token,
                "--command",
                "str_replace",
                "--pattern",
                current,
                "--content",
                title,
            ]
        )


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
            "--command",
            "append",
            "--content",
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


def clear_wiki_child_cache() -> None:
    _WIKI_CHILD_CACHE.clear()


def cache_child_node(config: dict[str, Any], parent_token: str, title: str, output: dict[str, Any]) -> None:
    wiki = config.setdefault("wiki", {})
    space_id = wiki.get("space_id", "my_library")
    key = (str(space_id), parent_token)
    if key not in _WIKI_CHILD_CACHE:
        return
    node = dict(output)
    node.setdefault("title", title)
    _WIKI_CHILD_CACHE[key].append(node)


def find_child_node(config: dict[str, Any], parent_token: str, title: str) -> dict[str, Any] | None:
    aliases = {title}
    if title.startswith("Template: "):
        aliases.add(title.removeprefix("Template: "))
    for item in list_child_nodes(config, parent_token):
        if item.get("title") in aliases or item.get("name") in aliases:
            return item
    return None


def ensure_wiki_node(config: dict[str, Any], title: str, *, parent_token: str = "") -> dict[str, str]:
    wiki = config.setdefault("wiki", {})
    space_id = wiki.get("space_id", "my_library")
    nodes = wiki.setdefault("nodes", {})
    key = f"{parent_token or 'root'}/{title}"
    cached = nodes.get(key)
    if isinstance(cached, dict) and cached.get("node_token"):
        return {"node_token": str(cached["node_token"]), "url": str(cached.get("url") or cached["node_token"])}

    existing = find_child_node(config, parent_token, title)
    if existing:
        token = str(existing.get("node_token") or existing.get("obj_token") or existing.get("token") or "")
        url = str(existing.get("url") or existing.get("link") or token)
        nodes[key] = {"node_token": token, "url": url}
        return {"node_token": token, "url": url}

    args = ["wiki", "+node-create", "--as", "user", "--space-id", space_id, "--title", title, "--obj-type", "docx"]
    if parent_token:
        args.extend(["--parent-node-token", parent_token])
    created, _ = run_lark(args)
    token = node_token(created)
    url = node_url(created, token or title)
    nodes[key] = {"node_token": token, "url": url}
    cache_child_node(config, parent_token, title, created)
    return {"node_token": token, "url": url}


def create_doc(title: str, body: str, *, parent_token: str = "", space_id: str = "") -> tuple[dict[str, Any], str]:
    if space_id and parent_token:
        return run_lark(
            [
                "wiki",
                "+node-create",
                "--as",
                "user",
                "--space-id",
                space_id,
                "--parent-node-token",
                parent_token,
                "--title",
                title,
                "--obj-type",
                "docx",
            ]
        )
    return run_lark(["docs", "+create", "--api-version", "v2", "--as", "user", "--title", title, "--content", body])


def ensure_doc(config: dict[str, Any], title: str, body: str, *, parent_token: str) -> tuple[dict[str, Any], str]:
    wiki = config.setdefault("wiki", {})
    space_id = wiki.get("space_id", "my_library")
    existing = find_child_node(config, parent_token, title)
    if existing:
        return existing, json.dumps(existing, ensure_ascii=False)
    created, stdout = create_doc(title, body, parent_token=parent_token, space_id=space_id)
    cache_child_node(config, parent_token, title, created)
    return created, stdout


def list_child_nodes(config: dict[str, Any], parent_token: str) -> list[dict[str, Any]]:
    wiki = config.setdefault("wiki", {})
    space_id = wiki.get("space_id", "my_library")
    args = ["wiki", "+node-list", "--as", "user", "--space-id", space_id, "--format", "json", "--page-all"]
    if parent_token:
        args.extend(["--parent-node-token", parent_token])
    cache_key = (str(space_id), parent_token)
    if cache_key in _WIKI_CHILD_CACHE:
        return _WIKI_CHILD_CACHE[cache_key]
    output, _ = run_lark(args, check=False)
    nodes = output.get("data", {}).get("nodes") or output.get("data", {}).get("items") or []
    _WIKI_CHILD_CACHE[cache_key] = [node for node in nodes if isinstance(node, dict)]
    return _WIKI_CHILD_CACHE[cache_key]


def archive_node(config: dict[str, Any], node: dict[str, Any], archive_parent_token: str) -> None:
    node_token_value = str(node.get("node_token") or node.get("token") or "")
    if not node_token_value:
        return
    wiki = config.setdefault("wiki", {})
    space_id = wiki.get("space_id", "my_library")
    run_lark(
        [
            "wiki",
            "+move",
            "--as",
            "user",
            "--node-token",
            node_token_value,
            "--source-space-id",
            space_id,
            "--target-parent-token",
            archive_parent_token,
            "--target-space-id",
            space_id,
        ],
        check=False,
    )
    clear_wiki_child_cache()


def cleanup_wiki_noise(config: dict[str, Any], layout: dict[str, dict[str, str]]) -> None:
    archive = ensure_wiki_node(config, "99 Provision Cleanup", parent_token=layout["archive"]["node_token"])
    archive_parent = archive["node_token"]
    root_token = config.get("wiki", {}).get("root_node_token", "")
    for parent in (root_token, layout["global_root"]["node_token"]):
        for node in list_child_nodes(config, parent):
            title = str(node.get("title") or node.get("name") or "")
            if title == "Untitled":
                archive_node(config, node, archive_parent)
            if parent == layout["global_root"]["node_token"] and title in {"Dev Hub 使用说明", "AI 写入规则"}:
                archive_node(config, node, archive_parent)


def wiki_layout(config: dict[str, Any], project: str) -> dict[str, dict[str, str]]:
    root = config.get("wiki", {}).get("root_node_token", "")
    global_root = ensure_wiki_node(config, "00 Global", parent_token=root)
    global_templates = ensure_wiki_node(config, "02 Templates", parent_token=global_root["node_token"])
    global_maps = ensure_wiki_node(config, "50 Maps", parent_token=global_root["node_token"])
    projects_root = ensure_wiki_node(config, "10 Projects", parent_token=root)
    project_root = ensure_wiki_node(config, project, parent_token=projects_root["node_token"])
    project_overview = ensure_wiki_node(config, "00 Overview", parent_token=project_root["node_token"])
    project_bugfixes = ensure_wiki_node(config, "20 Bugfix Retros", parent_token=project_root["node_token"])
    project_playbooks = ensure_wiki_node(config, "30 Playbooks", parent_token=project_root["node_token"])
    project_decisions = ensure_wiki_node(config, "40 Decisions", parent_token=project_root["node_token"])
    project_maps = ensure_wiki_node(config, "50 Maps", parent_token=project_root["node_token"])
    project_reports = ensure_wiki_node(config, "60 Reports", parent_token=project_root["node_token"])
    archive = ensure_wiki_node(config, "90 Archive", parent_token=root)
    return {
        "global_root": global_root,
        "global_templates": global_templates,
        "global_maps": global_maps,
        "projects_root": projects_root,
        "project_root": project_root,
        "project_overview": project_overview,
        "project_bugfixes": project_bugfixes,
        "project_playbooks": project_playbooks,
        "project_decisions": project_decisions,
        "project_maps": project_maps,
        "project_reports": project_reports,
        "archive": archive,
    }


def create_artifacts(config: dict[str, Any]) -> None:
    clear_wiki_child_cache()
    project = current_project_name(config)
    layout = wiki_layout(config, project)
    cleanup_wiki_noise(config, layout)
    artifact_payloads: list[dict[str, Any]] = []
    docs = [
        ("Global: Dev Hub 使用说明", "00 Global", layout["global_root"]["node_token"], "global-devhub-guide.md", "Dev Hub Base 是结构化事实源；Docs 承载长文；Whiteboard/Maps 承载视觉关系。"),
        ("Global: AI 写入规则", "00 Global", layout["global_root"]["node_token"], "ai-write-rules.md", "AI 在修复前检索 Pitfalls / Bugfixes / Playbooks，修复后写 Bugfix、AI Run 和 receipt。"),
        ("Template: 项目记录模板", "02 Templates", layout["global_templates"]["node_token"], "project-record.md", "记录项目定位、Areas、关键风险、当前重点和 AI 摘要。"),
        ("Template: Bugfix 复盘模板", "02 Templates", layout["global_templates"]["node_token"], "bugfix-retro.md", "记录症状、证据、根因、修复、验证、风险、下次检查和禁止做法。"),
        ("Template: Playbook 模板", "02 Templates", layout["global_templates"]["node_token"], "playbook.md", "记录适用场景、排查顺序、必看证据、命令、成功标准和禁止做法。"),
        ("Template: Decision 决策模板", "02 Templates", layout["global_templates"]["node_token"], "decision.md", "记录架构或产品决策、备选方案、取舍、影响和复审触发器。"),
        ("Template: Release 写回模板", "02 Templates", layout["global_templates"]["node_token"], "release-writeback.md", "记录 main/PR 发布摘要、验证、关联记录和回滚方案。"),
        ("Template: AI Run 总结模板", "02 Templates", layout["global_templates"]["node_token"], "ai-run.md", "记录 Agent 本次做了什么、查了什么、改了什么、如何验证和写回。"),
        ("Template: Bug 排查路径模板", "02 Templates", layout["global_templates"]["node_token"], "bug-investigation-path.md", "记录症状、证据分层、分支判断和知识库收尾。"),
        (f"{project}: 项目主页", "00 Overview", layout["project_overview"]["node_token"], "project-home.md", "项目主页用于聚合项目当前事实、常用入口、架构链接、任务队列和最近发布。"),
    ]
    for title, folder, parent, template_name, summary in docs:
        body = render_template(read_template("wiki", template_name, f"# {title}\n\n{summary}\n"), project=project)
        output, _ = ensure_doc(config, title, body, parent_token=parent)
        doc_token = document_token(output)
        update_doc_content(doc_token, title, body)
        ensure_doc_title(doc_token, title)
        url = wiki_node_url(config, output, title)
        artifact_payloads.append(
            {
                "Title": title,
                "Project": project if title.startswith(f"{project}:") else "Global",
                "Area": folder,
                "Artifact Type": "Doc",
                "Source URL": url,
                "Summary": summary,
                "AI Summary": f"{title} for Feishu Dev Hub.",
                "Search Keywords": f"Dev Hub {project} {folder} {title}",
                "Status": "Active",
            }
        )

    boards = [
        (
            "Global: Dev Hub 总览图",
            "50 Maps",
            layout["global_maps"]["node_token"],
            "Global",
            "global-devhub-overview.svg",
            "Dev Hub 全局知识模型：Base、Wiki/Docs、Whiteboard、Task、Receipts/Outbox 的关系。",
        ),
        (
            "Global: Bug 排查路径图",
            "50 Maps",
            layout["global_maps"]["node_token"],
            "Global",
            "bug-investigation-map.svg",
            "全局 Bug 排查白板：给所有项目复用的证据分层、根因定位和知识沉淀路径。",
        ),
        (
            "Global: PR 写回流程图",
            "50 Maps",
            layout["global_maps"]["node_token"],
            "Global",
            "pr-writeback-map.svg",
            "全局 PR 写回白板：PR、review、merge、CI failed 到 Base 和 receipt 的映射。",
        ),
        (
            "Global: 任务执行闭环图",
            "50 Maps",
            layout["global_maps"]["node_token"],
            "Global",
            "task-loop-map.svg",
            "全局任务闭环白板：Feishu Task、Base Task、AI Run、Bugfix/Release 与 receipt 的关系。",
        ),
        (
            f"{project}: 架构图",
            "50 Maps",
            layout["project_maps"]["node_token"],
            project,
            "project-architecture.svg",
            "项目新架构图：skills、helper、templates、Base、Wiki/Docs、Whiteboard 和写回纪律的连接。",
        ),
        (
            f"{project}: Bug 排查路径图",
            "50 Maps",
            layout["project_maps"]["node_token"],
            project,
            "bug-investigation-map.svg",
            "项目级 Bug 排查白板：结合当前项目的历史记录、证据分层和复盘沉淀入口。",
        ),
        (
            f"{project}: PR 写回流程图",
            "50 Maps",
            layout["project_maps"]["node_token"],
            project,
            "pr-writeback-map.svg",
            "项目级 PR 写回白板：把该项目的 PR、review、merge、CI failed 映射到 Dev Hub。",
        ),
        (
            f"{project}: 任务执行闭环图",
            "50 Maps",
            layout["project_maps"]["node_token"],
            project,
            "task-loop-map.svg",
            "项目级任务闭环白板：该项目执行任务、写回记录和验证 receipt 的标准路径。",
        ),
        (
            "Template: Bug 排查路径图",
            "02 Templates",
            layout["global_templates"]["node_token"],
            "Global",
            "bug-investigation-map.svg",
            "Bug 排查白板模板：从症状到证据、根因、修复、验证和复盘沉淀。",
        ),
        (
            "Template: PR 写回流程图",
            "02 Templates",
            layout["global_templates"]["node_token"],
            "Global",
            "pr-writeback-map.svg",
            "PR 写回白板模板：PR created、reviewed、merged、CI failed 到对应 Base 表的映射。",
        ),
        (
            "Template: 任务执行闭环图",
            "02 Templates",
            layout["global_templates"]["node_token"],
            "Global",
            "task-loop-map.svg",
            "任务执行白板模板：Feishu Task、Base Task、AI Run、Bugfix/Release 和 receipt 的闭环。",
        ),
    ]
    for title, folder, parent, item_project, template_name, summary in boards:
        board_source = render_template(read_template("whiteboards", template_name, ""), project=project)
        body = f"# {title}\n\n{summary}\n\nAI 可回看摘要在 Dev Hub Base 的 Artifacts 表中；白板用于人类快速扫关系。\n\nSource template: `templates/whiteboards/{template_name}`\n"
        output, _ = ensure_doc(config, title, body, parent_token=parent)
        doc_token = document_token(output)
        existing_content = fetch_doc_content(doc_token)
        existing_whiteboard = find_whiteboard_token_in_content(existing_content)
        if not existing_whiteboard:
            update_doc_content(doc_token, title, body)
        else:
            ensure_doc_title(doc_token, title)
        board_token = ""
        warning = ""
        if doc_token and board_source:
            try:
                if existing_whiteboard:
                    board_token = existing_whiteboard
                    newly_created = False
                else:
                    board_token = append_whiteboard(doc_token)
                    newly_created = True
                if should_preserve_existing_whiteboard(newly_created):
                    warning = ""
                else:
                    update_source, input_format = whiteboard_update_input(template_name, board_source)
                    warning = update_whiteboard(board_token, update_source, input_format, title, newly_created=newly_created)
            except Exception as exc:
                warning = str(exc)
        url = wiki_node_url(config, output, title)
        ai_summary = f"{title}: visual aid; use Base records as source of truth."
        if warning:
            ai_summary = f"{ai_summary} Whiteboard warning: {warning}"
        artifact_payloads.append(
            {
                "Title": title,
                "Project": item_project,
                "Area": folder,
                "Artifact Type": "Whiteboard" if board_token else "Doc",
                "Source URL": url,
                "Summary": summary,
                "AI Summary": ai_summary,
                "Search Keywords": f"Dev Hub map whiteboard {project} {folder} {title}",
                "Status": "Active",
            }
        )
    batch_upsert_records(config, "Artifacts", artifact_payloads, match_fields=["Title", "Project"])
