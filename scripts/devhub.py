#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


HOME = Path(os.environ.get("HOME", str(Path.home()))).expanduser()
DEVHUB_HOME = Path(os.environ.get("DEVHUB_HOME", str(HOME / ".codex" / "devhub"))).expanduser()
CONFIG_PATH = Path(os.environ.get("DEVHUB_CONFIG", str(DEVHUB_HOME / "config.json"))).expanduser()
DEFAULT_REPO = Path(os.environ.get("DEVHUB_REPO", str(Path.cwd()))).expanduser()


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return load_json(CONFIG_PATH)
    return {
        "version": 1,
        "mode": "shadow",
        "identity": "user",
        "timezone": "Asia/Shanghai",
        "wiki": {"space_id": "", "root_node_token": "", "root_url": ""},
        "base": {"token": "", "url": "", "tables": {}},
        "defaults": {
            "project": DEFAULT_REPO.name,
            "repo_path": str(DEFAULT_REPO),
            "receipt_dir": ".devhub/receipts",
            "outbox_dir": ".devhub/outbox",
        },
    }


def save_config(config: dict) -> None:
    write_json(CONFIG_PATH, config)


def redact_resource_summary(config: dict) -> dict:
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


def parse_json_output(stdout: str) -> dict:
    text = stdout.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])
    return {"raw": text}


def run_lark(args: list[str], *, check: bool = True) -> tuple[dict, str]:
    cmd = ["lark-cli", *args]
    result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or f"lark-cli exited {result.returncode}"
        raise RuntimeError(message)
    return parse_json_output(result.stdout), result.stdout


def run_lark_with_input(args: list[str], stdin: str, *, check: bool = True) -> tuple[dict, str]:
    cmd = ["lark-cli", *args]
    result = subprocess.run(cmd, text=True, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or f"lark-cli exited {result.returncode}"
        raise RuntimeError(message)
    return parse_json_output(result.stdout), result.stdout


def find_first(obj, names: set[str]):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in names and value:
                return value
        for value in obj.values():
            found = find_first(value, names)
            if found:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_first(value, names)
            if found:
                return found
    return None


def find_first_token(obj, names: set[str]) -> str:
    value = find_first(obj, names)
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value or "")


def repo_runtime_dir(cwd: Path, key: str) -> Path:
    try:
        config = load_config()
    except Exception:
        config = {}
    fallback = {"receipt_dir": ".devhub/receipts", "outbox_dir": ".devhub/outbox"}
    dirname = config.get("defaults", {}).get(key, fallback.get(key, f".devhub/{key}"))
    return cwd / dirname


def write_outbox(cwd: Path, kind: str, payload: dict, error: str) -> Path:
    outbox = repo_runtime_dir(cwd, "outbox_dir")
    outbox.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    path = outbox / f"{now_iso().replace(':', '-')}-{kind}-{digest}.json"
    write_json(
        path,
        {
            "kind": kind,
            "created_at": now_iso(),
            "error": error,
            "payload": payload,
            "retry_count": 0,
        },
    )
    return path


def write_receipt(cwd: Path, kind: str, record_url: str, summary: str, extra: dict | None = None) -> Path:
    receipts = repo_runtime_dir(cwd, "receipt_dir")
    receipts.mkdir(parents=True, exist_ok=True)
    data = {
        "kind": kind,
        "created_at": now_iso(),
        "record_url": record_url,
        "summary": summary,
    }
    if extra:
        data.update(extra)
    digest = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    path = receipts / f"{now_iso().replace(':', '-')}-{kind}-{digest}.json"
    write_json(path, data)
    return path


def schema_tables(schema: dict) -> list[dict]:
    tables = schema.get("tables", schema)
    if isinstance(tables, dict):
        return [{"name": name, **value} for name, value in tables.items()]
    if isinstance(tables, list):
        return tables
    raise ValueError("base schema must contain a tables object or list")


def ensure_wiki(config: dict) -> None:
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


def ensure_base(config: dict) -> None:
    base = config.setdefault("base", {"token": "", "url": "", "tables": {}})
    if base.get("token"):
        return
    created, _ = run_lark(["base", "+base-create", "--as", "user", "--name", "Dev Hub Base", "--time-zone", "Asia/Shanghai"])
    token = str(find_first(created, {"app_token", "base_token", "token"}) or "")
    if not token:
        raise RuntimeError("could not find base token in lark-cli output")
    base["token"] = token
    base["url"] = str(find_first(created, {"url", "link"}) or f"base:{token}")
    base.setdefault("tables", {})


