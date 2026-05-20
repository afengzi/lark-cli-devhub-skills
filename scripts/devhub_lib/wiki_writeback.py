from __future__ import annotations

import re
from typing import Any

from .base import cell_text, find_matching_record_id, upsert_record
from .io import find_first_token, now_iso
from .relationships import write_record_relations
from .wiki_common import (
    append_doc_content,
    current_project_name,
    document_token,
    ensure_doc_title,
    ensure_wiki,
    markdown_table_row,
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
    "Pitfalls": {
        "title_prefix": "Pitfall",
        "template": "pitfall.md",
        "layout_key": "project_bugfixes",
        "artifact_type": "Doc",
        "area_fallback": "20 Bugfix Retros",
    },
    "Playbooks": {
        "title_prefix": "Playbook",
        "template": "playbook.md",
        "layout_key": "project_playbooks",
        "artifact_type": "Doc",
        "area_fallback": "30 Playbooks",
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


def payload_value(payload: dict[str, Any], *keys: str, default: str = "未提供") -> str:
    for key in keys:
        value = payload.get(key)
        text = cell_text(value).strip()
        if text:
            return text
    return default


def payload_table(payload: dict[str, Any], rows: list[tuple[str, str | tuple[str, ...]]]) -> str:
    lines = ["| 字段 | 内容 |", "|---|---|"]
    for label, keys in rows:
        if isinstance(keys, str):
            keys = (keys,)
        lines.append(markdown_table_row(label, payload_value(payload, *keys)))
    return "\n".join(lines)


def code_block(value: str, *, language: str = "bash") -> str:
    text = value.strip()
    if not text:
        text = "# 未提供"
    return f"```{language}\n{text}\n```"


def bullet_block(value: str) -> str:
    text = value.strip()
    if not text:
        return "- 未提供"
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "- 未提供"
    if len(lines) == 1 and (";" in lines[0] or "；" in lines[0]):
        lines = [item.strip() for item in re.split(r"[;；]", lines[0]) if item.strip()]
    return "\n".join(line if line.startswith(("-", "*", "1.")) else f"- {line}" for line in lines)


def section(title: str, content: str) -> list[str]:
    return [f"### {title}", "", content.strip() or "未提供", ""]


def long_form_section(payload: dict[str, Any]) -> list[str]:
    body = str(payload.get("Wiki Body") or "").strip()
    if not body:
        return []
    return ["### 补充说明", "", demote_markdown_headings(strip_top_heading(body), levels=1), ""]


def relation_hints_section(payload: dict[str, Any]) -> list[str]:
    return section("相关记录线索", payload_value(payload, "Relation Hints", "Linked Records", "Related Records"))


def render_bugfix_entry(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    parts.extend(section("快速摘要", payload_table(payload, [("Project", "Project"), ("Area", "Area"), ("Status", "Status"), ("Severity", "Severity"), ("Commit / PR", ("Commit SHA", "PR", "Source URL"))])))
    parts.extend(section("症状", payload_value(payload, "Symptom")))
    parts.extend(section("证据", payload_value(payload, "Evidence")))
    parts.extend(section("根因", payload_value(payload, "Root Cause")))
    parts.extend(section("修复方案", payload_value(payload, "Fix Summary")))
    parts.extend(section("改动文件", bullet_block(payload_value(payload, "Changed Files", default=""))))
    parts.extend(section("验证", payload_table(payload, [("Commands", "Verification Commands"), ("Result", "Verification Result")])))
    parts.extend(section("回归风险", payload_value(payload, "Regression Risk")))
    parts.extend(section("下次优先检查", payload_value(payload, "Next Time Check")))
    parts.extend(section("不要再做", payload_value(payload, "Avoid")))
    parts.extend(relation_hints_section(payload))
    parts.extend(long_form_section(payload))
    return "\n".join(parts).rstrip()


def render_pitfall_entry(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    parts.extend(section("快速摘要", payload_table(payload, [("Project", "Project"), ("Area", "Area"), ("Scope", "Scope"), ("Severity", "Severity"), ("Last Seen", "Last Seen At")])))
    parts.extend(section("触发条件", payload_value(payload, "Trigger Condition")))
    parts.extend(section("错误做法", payload_value(payload, "Wrong Approach")))
    parts.extend(section("正确做法", payload_value(payload, "Correct Approach")))
    parts.extend(section("检查命令", code_block(payload_value(payload, "Check Command", default=""))))
    parts.extend(section("下次优先检查", payload_value(payload, "Next Time Check")))
    parts.extend(section("禁止动作", payload_value(payload, "Avoid")))
    parts.extend(relation_hints_section(payload))
    parts.extend(long_form_section(payload))
    return "\n".join(parts).rstrip()


def render_playbook_entry(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    parts.extend(section("适用场景", payload_value(payload, "Scenario")))
    parts.extend(section("排查顺序", payload_value(payload, "Diagnosis Order")))
    parts.extend(section("必看证据", payload_value(payload, "Must Check Evidence")))
    parts.extend(section("命令", code_block(payload_value(payload, "Commands", default=""))))
    parts.extend(section("成功标准", payload_value(payload, "Success Criteria")))
    parts.extend(section("禁止动作", payload_value(payload, "Forbidden Actions")))
    parts.extend(relation_hints_section(payload))
    parts.extend(long_form_section(payload))
    return "\n".join(parts).rstrip()


def render_decision_entry(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    parts.extend(section("决策", payload_value(payload, "Decision")))
    parts.extend(section("背景", payload_value(payload, "Context")))
    parts.extend(section("备选方案", payload_value(payload, "Alternatives")))
    parts.extend(section("取舍", payload_value(payload, "Tradeoffs")))
    parts.extend(section("影响范围", payload_value(payload, "Consequences")))
    parts.extend(section("复审触发器", payload_value(payload, "Review Trigger")))
    parts.extend(relation_hints_section(payload))
    parts.extend(long_form_section(payload))
    return "\n".join(parts).rstrip()


def render_project_fact_entry(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    parts.extend(section("基本信息", payload_table(payload, [("Project", "Project"), ("Area", "Area"), ("Status", "Status"), ("Source", "Source"), ("Last Reviewed", "Last Reviewed At")])))
    parts.extend(section("事实", payload_value(payload, "Fact", "Title")))
    parts.extend(section("当前真实状态", payload_value(payload, "Current Truth")))
    parts.extend(section("已退役路径 / 旧事实", payload_value(payload, "Retired Paths")))
    parts.extend(section("复审触发器", payload_value(payload, "Review Trigger")))
    parts.extend(section("AI 检索关键词", payload_value(payload, "Search Keywords")))
    parts.extend(relation_hints_section(payload))
    parts.extend(long_form_section(payload))
    return "\n".join(parts).rstrip()


def render_ai_run_entry(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    parts.extend(section("基本信息", payload_table(payload, [("Project", "Project"), ("Area", "Area"), ("Agent", "Agent"), ("Task Intent", "Task Intent"), ("Commit / PR", ("Commit SHA", "PR", "Source URL"))])))
    parts.extend(section("本次做了什么", payload_value(payload, "Actions Taken")))
    parts.extend(section("查过的证据", payload_value(payload, "Evidence Checked")))
    parts.extend(section("改过的文件", bullet_block(payload_value(payload, "Files Changed", default=""))))
    parts.extend(section("验证", payload_table(payload, [("Commands", "Verification Commands"), ("Result", "Verification Result")])))
    parts.extend(section("写回状态", payload_value(payload, "Writeback Status")))
    parts.extend(section("后续风险", payload_value(payload, "Follow-up Risk", "Risk", "Regression Risk")))
    parts.extend(relation_hints_section(payload))
    parts.extend(long_form_section(payload))
    return "\n".join(parts).rstrip()


def render_release_entry(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    parts.extend(section("发布信息", payload_table(payload, [("Project", "Project"), ("Branch", "Branch"), ("Commit SHA", "Commit SHA"), ("PR", "PR"), ("Status", "Status")])))
    parts.extend(section("发布摘要", payload_value(payload, "Summary", "AI Summary")))
    parts.extend(section("验证证据", payload_table(payload, [("Commands", "Verification Commands"), ("Result", "Verification Result")])))
    parts.extend(relation_hints_section(payload))
    parts.extend(section("回滚方案", payload_value(payload, "Rollback Notes")))
    parts.extend(section("发布后观察", payload_value(payload, "Post Release Watch", "Watch Notes", "Regression Risk")))
    parts.extend(long_form_section(payload))
    return "\n".join(parts).rstrip()


WIKI_ENTRY_RENDERERS = {
    "Bugfixes": render_bugfix_entry,
    "Pitfalls": render_pitfall_entry,
    "Playbooks": render_playbook_entry,
    "AI Runs": render_ai_run_entry,
    "Releases": render_release_entry,
    "Decisions": render_decision_entry,
    "Project Facts": render_project_fact_entry,
}


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
    visible_payload = {key: value for key, value in payload.items() if key not in {"Relation Hints", "Wiki Body", "Wiki Title"}}
    rows = "\n".join(markdown_table_row(key, value) for key, value in visible_payload.items())
    renderer = WIKI_ENTRY_RENDERERS.get(table)
    rendered_body = renderer(payload) if renderer else ""
    parts = [
        f"## {entry_title}",
        "",
        f"Write time: `{write_time or wiki_writeback_timestamp()}`",
    ]
    if base_title:
        parts.extend(["", f"Write summary: {base_title}"])
    if base_record_id:
        parts.extend(["", f"Base record: `{base_record_id}`"])
    if rendered_body:
        parts.extend(["", rendered_body])
    parts.extend(["", "### 原始结构化字段", "", "| Field | Value |", "|---|---|"])
    if rows:
        parts.append(rows)
    else:
        parts.append("|  |  |")
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
