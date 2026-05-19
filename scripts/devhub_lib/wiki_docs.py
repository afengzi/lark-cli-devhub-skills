from __future__ import annotations

import json
from typing import Any

from .base import upsert_record
from .io import find_first, find_first_token
from .lark import run_lark, run_lark_with_input
from .paths import DEFAULT_REPO


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


def create_doc(title: str, body: str, *, parent_token: str = "") -> tuple[dict[str, Any], str]:
    content = f"<title>{title}</title>{body}"
    args = ["docs", "+create", "--api-version", "v2", "--as", "user", "--content", content]
    if parent_token:
        args.extend(["--parent-token", parent_token])
    else:
        args.extend(["--parent-position", "my_library"])
    return run_lark(args)


def create_artifacts(config: dict[str, Any]) -> None:
    project = config.get("defaults", {}).get("project") or DEFAULT_REPO.name
    docs = {
        "Dev Hub 使用说明": "<p>Dev Hub Base 是结构化事实源；Docs 承载长文；Whiteboard 承载视觉关系。</p>",
        "AI 写入规则": "<p>AI 在修复前检索 Pitfalls / Bugfixes / Playbooks，修复后写 Bugfix、AI Run 和 receipt。</p>",
        "项目记录模板": "<p>记录项目定位、Areas、关键风险、当前重点和 AI 摘要。</p>",
        "Bugfix 复盘模板": "<p>记录症状、证据、根因、修复、验证、风险、下次检查和禁止做法。</p>",
        "Playbook 模板": "<p>记录适用场景、排查顺序、必看证据、命令、成功标准和禁止做法。</p>",
    }
    parent = config.get("wiki", {}).get("root_node_token", "")
    for title, body in docs.items():
        output, _ = create_doc(title, body, parent_token=parent)
        url = str(find_first(output, {"url", "link"}) or find_first(output, {"document_id", "token"}) or title)
        upsert_record(
            config,
            "Artifacts",
            {
                "Title": title,
                "Project": "Global",
                "Area": "Dev Hub",
                "Artifact Type": "Doc",
                "Source URL": url,
                "Summary": body.replace("<p>", "").replace("</p>", ""),
                "AI Summary": f"{title} for Feishu Dev Hub.",
                "Search Keywords": f"Dev Hub {title}",
                "Status": "Active",
            },
        )
    boards = {
        "Dev Hub 总览图": "graph TD\n  Base[Dev Hub Base] --> Tasks[Tasks]\n  Base --> Bugfixes[Bugfixes]\n  Base --> Pitfalls[Pitfalls]\n  Base --> Playbooks[Playbooks]\n  Base --> Artifacts[Docs and Whiteboards]",
        f"{project} 架构图": "graph TD\n  UI[User Interface] --> API[Application API]\n  API --> Domain[Domain Services]\n  Domain --> Data[(Data Stores)]\n  API --> Integrations[External Integrations]\n  Domain --> Tests[Verification Evidence]",
        "Bug 排查路径模板": "graph TD\n  Symptom[Symptom] --> Evidence[Evidence]\n  Evidence --> RootCause[Root Cause]\n  RootCause --> Fix[Fix]\n  Fix --> Verify[Verification]\n  Verify --> Pitfall[Update Pitfall]",
    }
    for title, mermaid in boards.items():
        output, _ = create_doc(title, '<p>Whiteboard summary is indexed in Dev Hub Base.</p><whiteboard type="blank"></whiteboard>', parent_token=parent)
        board_token = find_first_token(output, {"board_tokens", "board_token", "whiteboard_token"})
        if board_token:
            try:
                run_lark_with_input(
                    [
                        "whiteboard",
                        "+update",
                        "--as",
                        "user",
                        "--whiteboard-token",
                        str(board_token),
                        "--input_format",
                        "mermaid",
                        "--source",
                        "-",
                        "--overwrite",
                    ],
                    mermaid,
                )
            except Exception as exc:
                output.setdefault("whiteboard_warning", str(exc))
        url = str(find_first(output, {"url", "link"}) or find_first(output, {"document_id", "token"}) or title)
        upsert_record(
            config,
            "Artifacts",
            {
                "Title": title,
                "Project": project if project in title else "Global",
                "Area": "Dev Hub",
                "Artifact Type": "Whiteboard",
                "Source URL": url,
                "Summary": "Visual relationship map with Base-backed text summary.",
                "AI Summary": f"{title}: visual aid; use Base records as source of truth.",
                "Search Keywords": f"Dev Hub whiteboard {title}",
                "Status": "Active",
            },
        )