def create_tables_and_fields(config: dict, schema: dict) -> None:
    base = config["base"]
    token = base["token"]
    table_map = base.setdefault("tables", {})
    for table in schema_tables(schema):
        table_name = table["name"]
        table_info = table_map.setdefault(table_name, {})
        if not table_info.get("id"):
            created, _ = run_lark(["base", "+table-create", "--as", "user", "--base-token", token, "--name", table_name])
            table_info["id"] = str(find_first(created, {"table_id", "id"}) or table_name)
        for field in table.get("fields", []):
            field_name = field.get("name")
            if not field_name:
                continue
            known = table_info.setdefault("fields", {})
            if field_name in known:
                continue
            try:
                created, _ = run_lark(
                    [
                        "base",
                        "+field-create",
                        "--as",
                        "user",
                        "--base-token",
                        token,
                        "--table-id",
                        table_info["id"],
                        "--json",
                        json.dumps(field, ensure_ascii=False),
                    ]
                )
                known[field_name] = str(find_first(created, {"field_id", "id"}) or field_name)
            except Exception as exc:
                known[field_name] = f"unverified:{field_name}"
                table_info.setdefault("field_warnings", {})[field_name] = str(exc)


def upsert_record(config: dict, table: str, payload: dict) -> tuple[dict, str]:
    base = config["base"]
    table_id = base.get("tables", {}).get(table, {}).get("id", table)
    return run_lark(
        [
            "base",
            "+record-upsert",
            "--as",
            "user",
            "--base-token",
            base["token"],
            "--table-id",
            table_id,
            "--json",
            json.dumps(payload, ensure_ascii=False),
        ]
    )


def seed_records(config: dict, seed: dict) -> None:
    for table, records in seed.items():
        if not isinstance(records, list):
            continue
        for record in records:
            upsert_record(config, table, record)


def create_doc(title: str, body: str, *, parent_token: str = "") -> tuple[dict, str]:
    content = f"<title>{title}</title>{body}"
    args = ["docs", "+create", "--api-version", "v2", "--as", "user", "--content", content]
    if parent_token:
        args.extend(["--parent-token", parent_token])
    else:
        args.extend(["--parent-position", "my_library"])
    return run_lark(args)


def create_artifacts(config: dict) -> None:
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
        output, _ = create_doc(title, "<p>Whiteboard summary is indexed in Dev Hub Base.</p><whiteboard type=\"blank\"></whiteboard>", parent_token=parent)
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


def command_preflight(_args: argparse.Namespace) -> int:
    for cmd in [
        ["doctor", "--offline"],
        ["auth", "status", "--verify"],
        ["auth", "scopes"],
    ]:
        _data, stdout = run_lark(cmd)
        print(stdout.strip())
    return 0


