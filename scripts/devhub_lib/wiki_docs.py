from __future__ import annotations

import html
import re
from typing import Any

from .base import batch_upsert_records
from .wiki_common import (
    clear_wiki_child_cache,
    cleanup_wiki_noise,
    current_project_name,
    document_token,
    ensure_doc,
    ensure_doc_title,
    ensure_wiki,
    fetch_doc_content,
    read_template,
    render_template,
    update_doc_content,
    update_doc_xml_content,
    wiki_layout,
    wiki_node_url,
)
from .wiki_whiteboards import (
    append_whiteboard,
    find_whiteboard_token_in_content,
    should_preserve_existing_whiteboard,
    update_whiteboard,
    whiteboard_update_input,
)
from .wiki_writeback import (
    wiki_writeback_supported,
    write_report_wiki_artifact,
    write_wiki_artifact,
)


TIMESTAMP_HEADING_RE = re.compile(r"<h2>\d{4}-\d{2}-\d{2} ")


def is_title_only_doc(content: str, title: str) -> bool:
    stripped = content.strip()
    if not stripped:
        return True
    return stripped in {f"<title>{title}</title>", f"# {title}"}


def numbered_page_body(
    title: str,
    *,
    project: str,
    purpose: str,
    record_types: list[tuple[str, str]],
) -> str:
    lines = [
        f"# {title}",
        "",
        "> Dev Hub numbered page. Base remains the structured index; this page keeps human-readable context and append-only entries.",
        "",
        f"Project: `{project}`",
        "Write mode: initialize once, then append timestamped sections. Do not create child docs for routine writeback.",
        "",
        "## 页面用途",
        "",
        purpose,
        "",
        "## AI 写入与回看规则",
        "",
        "- 写入前先查 Base 里的相关 Tasks、Bugfixes、Pitfalls、Playbooks、Decisions、AI Runs、Releases 和 Record Relations。",
        "- Base 是结构化事实源；Wiki 负责让人和 AI 快速读懂上下文。",
        "- 每次写入都追加带时间、标题、Base record id 的二级标题，不覆盖旧段落。",
        "- 写入成功必须有 receipt；失败必须留 outbox，不伪造成功。",
        "",
        "## 增量写入入口",
        "",
        "| Record type | Command | Target |",
        "|---|---|---|",
    ]
    for record_type, command in record_types:
        lines.append(f"| {record_type} | `{command}` | `{title}` |")
    return "\n".join(lines).rstrip() + "\n"


def inline_xml(text: str) -> str:
    escaped = html.escape(text, quote=False)
    return re.sub(r"`([^`]+)`", lambda match: f"<code>{match.group(1)}</code>", escaped)


def numbered_page_intro_xml(title: str, *, project: str, purpose: str, record_types: list[tuple[str, str]]) -> str:
    rows = "".join(
        "<tr>"
        f'<td vertical-align="top"><p>{inline_xml(record_type)}</p></td>'
        f'<td vertical-align="top"><p><code>{html.escape(command, quote=False)}</code></p></td>'
        f'<td vertical-align="top"><p><code>{html.escape(title, quote=False)}</code></p></td>'
        "</tr>"
        for record_type, command in record_types
    )
    return (
        f"<title>{html.escape(title, quote=False)}</title>"
        "<blockquote><p>Dev Hub numbered page. Base remains the structured index; this page keeps human-readable context and append-only entries.</p></blockquote>"
        f"<p>Project: <code>{html.escape(project, quote=False)}</code><br/>"
        "Write mode: initialize once, then append timestamped sections. Do not create child docs for routine writeback.</p>"
        "<h2>页面用途</h2>"
        f"<p>{inline_xml(purpose)}</p>"
        "<h2>AI 写入与回看规则</h2>"
        "<ul>"
        "<li>写入前先查 Base 里的相关 Tasks、Bugfixes、Pitfalls、Playbooks、Decisions、AI Runs、Releases 和 Record Relations。</li>"
        "<li>Base 是结构化事实源；Wiki 负责让人和 AI 快速读懂上下文。</li>"
        "<li>每次写入都追加带时间、标题、Base record id 的二级标题，不覆盖旧段落。</li>"
        "<li>写入成功必须有 receipt；失败必须留 outbox，不伪造成功。</li>"
        "</ul>"
        "<h2>增量写入入口</h2>"
        "<table><colgroup><col/><col/><col/></colgroup><thead><tr>"
        '<th vertical-align="top"><p>Record type</p></th>'
        '<th vertical-align="top"><p>Command</p></th>'
        '<th vertical-align="top"><p>Target</p></th>'
        f"</tr></thead><tbody>{rows}</tbody></table>"
    )


def strip_xml_h2_section(content: str, heading: str) -> str:
    marker = f"<h2>{heading}</h2>"
    while True:
        start = content.find(marker)
        if start < 0:
            return content
        next_h2 = content.find("<h2>", start + len(marker))
        end = next_h2 if next_h2 >= 0 else len(content)
        content = content[:start] + content[end:]


