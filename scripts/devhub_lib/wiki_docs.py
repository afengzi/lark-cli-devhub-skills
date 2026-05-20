from __future__ import annotations

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

    overview_title = "00 Overview"
    overview_summary = "项目主页用于聚合项目当前事实、常用入口、架构链接、任务队列和最近发布。"
    overview_body = render_template(read_template("wiki", "project-home.md", f"# {overview_title}\n\n{overview_summary}\n"), project=project)
    overview_doc_token = document_token(layout["project_overview"])
    update_doc_content(overview_doc_token, overview_title, overview_body)
    ensure_doc_title(overview_doc_token, overview_title)
    artifact_payloads.append(
        {
            "Title": overview_title,
            "Project": project,
            "Area": "00 Overview",
            "Artifact Type": "Doc",
            "Source URL": layout["project_overview"].get("url", ""),
            "Summary": overview_summary,
            "AI Summary": f"{project} 00 Overview for Feishu Dev Hub.",
            "Search Keywords": f"Dev Hub {project} 00 Overview project home",
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