def command_provision(args: argparse.Namespace) -> int:
    config = {}
    config_loaded = False
    try:
        config = load_config()
        config_loaded = True
        schema = load_json(Path(args.schema))
        seed = load_json(Path(args.seed))
        ensure_wiki(config)
        ensure_base(config)
        create_tables_and_fields(config, schema)
        save_config(config)
        seed_records(config, seed)
        create_artifacts(config)
        save_config(config)
        print(json.dumps({"ok": True, **redact_resource_summary(config)}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        if config_loaded:
            save_config(config)
        outbox = write_outbox(
            Path.cwd(),
            "provision",
            {
                "operation": "provision",
                "schema_path": str(Path(args.schema)),
                "seed_path": str(Path(args.seed)),
                "resource_summary": redact_resource_summary(config),
            },
            str(exc),
        )
        print(json.dumps({"ok": False, "outbox": str(outbox), "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


def command_search(args: argparse.Namespace) -> int:
    config = load_config()
    if not config.get("base", {}).get("token"):
        print("Dev Hub Base is not configured yet.", file=sys.stderr)
        return 1
    results = {}
    for table in ["Pitfalls", "Bugfixes", "Playbooks", "Decisions", "Areas"]:
        table_id = config["base"].get("tables", {}).get(table, {}).get("id", table)
        query = {
            "keyword": args.query,
            "search_fields": ["Title", "AI Summary", "Search Keywords"],
            "select_fields": ["Title", "Project", "Area", "AI Summary", "Search Keywords"],
            "limit": 10,
        }
        try:
            data, stdout = run_lark(
                [
                    "base",
                    "+record-search",
                    "--as",
                    "user",
                    "--base-token",
                    config["base"]["token"],
                    "--table-id",
                    table_id,
                    "--json",
                    json.dumps(query, ensure_ascii=False),
                    "--format",
                    "json",
                ],
                check=False,
            )
            results[table] = data if data else stdout.strip()
        except Exception as exc:
            results[table] = {"error": str(exc)}
    print(json.dumps({"project": args.project, "query": args.query, "results": results}, ensure_ascii=False, indent=2))
    return 0


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


def command_receipt(args: argparse.Namespace) -> int:
    path = write_receipt(Path.cwd(), args.kind, args.record_url, args.summary)
    print(path)
    return 0


def is_git_commit(cmd: str) -> bool:
    return "git commit" in cmd


def is_git_push(cmd: str) -> bool:
    return "git push" in cmd


def targets_main(cmd: str, cwd: Path) -> bool:
    if " main" in cmd or " master" in cmd or ":main" in cmd or ":master" in cmd:
        return True
    stripped = cmd.split("#", 1)[0]
    tokens = stripped.split()
    if len(tokens) <= 3:
        branch = subprocess.run(["git", "symbolic-ref", "--short", "HEAD"], cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return branch.stdout.strip() in {"main", "master"}
    return False


def has_runtime_evidence(cwd: Path) -> bool:
    receipts = repo_runtime_dir(cwd, "receipt_dir")
    outbox = repo_runtime_dir(cwd, "outbox_dir")
    has_receipt = any(receipts.glob("*.json")) if receipts.exists() else False
    has_outbox = any(outbox.glob("*.json")) if outbox.exists() else False
    return has_receipt or has_outbox


def command_hook_check(args: argparse.Namespace) -> int:
    config = load_config()
    mode = config.get("mode", "shadow")
    cmd = args.command
    cwd = Path(args.cwd)
    if not is_git_commit(cmd) and not is_git_push(cmd):
        return 0
    needs_kb = False
    reason = ""
    if is_git_push(cmd) and targets_main(cmd, cwd):
        needs_kb = True
        reason = "push to main/master should have a Release or Bugfix writeback"
    elif is_git_commit(cmd) and any(word in cmd.lower() for word in ["fix", "bug", "release"]):
        needs_kb = True
        reason = "bugfix/release commit should have a knowledge-base writeback"
    if not needs_kb:
        return 0
    if "# kb-updated" in cmd or "# kb-skip:" in cmd or has_runtime_evidence(cwd):
        return 0
    message = f"Dev Hub knowledge writeback missing: {reason}. Add # kb-updated after writing Feishu, or # kb-skip: reason for a justified skip."
    if mode == "enforced":
        print(f"BLOCKED: {message}", file=sys.stderr)
        return 2
    print(f"Shadow Mode: {message}", file=sys.stderr)
    return 0


def command_sync_outbox(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd)
    outbox = repo_runtime_dir(cwd, "outbox_dir")
    if not outbox.exists():
        print("No outbox directory.")
        return 0
    files = sorted(outbox.glob("*.json"))
    print(json.dumps({"outbox": str(outbox), "count": len(files), "files": [str(path) for path in files]}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Feishu Dev Hub helper")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("preflight").set_defaults(func=command_preflight)
    provision = sub.add_parser("provision")
    provision.add_argument("--schema", required=True)
    provision.add_argument("--seed", required=True)
    provision.set_defaults(func=command_provision)
    search = sub.add_parser("search")
    search.add_argument("--project", required=True)
    search.add_argument("--query", required=True)
    search.set_defaults(func=command_search)
    for name, table in [("record-bugfix", "Bugfixes"), ("record-ai-run", "AI Runs"), ("record-release", "Releases")]:
        item = sub.add_parser(name)
        item.add_argument("--payload", required=True)
        item.set_defaults(func=lambda ns, n=name, t=table: record_command(n, t, Path(ns.payload), Path.cwd()))
    receipt = sub.add_parser("receipt")
    receipt.add_argument("--kind", required=True)
    receipt.add_argument("--record-url", required=True)
    receipt.add_argument("--summary", required=True)
    receipt.set_defaults(func=command_receipt)
    hook = sub.add_parser("hook-check")
    hook.add_argument("--command", required=True)
    hook.add_argument("--cwd", required=True)
    hook.set_defaults(func=command_hook_check)
    sync = sub.add_parser("sync-outbox")
    sync.add_argument("--cwd", required=True)
    sync.set_defaults(func=command_sync_outbox)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as exc:
        print(f"devhub error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