def strip_legacy_entry_template_sections(content: str) -> str:
    marker = "<h3>Template</h3>"
    while True:
        start = content.find(marker)
        if start < 0:
            return content
        search_from = start + len(marker)
        next_h2 = content.find("<h2>", search_from)
        candidates = []
        for stop_marker in ("<h3>原始结构化字段</h3>", "<h3>Fields</h3>"):
            stop = content.find(stop_marker, search_from)
            if stop >= 0 and (next_h2 < 0 or stop < next_h2):
                candidates.append(stop)
        if candidates:
            end = min(candidates)
        else:
            end = next_h2 if next_h2 >= 0 else len(content)
        content = content[:start] + content[end:]


def replace_legacy_overview_intro(content: str, *, title: str, intro_xml: str) -> str:
    if title != "00 Overview":
        return content
    if "<h2>项目身份</h2>" not in content or "<h2>不要重复踩坑</h2>" not in content:
        return content
    match = TIMESTAMP_HEADING_RE.search(content)
    tail = content[match.start() :] if match else ""
    return intro_xml + tail


def remove_legacy_template_content(content: str, *, title: str, intro_xml: str) -> str:
    cleaned = strip_xml_h2_section(content, "参考模板")
    cleaned = strip_legacy_entry_template_sections(cleaned)
    cleaned = replace_legacy_overview_intro(cleaned, title=title, intro_xml=intro_xml)
    return cleaned


def ensure_numbered_page_content(page: dict[str, str], title: str, body: str, intro_xml: str) -> None:
    doc_token = document_token(page)
    existing_content = fetch_doc_content(doc_token)
    if page.get("created") or is_title_only_doc(existing_content, title):
        update_doc_content(doc_token, title, body)
    else:
        clean_content = remove_legacy_template_content(
            existing_content,
            title=title,
            intro_xml=intro_xml,
        )
        if clean_content != existing_content and clean_content.lstrip().startswith("<title>"):
            update_doc_xml_content(doc_token, clean_content)
        elif clean_content != existing_content:
            update_doc_content(doc_token, title, clean_content)
        ensure_doc_title(doc_token, title)


def create_artifacts(config: dict[str, Any]) -> None:
    clear_wiki_child_cache()
    project = current_project_name(config)
    layout = wiki_layout(config, project)
    cleanup_wiki_noise(config, layout)
    artifact_payloads: list[dict[str, Any]] = []
    docs = [
        ("Global: Dev Hub 使用说明", "00 Global", layout["global_root"]["node_token"], "global-devhub-guide.md", "Dev Hub Base 是结构化事实源；Docs 承载长文；Whiteboard/Maps 承载视觉关系。"),
        ("Global: AI 写入规则", "00 Global", layout["global_root"]["node_token"], "ai-write-rules.md", "AI 在修复前检索 Pitfalls / Bugfixes / Playbooks，修复后写 Bugfix、AI Run 和 receipt。"),
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

    numbered_pages = [
        (
            "00 Overview",
            layout["project_overview"],
            "项目主页用于聚合项目当前事实、常用入口、架构链接、任务队列和最近发布。",
            [("Project Facts", "record-project-fact --wiki")],
        ),
        (
            "20 Bugfix Retros",
            layout["project_bugfixes"],
            "记录已修复问题、症状证据、根因、修复方案、验证结果，以及需要下次优先检查的 Pitfalls。",
            [("Bugfixes", "record-bugfix --wiki"), ("Pitfalls", "record-pitfall --wiki")],
        ),
        (
            "30 Playbooks",
            layout["project_playbooks"],
            "沉淀可重复使用的排查路径、命令、必看证据、成功标准和禁止动作。",
            [("Playbooks", "record-playbook --wiki")],
        ),
        (
            "40 Decisions",
            layout["project_decisions"],
            "记录架构或产品决策、备选方案、取舍、影响范围和复审触发条件。",
            [("Decisions", "record-decision --wiki")],
        ),
        (
            "60 Reports",
            layout["project_reports"],
            "沉淀 AI Run、Release、日报/周报/月报等过程记录，方便复盘和汇报。",
            [("AI Runs", "record-ai-run --wiki"), ("Releases", "record-release --wiki"), ("Reports", "report-draft --wiki")],
        ),
    ]
    for title, page, summary, record_types in numbered_pages:
        body = render_template(
            numbered_page_body(
                title,
                project=project,
                purpose=summary,
                record_types=record_types,
            ),
            project=project,
        )
        intro_xml = numbered_page_intro_xml(title, project=project, purpose=summary, record_types=record_types)
        ensure_numbered_page_content(page, title, body, intro_xml)
        artifact_payloads.append(
            {
                "Title": title,
                "Project": project,
                "Area": title,
                "Artifact Type": "Doc",
                "Source URL": page.get("url", ""),
                "Summary": summary,
                "AI Summary": f"{project} {title} append-only Wiki page.",
                "Search Keywords": f"Dev Hub {project} {title} append-only wiki",
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
