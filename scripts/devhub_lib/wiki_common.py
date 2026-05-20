from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from .io import find_first, find_first_token
from .lark import run_lark, run_lark_with_input
from .paths import DEFAULT_REPO, DEVHUB_HOME


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


def document_token(output: dict[str, Any]) -> str:
    if isinstance(output, dict):
        for key in ("doc_token", "obj_token", "document_id"):
            if output.get(key):
                return str(output[key])
    return find_first_token(output, {"doc_token", "obj_token", "document_id"})


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
    return str(find_first(output, {"markdown", "content"}) or "")


def should_retry_legacy_docs_update(error: RuntimeError) -> bool:
    text = str(error)
    return any(
        marker in text
        for marker in (
            "unknown flag",
            "unknown shorthand",
            "unknown command",
            "--command is required",
        )
    )


def legacy_markdown_update_args(doc_token: str, command: str, content: str) -> list[str]:
    return [
        "docs",
        "+update",
        "--api-version",
        "v2",
        "--as",
        "user",
        "--doc",
        doc_token,
        "--command",
        command,
        "--doc-format",
        "markdown",
        "--content",
        content,
    ]


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
        "--mode",
        "overwrite",
        "--new-title",
        title,
        "--markdown",
        "-",
    ]
    try:
        run_lark_with_input(args, body)
    except RuntimeError as exc:
        if not should_retry_legacy_docs_update(exc):
            raise
        run_lark(legacy_markdown_update_args(doc_token, "overwrite", body))


def append_doc_content(doc_token: str, body: str) -> None:
    if not doc_token or not body.strip():
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
        "--mode",
        "append",
        "--markdown",
        "-",
    ]
    try:
        run_lark_with_input(args, body)
    except RuntimeError as exc:
        if not should_retry_legacy_docs_update(exc):
            raise
        run_lark(legacy_markdown_update_args(doc_token, "append", body))


def ensure_doc_title(doc_token: str, title: str) -> None:
    content = fetch_doc_content(doc_token)
    match = re.search(r"<title>(.*?)</title>", content)
    current = match.group(1) if match else ""
    if current == title:
        return
    if current:
        try:
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
                    "--new-title",
                    title,
                ]
            )
        except RuntimeError as exc:
            if not should_retry_legacy_docs_update(exc):
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
                    "str_replace",
                    "--pattern",
                    current,
                    "--content",
                    title,
                ]
            )


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
    if isinstance(cached, dict) and cached.get("node_token") and cached.get("doc_token"):
        return {
            "node_token": str(cached["node_token"]),
            "doc_token": str(cached["doc_token"]),
            "url": str(cached.get("url") or cached["node_token"]),
            "created": False,
        }

    existing = find_child_node(config, parent_token, title)
    if existing:
        token = str(existing.get("node_token") or existing.get("obj_token") or existing.get("token") or "")
        doc_token = document_token(existing) or token
        url = str(existing.get("url") or existing.get("link") or token)
        nodes[key] = {"node_token": token, "doc_token": doc_token, "url": url}
        return {"node_token": token, "doc_token": doc_token, "url": url, "created": False}

    args = ["wiki", "+node-create", "--as", "user", "--space-id", space_id, "--title", title, "--obj-type", "docx"]
    if parent_token:
        args.extend(["--parent-node-token", parent_token])
    created, _ = run_lark(args)
    token = node_token(created)
    doc_token = document_token(created) or token
    url = node_url(created, token or title)
    nodes[key] = {"node_token": token, "doc_token": doc_token, "url": url}
    cache_child_node(config, parent_token, title, created)
    return {"node_token": token, "doc_token": doc_token, "url": url, "created": True}


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
    return run_lark(["docs", "+create", "--api-version", "v2", "--as", "user", "--title", title, "--markdown", body])


def ensure_doc_with_status(config: dict[str, Any], title: str, body: str, *, parent_token: str) -> tuple[dict[str, Any], str, bool]:
    wiki = config.setdefault("wiki", {})
    space_id = wiki.get("space_id", "my_library")
    existing = find_child_node(config, parent_token, title)
    if existing:
        return existing, json.dumps(existing, ensure_ascii=False), False
    created, stdout = create_doc(title, body, parent_token=parent_token, space_id=space_id)
    cache_child_node(config, parent_token, title, created)
    return created, stdout, True


def ensure_doc(config: dict[str, Any], title: str, body: str, *, parent_token: str) -> tuple[dict[str, Any], str]:
    output, stdout, _created = ensure_doc_with_status(config, title, body, parent_token=parent_token)
    return output, stdout


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


APPEND_ONLY_PROJECT_PAGES = {
    "00 Overview",
    "20 Bugfix Retros",
    "30 Playbooks",
    "40 Decisions",
    "60 Reports",
}


def should_archive_project_child(area_title: str, child_title: str) -> bool:
    if child_title == "Untitled":
        return True
    return area_title in APPEND_ONLY_PROJECT_PAGES


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
    project_pages = {
        "00 Overview": layout["project_overview"]["node_token"],
        "20 Bugfix Retros": layout["project_bugfixes"]["node_token"],
        "30 Playbooks": layout["project_playbooks"]["node_token"],
        "40 Decisions": layout["project_decisions"]["node_token"],
        "50 Maps": layout["project_maps"]["node_token"],
        "60 Reports": layout["project_reports"]["node_token"],
    }
    for area_title, parent in project_pages.items():
        for node in list_child_nodes(config, parent):
            title = str(node.get("title") or node.get("name") or "")
            if should_archive_project_child(area_title, title):
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
