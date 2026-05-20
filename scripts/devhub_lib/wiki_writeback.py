from __future__ import annotations

import json
import re
from typing import Any

from .base import cell_text, find_matching_record_id, upsert_record
from .io import find_first_token, now_iso
from .paths import DEFAULT_REPO
from .relationships import write_record_relations
from .wiki_common import (
    append_doc_content,
    current_project_name,
    document_token,
    ensure_doc_title,
    ensure_wiki,
    markdown_table_row,
    read_template,
    render_template,
    update_doc_content,
    wiki_layout,
    wiki_node_url,
)


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


def wiki_writeback_base_title(table: str, payload: dict[str, Any]) -> str:
    spec = WIKI_WRITEBACKS[table]
    title = str(payload.get("Wiki Title") or payload.get("Title") or spec["title_prefix"]).strip()
    prefix = spec["title_prefix"]
    if title.startswith(f"{prefix}:"):
        return title
    return f"{prefix}: {title}"


def wiki_writeback_timestamp() -> str:
    return now_iso().split("+", 1)[0].replace("T", " ")


def incremental_wiki_title(base_title: str, *, base_record_id: str = "", write_time: str = "") -> str:
    timestamp = write_time or wiki_writeback_timestamp()
    suffix = f" ({base_record_id})" if base_record_id else ""
    return f"{timestamp} - {base_title}{suffix}"


def demote_markdown_headings(text: str, *, levels: int = 1) -> str:
    def replace(match: re.Match[str]) -> str:
        marks = match.group(1)
        return f"{'#' * min(len(marks) + levels, 6)}{match.group(2)}"

    return re.sub(r"^(#{1,6})(\s+)", replace, text, flags=re.MULTILINE)


def strip_top_heading(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
        if lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines).strip()


def wiki_log_page_body(title: str, *, project: str, table: str) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            "> Dev Hub incremental Wiki page. Base remains the structured index; this page keeps append-only human-readable entries.",
            "",
            f"Project: `{project}`",
            f"Record type: `{table}`",
            "Write mode: append-only entries; do not overwrite older sections.",
            "",
        ]
    )


def wiki_writeback_body(
    table: str,
    payload: dict[str, Any],
    *,
    entry_title: str,
    base_title: str = "",
    base_record_id: str = "",
    write_time: str = "",
) -> str:
    project = str(payload.get("Project") or current_project_name({})).strip() or DEFAULT_REPO.name
    template = render_template(read_template("wiki", WIKI_WRITEBACKS[table]["template"], f"# {entry_title}\n"), project=project)
    visible_payload = {key: value for key, value in payload.items() if key not in {"Relation Hints", "Wiki Body", "Wiki Title"}}
    rows = "\n".join(markdown_table_row(key, value) for key, value in visible_payload.items())
    body = str(payload.get("Wiki Body") or "").strip()
    parts = [
        f"## {entry_title}",
        "",
        f"Write time: `{write_time or wiki_writeback_timestamp()}`",
    ]
    if base_title:
        parts.extend(["", f"Write summary: {base_title}"])
    if base_record_id:
        parts.extend(["", f"Base record: `{base_record_id}`"])
    parts.extend(["", "### Template", "", demote_markdown_headings(template.strip(), levels=2), "", "### Structured Writeback", "", "| Field | Value |", "|---|---|"])
    if rows:
        parts.append(rows)
    else:
        parts.append("|  |  |")
    if body:
        parts.extend(["", "### Long-form Notes", "", demote_markdown_headings(body, levels=1)])
    return "\n".join(parts).rstrip() + "\n"


def write_wiki_artifact(config: dict[str, Any], table: str, payload: dict[str, Any], *, base_record_id: str = "") -> dict[str, Any]:
    if not wiki_writeback_supported(table):
        raise RuntimeError(f"wiki writeback is not configured for table {table}")
    ensure_wiki(config)
    project = str(payload.get("Project") or current_project_name(config)).strip() or current_project_name(config)
    layout = wiki_layout(config, project)
    spec = WIKI_WRITEBACKS[table]
    target_page = layout[spec["layout_key"]]
    write_time = wiki_writeback_timestamp()
    base_title = wiki_writeback_base_title(table, payload)
    title = spec["area_fallback"]
    entry_title = incremental_wiki_title(base_title, base_record_id=base_record_id, write_time=write_time)
    wiki_path = f"Dev Knowledge Hub / 10 Projects / {project} / {title}"
    page_body = wiki_log_page_body(title, project=project, table=table)
    entry_body = wiki_writeback_body(table, payload, entry_title=entry_title, base_title=base_title, base_record_id=base_record_id, write_time=write_time)
    output = target_page
    created = bool(output.get("created"))
    doc_token = document_token(output)
    if created:
        update_doc_content(doc_token, title, page_body)
    append_doc_content(doc_token, entry_body)
    ensure_doc_title(doc_token, title)
    url = wiki_node_url(config, output, title)
    artifact_payload = {
        "Title": title,
        "Project": project,
        "Area": str(payload.get("Area") or spec["area_fallback"]),
        "Artifact Type": spec["artifact_type"],
        "Source URL": url,
        "Summary": f"Incremental Wiki page for {table}: {payload.get('Summary') or payload.get('AI Summary') or payload.get('Title') or title}",
        "AI Summary": f"Append-only Wiki artifact for {table}; latest entry: {payload.get('Title') or entry_title}",
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
        "path": wiki_path,
        "url": url,
        "doc_token": doc_token,
        "entry_title": entry_title,
        "mode": "append",
        "artifact_record_id": artifact_record_id,
        "artifact_relation_records": relation_records,
        "artifact": artifact_payload,
    }


def report_wiki_page_body(title: str, *, kind: str, project: str) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            "> Dev Hub report page. New report drafts are appended as timestamped sections so the report keeps history in one place.",
            "",
            f"Project: `{project}`",
            f"Report kind: `{kind}`",
            "Write mode: append-only entries; do not overwrite older report sections.",
            "",
        ]
    )


def report_wiki_entry_body(kind: str, project: str, body: str, *, write_time: str) -> tuple[str, str]:
    entry_title = f"{write_time} - {kind.title()} Report"
    report_body = demote_markdown_headings(strip_top_heading(body), levels=1)
    entry = "\n".join(
        [
            f"## {entry_title}",
            "",
            f"Project: `{project}`",
            f"Report kind: `{kind}`",
            "",
            report_body,
            "",
        ]
    ).rstrip() + "\n"
    return entry_title, entry


def write_report_wiki_artifact(config: dict[str, Any], *, kind: str, project: str, body: str) -> dict[str, Any]:
    ensure_wiki(config)
    layout = wiki_layout(config, project)
    write_time = wiki_writeback_timestamp()
    title = "60 Reports"
    wiki_path = f"Dev Knowledge Hub / 10 Projects / {project} / {title}"
    page_body = report_wiki_page_body(title, kind=kind, project=project)
    entry_title, entry_body = report_wiki_entry_body(kind, project, body, write_time=write_time)
    output = layout["project_reports"]
    doc_token = document_token(output)
    created = bool(output.get("created"))
    if created:
        update_doc_content(doc_token, title, page_body)
    append_doc_content(doc_token, entry_body)
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
    return {
        "title": title,
        "path": wiki_path,
        "url": url,
        "doc_token": doc_token,
        "entry_title": entry_title,
        "mode": "append",
        "artifact_record_id": artifact_record_id,
        "artifact": artifact_payload,
    }
